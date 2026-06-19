"""Tests for metadata extraction (ComfyUI / WebUI prompt parsing).

Covers the bug where Anima workflows store the positive prompt in FETextInput
(referenced via CLIPTextEncode.text=["id",idx]) and CLIPTextEncode.text being a
node-reference list crashed the old " ".join() code.
"""

import json
import pytest

from prompt_inspiration.metadata import (
    _parse_comfyui_prompt,
    _parse_webui_params,
    _resolve_text,
    _is_node_ref,
    _collect_text_nodes,
)


def _ksampler(positive_ref, negative_ref, **kwargs):
    node = {
        "class_type": "KSampler",
        "inputs": {
            "seed": kwargs.get("seed", 12345),
            "steps": kwargs.get("steps", 28),
            "cfg": kwargs.get("cfg", 6.0),
            "sampler_name": "euler",
            "scheduler": "beta",
            "denoise": 0.3,
            "positive": positive_ref,
            "negative": negative_ref,
            "latent_image": ["1", 0],
        },
    }
    return node


def test_standard_clip_text_encode_positive_and_negative():
    """Classic workflow: both prompts are direct strings in CLIPTextEncode."""
    data = {
        "10": {"class_type": "CLIPTextEncode", "inputs": {"text": "masterpiece, 1girl, smile", "clip": ["5", 0]}},
        "11": {"class_type": "CLIPTextEncode", "inputs": {"text": "lowres, bad quality", "clip": ["5", 0]}},
        "5": {"class_type": "CLIPLoader", "inputs": {"clip_name": "clip.safetensors"}},
        "20": _ksampler(["10", 0], ["11", 0]),
        "1": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    }
    meta = _parse_comfyui_prompt(json.dumps(data))
    assert meta.source == "comfyui"
    assert "masterpiece" in meta.best_positive()
    assert "lowres" in meta.best_negative()
    assert meta.steps == 28
    assert meta.seed == 12345


def test_fe_text_input_referenced_by_clip_text_encode():
    """Anima-style: positive text lives in FETextInput, referenced via CLIPTextEncode.text=["id",idx]."""
    data = {
        "10": {"class_type": "FETextInput", "inputs": {"input": "<lora:jijia:0.7>, 1girl, solo, smile"}},
        "37": {"class_type": "CLIPTextEncode", "inputs": {"text": "lowres, bad hands", "clip": ["39", 1]}},
        "38": {"class_type": "CLIPTextEncode", "inputs": {"text": ["39", 2], "clip": ["39", 1]}},
        "39": {"class_type": "FEEncLoraAutoLoader", "inputs": {
            "model_type": "noob", "prompt": ["10", 0], "model": ["25", 0], "clip": ["26", 0]}},
        "25": {"class_type": "UNETLoader", "inputs": {"unet_name": "anima_baseV10.safetensors", "weight_dtype": "fp8"}},
        "73": _ksampler(["38", 0], ["37", 0]),
    }
    meta = _parse_comfyui_prompt(json.dumps(data))
    pos = meta.best_positive()
    neg = meta.best_negative()
    assert "1girl" in pos and "smile" in pos
    assert "lowres" in neg
    assert "jijia" in pos
    # LoRA parsed from positive, not duplicated
    assert meta.loras == ["jijia:0.7"]
    # Model detected from UNETLoader
    assert meta.model == "anima_baseV10.safetensors"


def test_clip_text_encode_text_as_node_ref_does_not_crash():
    """Regression: CLIPTextEncode.text being a node-ref list must not crash join()."""
    data = {
        "38": {"class_type": "CLIPTextEncode", "inputs": {"text": ["39", 2]}},
        "37": {"class_type": "CLIPTextEncode", "inputs": {"text": "negative text"}},
        "39": {"class_type": "FETextInput", "inputs": {"input": "positive text here"}},
        "73": _ksampler(["38", 0], ["37", 0]),
    }
    # Must not raise
    meta = _parse_comfyui_prompt(json.dumps(data))
    assert "positive text here" in meta.best_positive()
    assert "negative text" in meta.best_negative()


def test_non_string_text_field_is_ignored():
    """A CLIPTextEncode whose text is an int / unrelated list must be skipped, not crash."""
    data = {
        "50": {"class_type": "CLIPTextEncode", "inputs": {"text": 12345}},
        "51": {"class_type": "CLIPTextEncode", "inputs": {"text": ["a", "b", "c"]}},  # not a node ref
        "52": {"class_type": "CLIPTextEncode", "inputs": {"text": "real positive"}},
        "73": _ksampler(["52", 0], ["51", 0]),
    }
    meta = _parse_comfyui_prompt(json.dumps(data))
    assert "real positive" in meta.best_positive()


def test_is_node_ref():
    assert _is_node_ref(["10", 0]) is True
    assert _is_node_ref(["10", 2]) is True
    assert _is_node_ref([10, 0]) is False       # id must be str
    assert _is_node_ref(["10", 0, 1]) is False  # len != 2
    assert _is_node_ref("hello") is False
    assert _is_node_ref(["ab", 0]) is False     # id must be digits


def test_resolve_text_follows_reference_chain():
    data = {
        "10": {"class_type": "FETextInput", "inputs": {"input": "deep text"}},
        "39": {"class_type": "FEEncLoraAutoLoader", "inputs": {"prompt": ["10", 0]}},
    }
    # ["39", 0] -> 39.prompt -> ["10",0] -> 10.input
    assert _resolve_text(["39", 0], data, set()) == "deep text"
    # string passthrough
    assert _resolve_text("plain string", data, set()) == "plain string"
    # non-ref, non-str
    assert _resolve_text(123, data, set()) == ""
    assert _resolve_text(None, data, set()) == ""


def test_resolve_text_cycle_protection():
    """Circular references must not infinite-loop."""
    data = {
        "1": {"class_type": "FETextInput", "inputs": {"input": ["2", 0]}},
        "2": {"class_type": "FETextInput", "inputs": {"input": ["1", 0]}},
    }
    # Should return empty, not hang
    assert _resolve_text(["1", 0], data, set()) == ""


def test_collect_text_nodes_dedupes_native_and_ref():
    """FETextInput (native) and CLIPTextEncode referencing it should not double-count."""
    data = {
        "10": {"class_type": "FETextInput", "inputs": {"input": "shared prompt"}},
        "38": {"class_type": "CLIPTextEncode", "inputs": {"text": ["39", 2]}},
        "39": {"class_type": "FEEncLoraAutoLoader", "inputs": {"prompt": ["10", 0]}},
    }
    nodes = _collect_text_nodes(data)
    texts = [txt for _, _, txt, _ in nodes]
    # Node 10 native text present; Node 38 resolves to same text (ref)
    assert "shared prompt" in texts
    # In parse, the ref duplicate is dropped so positive_prompts has 1 entry
    meta = _parse_comfyui_prompt(json.dumps({**data, "73": _ksampler(["38", 0], _neg_node())}))
    assert meta.positive_prompts.count("shared prompt") == 1


def _neg_node():
    return ["37", 0]


def test_webui_params_parsing():
    params = (
        "masterpiece, 1girl, solo\n"
        "Negative prompt: lowres, bad quality\n"
        "Steps: 28, CFG scale: 6.0, Seed: 12345, Sampler: Euler a, "
        "Model: noobaiXL, Size: 1024x1024"
    )
    meta = _parse_webui_params(params)
    assert meta.source == "webui"
    assert "masterpiece" in meta.positive_prompt
    assert "lowres" in meta.negative_prompt
    assert meta.steps == 28
    assert meta.cfg == 6.0
    assert meta.seed == 12345
    assert meta.model == "noobaiXL"
    assert meta.size == "1024x1024"


def test_empty_and_invalid_json():
    meta = _parse_comfyui_prompt("not json")
    assert meta.source == "comfyui"
    assert meta.best_positive() == ""
    meta2 = _parse_comfyui_prompt("{}")
    assert meta2.best_positive() == ""
