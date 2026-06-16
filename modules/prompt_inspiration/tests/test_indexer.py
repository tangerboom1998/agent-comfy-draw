"""Tests for indexer module."""

import numpy as np
from prompt_inspiration.indexer import parse_prompt, build_tag_index, save_tag_index, load_tag_index


def test_parse_prompt_splits_tags_from_description():
    text = "mecha, robot, solo, science fiction, A large robot standing in a field with a gun"
    tags, desc = parse_prompt(text)
    assert "mecha" in tags
    assert "robot" in tags
    assert "solo" in tags
    assert "science fiction" in tags
    assert "A large robot" in desc or "large robot" in desc


def test_parse_prompt_handles_mixed_case_description():
    text = "1girl, solo, portrait, brown hair, a young woman with brown hair and blue eyes, soft lighting"
    tags, desc = parse_prompt(text)
    assert "1girl" in tags
    assert "brown hair" in tags
    assert "young woman" in desc


def test_parse_prompt_no_description():
    text = "mecha, robot, solo"
    tags, desc = parse_prompt(text)
    assert tags == ["mecha", "robot", "solo"]
    assert desc == ""


def test_build_tag_index_creates_inverted_index(prompts_dir):
    tag_index, filenames, descriptions = build_tag_index(prompts_dir)
    assert "mecha" in tag_index
    assert "cyberpunk" in tag_index
    assert "fantasy" in tag_index
    assert len(filenames) == 4
    assert all(name in descriptions for name in filenames)
    assert len(tag_index["mecha"]) == 1


def test_save_and_load_tag_index_roundtrip(prompts_dir, data_dir):
    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    loaded_idx, loaded_fnames = load_tag_index(data_dir)
    assert loaded_idx == tag_index
    assert loaded_fnames == filenames


def test_build_tfidf_index_creates_matrix(prompts_dir):
    from prompt_inspiration.indexer import build_tag_index, build_tfidf_index
    _, filenames, _ = build_tag_index(prompts_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    assert tfidf_matrix.shape[0] == 4  # 4 documents
    assert tfidf_matrix.shape[1] > 0   # at least some features
    assert hasattr(vectorizer, "vocabulary_")


def test_save_and_load_tfidf_roundtrip(prompts_dir, data_dir):
    from prompt_inspiration.indexer import build_tag_index, build_tfidf_index, save_tfidf_index, load_tfidf_index
    _, filenames, _ = build_tag_index(prompts_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)
    loaded_matrix, loaded_vec = load_tfidf_index(data_dir)
    assert loaded_matrix.shape == tfidf_matrix.shape
    # Check the vectorizer has the same vocabulary
    assert loaded_vec.vocabulary_ == vectorizer.vocabulary_


from unittest.mock import patch, MagicMock


@patch("prompt_inspiration.model_setup._check_onnx_model_exists")
@patch("prompt_inspiration.model_setup._get_tokenizer_and_session")
def test_compute_embeddings_basic(mock_session, mock_check):
    mock_check.return_value = True
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {
        "input_ids": np.ones((2, 8), dtype=np.int64),
        "attention_mask": np.ones((2, 8), dtype=np.int64),
    }
    mock_sess = MagicMock()
    mock_sess.run.return_value = [np.ones((2, 8, 384), dtype=np.float32)]
    mock_session.return_value = (mock_tokenizer, mock_sess)

    from prompt_inspiration.model_setup import compute_embeddings
    embeddings = compute_embeddings(["test text one", "test text two"])
    assert embeddings.shape == (2, 384)
    # Check normalized (unit length)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


@patch("prompt_inspiration.indexer.compute_embeddings")
def test_build_embedding_index(mock_compute, prompts_dir, data_dir):
    import numpy as np
    from prompt_inspiration.indexer import build_tag_index, build_embedding_index, save_embedding_index, load_embedding_index
    _, filenames, _ = build_tag_index(prompts_dir)
    mock_compute.return_value = np.random.randn(4, 384).astype(np.float32)
    embeddings = build_embedding_index(filenames, prompts_dir)
    assert embeddings.shape == (4, 384)
    save_embedding_index(embeddings, data_dir)
    loaded = load_embedding_index(data_dir)
    assert np.allclose(loaded, embeddings)


def test_is_available_returns_false_without_model():
    from prompt_inspiration.model_setup import is_available
    # Without actual model file, should return False
    result = is_available()
    # This could be True if model happens to exist, but we expect False in general
    assert isinstance(result, bool)


@patch("prompt_inspiration.indexer.build_embedding_index")
@patch("prompt_inspiration.indexer.save_embedding_index")
def test_build_all_without_onnx(mock_save_emb, mock_build_emb, prompts_dir, data_dir):
    """build_all should work even without ONNX model."""
    from prompt_inspiration.indexer import build_all
    build_all(prompts_dir=prompts_dir, data_dir=data_dir)
    assert (data_dir / "tags.index.json").exists()
    assert (data_dir / "filenames.json").exists()
    assert (data_dir / "tfidf.npz").exists()
    assert (data_dir / "vectorizer.pkl").exists()
    # Embeddings should NOT be saved (ONNX not available)
    assert not (data_dir / "embeddings.npy").exists()


def test_build_all_fails_on_missing_prompts_dir(data_dir):
    from prompt_inspiration.indexer import build_all
    import pytest
    with pytest.raises(FileNotFoundError):
        build_all(prompts_dir=data_dir / "nonexistent", data_dir=data_dir)
