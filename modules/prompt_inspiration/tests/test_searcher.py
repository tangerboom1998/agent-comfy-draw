"""Tests for searcher module."""

import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_search_tag_mode(prompts_dir, data_dir):
    """Test tag-only search mode."""
    from prompt_inspiration.indexer import build_tag_index, save_tag_index, build_tfidf_index, save_tfidf_index
    from prompt_inspiration.searcher import search_inspiration

    # Build and save indices
    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)

    results = search_inspiration(
        query="",
        tags=["mecha"],
        mode="tag",
        top_k=5,
        prompts_dir=prompts_dir,
        data_dir=data_dir,
    )
    assert len(results) >= 1
    # The mecha doc should appear
    assert any("test_mecha" in r["filename"] for r in results)


def test_search_hybrid_fallback_to_tfidf(prompts_dir, data_dir):
    """Hybrid mode should fallback to TF-IDF when no ONNX model."""
    from prompt_inspiration.indexer import build_tag_index, save_tag_index, build_tfidf_index, save_tfidf_index
    from prompt_inspiration.searcher import search_inspiration

    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)

    results = search_inspiration(
        query="dragon fantasy epic",
        mode="hybrid",
        top_k=5,
        prompts_dir=prompts_dir,
        data_dir=data_dir,
    )
    assert len(results) >= 1
    # Fantasy should rank highly for "dragon fantasy epic"
    fantasy_results = [r for r in results if "test_fantasy" in r["filename"]]
    assert len(fantasy_results) >= 1


def test_search_empty_result_with_unmatched_tag_filter(prompts_dir, data_dir):
    """Search with a tag that matches nothing should return empty result."""
    from prompt_inspiration.indexer import build_tag_index, save_tag_index, build_tfidf_index, save_tfidf_index
    from prompt_inspiration.searcher import search_inspiration

    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)

    results = search_inspiration(
        query="test",
        tags=["nonexistent_tag_xyz"],
        mode="hybrid",
        top_k=5,
        prompts_dir=prompts_dir,
        data_dir=data_dir,
    )
    assert len(results) >= 1
    assert results[0]["filename"] is None
    assert "note" in results[0]


def test_search_semantic_with_mocked_embeddings(prompts_dir, data_dir):
    """Test semantic search mode with mock ONNX embeddings."""
    from prompt_inspiration.indexer import build_tag_index, save_tag_index, build_tfidf_index, save_tfidf_index
    from prompt_inspiration.searcher import search_inspiration

    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)

    # Create mock normalized embeddings
    rng = np.random.default_rng(42)
    embeddings = rng.normal(size=(4, 384)).astype(np.float32)
    embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
    np.save(data_dir / "embeddings.npy", embeddings)

    with patch("prompt_inspiration.searcher.model_available") as mock_avail:
        mock_avail.return_value = True
        with patch("prompt_inspiration.searcher.compute_embeddings") as mock_emb:
            # Make query embedding close to doc 0 (mecha) and doc 2 (cyberpunk)
            q_emb = (embeddings[0] + embeddings[2]) / 2
            q_emb = (q_emb / np.linalg.norm(q_emb)).reshape(1, -1)
            mock_emb.return_value = q_emb

            results = search_inspiration(
                query="robot technology",
                mode="semantic",
                top_k=3,
                prompts_dir=prompts_dir,
                data_dir=data_dir,
            )
            assert len(results) > 0
            for r in results:
                assert "filename" in r
                assert "score" in r
                assert "semantic_score" in r
                assert "description" in r
                assert "matched_tags" in r


def test_search_result_format(prompts_dir, data_dir):
    """Test that search results have the correct keys and types."""
    from prompt_inspiration.indexer import build_tag_index, save_tag_index, build_tfidf_index, save_tfidf_index
    from prompt_inspiration.searcher import search_inspiration

    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)

    results = search_inspiration(
        query="test",
        mode="hybrid",
        top_k=2,
        prompts_dir=prompts_dir,
        data_dir=data_dir,
    )

    for r in results:
        assert isinstance(r["filename"], str)
        assert isinstance(r["score"], float)
        assert isinstance(r["semantic_score"], float)
        assert isinstance(r["tag_score"], float)
        assert isinstance(r["tags"], list)
        assert isinstance(r["description"], str)
        assert isinstance(r["matched_tags"], list)
