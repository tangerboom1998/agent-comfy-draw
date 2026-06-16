"""Command-line interface for prompt inspiration tool."""

import argparse
import json
import logging
import sys
from pathlib import Path

from . import config
from .indexer import build_all
from .searcher import search_inspiration
from .model_setup import download_model, is_available as model_available
from .tagger.wd import WDTagger
from .tagger.vlm import VLMTagger

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_setup(args) -> None:
    """Download ONNX model and build all indices."""
    logger.info("Step 1: Building tag and TF-IDF indices...")
    build_all()

    logger.info("Step 2: Downloading ONNX model...")
    try:
        download_model()
    except ImportError:
        logger.error(
            "Optional dependencies required. Install: pip install 'prompt-inspiration[setup]'"
        )
        sys.exit(1)

    logger.info("Step 3: Building embedding index...")
    build_all()
    logger.info("Setup complete!")


def cmd_build(args) -> None:
    """Build all indices from prompts (no model download)."""
    logger.info("Building tag index...")
    from .indexer import build_tag_index, save_tag_index
    from .config import PROMPTS_DIR, DATA_DIR
    tag_index, filenames, _ = build_tag_index(PROMPTS_DIR)
    save_tag_index(tag_index, filenames, DATA_DIR)
    logger.info("Tag index: %d tags, %d docs", len(tag_index), len(filenames))

    logger.info("Building TF-IDF index...")
    from .indexer import build_tfidf_index, save_tfidf_index
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, PROMPTS_DIR)
    save_tfidf_index(tfidf_matrix, vectorizer, DATA_DIR)
    logger.info("TF-IDF matrix: %s", tfidf_matrix.shape)

    if model_available():
        logger.info("Building embedding index (ONNX)...")
        from .indexer import build_embedding_index, save_embedding_index
        embeddings = build_embedding_index(filenames, PROMPTS_DIR)
        save_embedding_index(embeddings, DATA_DIR)
        logger.info("Embedding index: %s", embeddings.shape)
    else:
        logger.info("ONNX model not available. Embedding index skipped.")

    logger.info("Build complete!")


def cmd_search(args) -> None:
    """Search prompt database."""
    results = search_inspiration(
        query=args.query,
        tags=args.tags,
        top_k=args.top_k,
        mode=args.mode,
    )
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results found.")
            return
        for i, r in enumerate(results, 1):
            if r.get("filename") is None:
                print(f"[{i}] Note: {r.get('note', 'No results')}")
                continue
            print(f"[{i}] {r['filename']}  (score: {r['score']})")
            if r.get("matched_tags"):
                print(f"    Matched tags: {', '.join(r['matched_tags'])}")
            if r.get("tags"):
                tags_str = ", ".join(r['tags'][:10])
                print(f"    Tags: {tags_str}")
            if r.get("description"):
                desc = r['description'][:150]
                print(f"    Desc: {desc}...")
            print()


def cmd_info(args) -> None:
    """Show tool status and statistics."""
    tag_ok = config.TAGS_INDEX_PATH.exists()
    tfidf_ok = config.TFIDF_MATRIX_PATH.exists()
    emb_ok = config.EMBEDDINGS_PATH.exists()
    model_ok = model_available()

    prompts_count = len(list(config.PROMPTS_DIR.glob("*.txt")))

    print("Prompt Inspiration Tool - Status")
    print("=" * 40)
    print(f"Prompts dir: {config.PROMPTS_DIR}")
    print(f"  Files: {prompts_count}")
    print(f"Data dir: {config.DATA_DIR}")
    print(f"  Tag index:     {'OK' if tag_ok else 'MISSING'}")
    print(f"  TF-IDF index:  {'OK' if tfidf_ok else 'MISSING'}")
    print(f"  Embedding idx: {'OK' if emb_ok else 'MISSING'}")
    print(f"  ONNX model:    {'OK' if model_ok else 'MISSING'}")
    print()
    print("Commands:")
    print("  prompt-inspiration build    - Build indices from prompts")
    print("  prompt-inspiration setup    - Full setup (model + all indices)")
    print("  prompt-inspiration search   - Search prompts")
    print("  prompt-inspiration info     - Show this status")


def cmd_tag(args) -> None:
    """Tag images with WD model and/or VLM."""
    image_paths = [Path(p).resolve() for p in args.images]
    for p in image_paths:
        if not p.exists():
            logger.error("File not found: %s", p)
            sys.exit(1)

    mode = args.mode  # "tags", "caption", "both"
    save = args.save
    use_wd = mode in ("tags", "both")
    use_vlm = mode in ("caption", "both")

    # WD tagger (tags mode)
    wd_result = None
    if use_wd:
        logger.info("Loading WD tagger...")
        try:
            wd = WDTagger()
        except FileNotFoundError as e:
            logger.error("WD model not found: %s", e)
            logger.info("Run 'prompt-inspiration tag --download-wd' to download the model")
            sys.exit(1)

        for img_path in image_paths:
            logger.info("Tagging: %s", img_path.name)
            tags = wd.tag_image(
                str(img_path),
                general_threshold=args.threshold,
                character_threshold=args.char_threshold,
                additional_tags=args.additional_tags,
                exclude_tags=args.exclude_tags,
            )
            print(f"\n[{img_path.name}] WD Tags:")
            print(f"  {tags}")
            wd_result = tags

    # VLM tagger (caption mode)
    vlm_result = None
    if use_vlm:
        logger.info("Connecting to VLM API...")
        vlm = VLMTagger(
            api_base=args.api_base,
            api_key=args.api_key,
            model=args.vlm_model,
            max_tokens=args.max_tokens,
        )

        vlm_mode = "tags" if mode == "tags" else "caption"
        for img_path in image_paths:
            logger.info("Generating %s via VLM: %s", vlm_mode, img_path.name)
            result = vlm.tag_image(
                str(img_path),
                prompt=args.vlm_prompt,
                mode=vlm_mode,
            )
            label = "VLM Tags" if vlm_mode == "tags" else "VLM Caption"
            print(f"\n[{img_path.name}] {label}:")
            print(f"  {result}")
            vlm_result = result

    # Both mode: merge results
    if mode == "both" and wd_result and vlm_result:
        combined = f"{wd_result}, {vlm_result}"
        print(f"\n[{image_paths[0].name}] Combined:")
        print(f"  {combined}")
        final = combined
    elif wd_result:
        final = wd_result
    else:
        final = vlm_result or ""

    # Save to prompt library
    if save and final:
        save_path = config.PROMPTS_DIR / f"{image_paths[0].stem}.txt"
        save_path.write_text(final)
        logger.info("Saved to prompt library: %s", save_path)

        # Rebuild index if saving
        if args.rebuild:
            logger.info("Rebuilding index...")
            cmd_build(args)

    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Prompt Inspiration Tool - search image tagging prompts for inspiration"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # build
    sub.add_parser("build", help="Build indices from prompts (no model download)")

    # setup
    p_setup = sub.add_parser("setup", help="Download ONNX model and build all indices")
    p_setup.add_argument("--no-model", action="store_true",
                        help="Skip ONNX model download (build tag + TF-IDF only)")

    # search
    p_search = sub.add_parser("search", help="Search prompts")
    p_search.add_argument("query", type=str, help="Search query (natural language)")
    p_search.add_argument("--tags", "-t", type=str, nargs="*", default=None,
                         help="Filter by tags (AND logic)")
    p_search.add_argument("--top-k", "-k", type=int, default=10,
                         help="Number of results (default: 10)")
    p_search.add_argument("--mode", "-m", choices=["semantic", "tag", "hybrid"],
                         default="hybrid", help="Search mode (default: hybrid)")
    p_search.add_argument("--json", "-j", action="store_true",
                         help="Output as JSON")

    # info
    sub.add_parser("info", help="Show index status")

    # tag
    p_tag = sub.add_parser("tag", help="Tag images and generate prompts")
    p_tag.add_argument("images", type=str, nargs="+",
                       help="Image file paths")
    p_tag.add_argument("--mode", "-m", choices=["tags", "caption", "both"],
                       default="both", help="Output mode (default: both)")
    p_tag.add_argument("--save", "-s", action="store_true",
                       help="Save generated prompt to library")
    p_tag.add_argument("--rebuild", "-r", action="store_true",
                       help="Rebuild search index after saving")

    # WD options
    p_tag.add_argument("--threshold", type=float, default=0.35,
                       help="WD general tag threshold (default: 0.35)")
    p_tag.add_argument("--char-threshold", type=float, default=0.85,
                       help="WD character tag threshold (default: 0.85)")
    p_tag.add_argument("--additional-tags", type=str, nargs="*", default=None,
                       help="Additional tags to always include")
    p_tag.add_argument("--exclude-tags", type=str, nargs="*", default=None,
                       help="Tags to exclude from results")

    # VLM options (defaults from config/env vars)
    p_tag.add_argument("--api-base", type=str,
                       default=config.VLM_API_BASE,
                       help="VLM API base URL (default: from VLM_API_BASE env)")
    p_tag.add_argument("--api-key", type=str,
                       default=config.VLM_API_KEY,
                       help="VLM API key (default: from VLM_API_KEY env)")
    p_tag.add_argument("--vlm-model", type=str, default=config.VLM_MODEL,
                       help="VLM model name (default: from VLM_MODEL env)")
    p_tag.add_argument("--vlm-prompt", type=str, default=None,
                       help="Custom VLM prompt")
    p_tag.add_argument("--max-tokens", type=int, default=8192,
                       help="VLM max tokens (default: 8192)")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build(args)
    elif args.command == "tag":
        cmd_tag(args)
    elif args.command == "setup":
        if args.no_model:
            logger.info("Building indices without ONNX model...")
            build_all()
        else:
            cmd_setup(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "info":
        cmd_info(args)
    else:
        parser.print_help()


# Alias for __init__.py import
cli_main = main


if __name__ == "__main__":
    main()
