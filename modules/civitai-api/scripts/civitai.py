#!/usr/bin/env python3
"""
Civitai API skill — search, inspect, and DOWNLOAD models directly.

Usage:
  python civitai.py models --query "flux lora" --nsfw true
  python civitai.py model 12345
  python civitai.py version 67890
  python civitai.py download 67890 --comfyui-dir "$COMFYUI_ROOT"
  python civitai.py download-model 12345 --comfyui-dir "$COMFYUI_ROOT"
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://civitai.com/api/v1"
DOWNLOAD_BASE_URL = "https://civitai.com/api/download/models"

# ── Host aliases ──
HOST_ALIASES = {
    "civitai.com": ("https://civitai.com/api/v1", "https://civitai.com/api/download/models"),
    "civitai.red": ("https://civitai.red/api/v1", "https://civitai.red/api/download/models"),
}

# ── Model type → ComfyUI subdirectory mapping ──
TYPE_TO_COMFY_DIR = {
    "Checkpoint": "checkpoints",
    "LORA": "loras",
    "LoCon": "loras",
    "TextualInversion": "embeddings",
    "VAE": "vae",
    "Upscaler": "upscale_models",
    "Controlnet": "controlnet",
}

# ── Helpers ──

def load_env_file(start: Path) -> None:
    # Check script dir, parent dir, then walk up to profile root
    candidates = [start / ".env", start.parent / ".env"]
    # Also check up the tree until we find .env
    p = start
    for _ in range(6):
        p = p.parent
        candidates.append(p / ".env")
    for env_path in candidates:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
        return


def build_url(path: str, params: dict | None = None) -> str:
    url = f"{BASE_URL}{path}"
    if params:
        params = {k: v for k, v in params.items() if v not in (None, "", False)}
        if params:
            url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    return url


def _get_proxy() -> urllib.request.ProxyHandler | None:
    """Build proxy handler from environment variables."""
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        val = os.environ.get(var)
        if val:
            return urllib.request.ProxyHandler({"https": val, "http": val})
    return None


_proxy_handler = None  # lazy init

def _get_opener():
    global _proxy_handler
    if _proxy_handler is None:
        handler = _get_proxy()
        _proxy_handler = urllib.request.build_opener(handler) if handler else urllib.request.build_opener()
    return _proxy_handler


def request_json(url: str, token: str | None = None) -> dict:
    headers = {"User-Agent": "hermes-civitai-skill/2.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    opener = _get_opener()
    with opener.open(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def request_post_json(url: str, body: dict, token: str | None = None) -> dict:
    """POST JSON and return parsed response."""
    headers = {
        "User-Agent": "hermes-civitai-skill/2.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    opener = _get_opener()
    with opener.open(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _pick_file(files: list, prefer: str = "safetensors") -> dict | None:
    """Pick the best file from a version's files list. Prefer safetensors, then largest."""
    if not files:
        return None
    for f in files:
        if prefer in str(f.get("name", "")).lower():
            return f
    # fallback: largest file
    return max(files, key=lambda f: f.get("sizeKB", 0))


def _friendly_size(bytes_val: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def _progress_bar(done: int, total: int, width: int = 30) -> str:
    pct = done / total if total else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct*100:.0f}%"


# ── API query commands ──

def cmd_models(args, token):
    params = {
        "query": args.query, "limit": args.limit, "page": args.page,
        "cursor": args.cursor, "types": args.types, "sort": args.sort,
        "period": args.period, "username": args.username, "tag": args.tag,
        "nsfw": str(args.nsfw).lower() if args.nsfw is not None else None,
    }
    print_json(request_json(build_url("/models", params), token))


def cmd_model(args, token):
    print_json(request_json(build_url(f"/models/{args.model_id}"), token))


def cmd_version(args, token):
    print_json(request_json(build_url(f"/model-versions/{args.version_id}"), token))


def cmd_hash(args, token):
    """GET /model-versions/by-hash/{hash} — try full hash, fall back to AutoV2 prefix."""
    hash_val = args.hash_value.strip()
    # Try full hash (SHA256) first
    try:
        data = request_json(build_url(f"/model-versions/by-hash/{hash_val}"), token)
        print_json(data)
        return
    except urllib.error.HTTPError as e:
        if e.code == 404 and len(hash_val) >= 10:
            pass  # fall back to AutoV2
        else:
            raise
    # Fallback: try first 10 chars as AutoV2
    auto_v2 = hash_val[:10]
    print_json(request_json(build_url(f"/model-versions/by-hash/{auto_v2}"), token))


def cmd_creators(args, token):
    params = {"query": args.query, "limit": args.limit, "page": args.page, "cursor": args.cursor}
    print_json(request_json(build_url("/creators", params), token))


def cmd_tags(args, token):
    params = {"query": args.query, "limit": args.limit, "page": args.page, "cursor": args.cursor}
    print_json(request_json(build_url("/tags", params), token))


def cmd_images(args, token):
    params = {
        "postId": args.post_id, "modelId": args.model_id,
        "modelVersionId": args.model_version_id, "username": args.username,
        "limit": args.limit, "page": args.page, "cursor": args.cursor,
        "sort": args.sort, "period": args.period,
        "nsfw": str(args.nsfw).lower() if args.nsfw is not None else None,
    }
    print_json(request_json(build_url("/images", params), token))


def cmd_download_url(args, token):
    """Build download URL only (legacy, kept for scripting)."""
    params = {}
    if args.type:
        params["type"] = args.type
    if args.format:
        params["format"] = args.format
    if args.size:
        params["size"] = args.size
    if args.fp:
        params["fp"] = args.fp
    if token:
        params["token"] = token
    url = f"{DOWNLOAD_BASE_URL}/{args.version_id}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    print(url)


# ── NEW: Model Versions advanced ──

def cmd_by_hash_batch(args, token):
    """POST /model-versions/by-hash — batch lookup model versions by hashes."""
    hashes = [h.strip() for h in args.hashes.split(",") if h.strip()]
    print_json(request_post_json(build_url("/model-versions/by-hash"), {"hashes": hashes}, token))


def cmd_by_hash_ids(args, token):
    """POST /model-versions/by-hash/ids — batch hash → IDs only (lightweight)."""
    hashes = [h.strip() for h in args.hashes.split(",") if h.strip()]
    print_json(request_post_json(build_url("/model-versions/by-hash/ids"), {"hashes": hashes}, token))


def cmd_version_mini(args, token):
    """GET /model-versions/mini/{id} — lightweight version info."""
    print_json(request_json(build_url(f"/model-versions/mini/{args.version_id}"), token))


# ── NEW: Users ──

def cmd_me(args, token):
    """GET /me — current user info (requires auth)."""
    print_json(request_json(build_url("/me"), token))


def cmd_users(args, token):
    """GET /users — search or list users."""
    params = {"query": args.query, "limit": args.limit, "page": args.page, "cursor": args.cursor}
    print_json(request_json(build_url("/users", params), token))


# ── NEW: Permissions ──

def cmd_permissions(args, token):
    """GET /permissions/check — check user permissions."""
    params = {}
    if args.model_id:
        params["modelId"] = args.model_id
    if args.model_version_id:
        params["modelVersionId"] = args.model_version_id
    print_json(request_json(build_url("/permissions/check", params), token))


# ── NEW: Vault (membership required) ──

def cmd_vault_get(args, token):
    """GET /vault/get — get or create the user's vault."""
    print_json(request_json(build_url("/vault/get"), token))


def cmd_vault_all(args, token):
    """GET /vault/all — list all items in the vault."""
    params = {"limit": args.limit, "page": args.page, "cursor": args.cursor}
    print_json(request_json(build_url("/vault/all", params), token))


def cmd_vault_check(args, token):
    """GET /vault/check-vault — check if model versions are in the vault."""
    params = {"modelVersionIds": args.version_ids}
    print_json(request_json(build_url("/vault/check-vault", params), token))


def cmd_vault_toggle(args, token):
    """POST /vault/toggle-version — add or remove a model version from vault."""
    body = {"modelVersionId": args.version_id}
    print_json(request_post_json(build_url("/vault/toggle-version"), body, token))


# ── NEW: Enums ──

def cmd_enums(args, token):
    """GET /enums — list available enum values (model types, sort options, etc.)."""
    print_json(request_json(build_url("/enums"), token))


# ── REAL DOWNLOAD ──

def _download_file(url: str, dest: Path, resume: bool = False) -> bool:
    """Stream-download a file with progress bar and optional resume."""
    headers = {"User-Agent": "hermes-civitai-skill/2.0"}
    existing_size = 0
    if resume and dest.exists():
        existing_size = dest.stat().st_size
        headers["Range"] = f"bytes={existing_size}-"

    req = urllib.request.Request(url, headers=headers)
    try:
        resp = _get_opener().open(req)
    except urllib.error.HTTPError as e:
        if e.code == 416 and resume:
            print(f"  ✓ File already complete: {dest.name}", file=sys.stderr)
            return True
        raise

    total = int(resp.headers.get("Content-Length", 0)) + existing_size
    print(f"  📥 Downloading: {dest.name}  ({_friendly_size(total)})", file=sys.stderr)

    mode = "ab" if existing_size else "wb"
    with open(dest, mode) as f:
        done = existing_size
        chunk_size = 1 << 18  # 256 KiB
        last_tick = time.time()
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            # Progress every 0.3s
            if time.time() - last_tick > 0.3:
                print(f"  {_progress_bar(done, total)}  {_friendly_size(done)}/{_friendly_size(total)}", end="\r", file=sys.stderr)
                last_tick = time.time()

    print(f"  {_progress_bar(done, total)}  ✅ Done", file=sys.stderr)
    return True


def _resolve_output_path(
    model_info: dict,
    version_info: dict,
    file_info: dict,
    output: str | None,
    comfyui_dir: str | None,
    name: str | None,
) -> Path:
    """Determine the output file path based on user options.

    Priority: -o/--output > --comfyui-dir > COMFYUI_ROOT env var > cwd
    """
    if output:
        return Path(output).expanduser()

    # Derive filename
    if name:
        fname = name
    else:
        model_name = model_info.get("name", "model")
        model_type = model_info.get("type", "Checkpoint")
        file_ext = Path(file_info.get("name", "model.safetensors")).suffix or ".safetensors"
        fname = f"{model_name}{file_ext}"

    # Fallback chain: CLI arg → COMFYUI_ROOT env var → cwd
    comfyui_root = comfyui_dir or os.environ.get("COMFYUI_ROOT")
    if comfyui_root:
        model_type = model_info.get("type", "Checkpoint")
        subdir = TYPE_TO_COMFY_DIR.get(model_type, "checkpoints")
        base = Path(comfyui_root).expanduser() / "models" / subdir
        base.mkdir(parents=True, exist_ok=True)
        return base / fname
    else:
        return Path.cwd() / fname


def _do_download(version_id: int, token: str | None,
                 output: str | None, comfyui_dir: str | None,
                 name: str | None, prefer: str, resume: bool) -> None:
    """Core download logic: fetch info → pick file → download."""
    # 1. Get version info
    print(f"🔍 Fetching version {version_id}...", file=sys.stderr)
    version_info = request_json(build_url(f"/model-versions/{version_id}"), token)

    # 2. Get model info (for type & name)
    model_id = version_info.get("modelId")
    model_info = {}
    if model_id:
        try:
            model_info = request_json(build_url(f"/models/{model_id}"), token)
        except Exception:
            pass

    # 3. Pick file
    files = version_info.get("files", [])
    if not files:
        print("❌ No files found in this version.", file=sys.stderr)
        sys.exit(1)

    file_info = _pick_file(files, prefer)
    if not file_info:
        file_info = files[0]

    print(f"  Model: {model_info.get('name', '?')}  ({model_info.get('type', '?')})", file=sys.stderr)
    print(f"  File:  {file_info.get('name', '?')}  ({_friendly_size(file_info.get('sizeKB', 0)*1024)})", file=sys.stderr)

    # 4. Determine output path
    dest = _resolve_output_path(model_info, version_info, file_info, output, comfyui_dir, name)
    print(f"  Dest:  {dest}", file=sys.stderr)

    # 5. Build download URL
    params = {"type": file_info.get("type", "Model"), "format": file_info.get("metadata", {}).get("format", "SafeTensor")}
    # Filter file-specific params
    for key in ("size", "fp"):
        val = file_info.get("metadata", {}).get(key) or file_info.get(key)
        if val:
            params[key] = val
    if token:
        params["token"] = token
    dl_url = f"{DOWNLOAD_BASE_URL}/{version_id}"
    if params:
        dl_url = f"{dl_url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v})}"

    # 6. Download
    _download_file(dl_url, dest, resume=resume)

    # 7. Print result as JSON for automation
    print_json({
        "status": "downloaded",
        "path": str(dest),
        "model_id": model_id,
        "version_id": version_id,
        "file": file_info.get("name"),
        "size_kb": file_info.get("sizeKB", 0),
        "hash": file_info.get("hashes", {}),
    })


def cmd_download(args, token):
    """Download a model file by version ID."""
    _do_download(
        version_id=args.version_id,
        token=token,
        output=args.output,
        comfyui_dir=args.comfyui_dir,
        name=args.name,
        prefer=args.prefer,
        resume=args.resume,
    )


def cmd_download_model(args, token):
    """Download a model by model ID (auto-picks latest version)."""
    print(f"🔍 Fetching model {args.model_id}...", file=sys.stderr)
    model_info = request_json(build_url(f"/models/{args.model_id}"), token)

    versions = model_info.get("modelVersions", [])
    if not versions:
        print("❌ No versions found for this model.", file=sys.stderr)
        sys.exit(1)

    # Pick latest / specified version
    if args.version_name:
        target = next((v for v in versions if v.get("name") == args.version_name), None)
        if not target:
            print(f"❌ Version '{args.version_name}' not found.", file=sys.stderr)
            sys.exit(1)
    else:
        target = versions[0]  # API returns newest first

    version_id = target["id"]
    print(f"  Version: {target.get('name', version_id)} (id={version_id})", file=sys.stderr)

    _do_download(
        version_id=version_id,
        token=token,
        output=args.output,
        comfyui_dir=args.comfyui_dir,
        name=args.name,
        prefer=args.prefer,
        resume=args.resume,
    )


# ── Main ──

def main():
    script_dir = Path(__file__).resolve().parent
    load_env_file(script_dir)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="Civitai public REST API — search, inspect, download models."
    )
    parser.add_argument(
        "--token", default=os.getenv("CIVITAI_API_KEY"),
        help="Civitai API token. Defaults to CIVITAI_API_KEY env var."
    )
    parser.add_argument(
        "--host", default="civitai.com", choices=list(HOST_ALIASES.keys()),
        help="API host domain"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── Search / Inspect ──

    p = subparsers.add_parser("models", help="Search or list models")
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int)
    p.add_argument("--cursor")
    p.add_argument("--types")
    p.add_argument("--sort")
    p.add_argument("--period")
    p.add_argument("--username")
    p.add_argument("--tag")
    p.add_argument("--nsfw", choices=["true", "false"])
    p.set_defaults(func=cmd_models)

    p = subparsers.add_parser("model", help="Get one model by id")
    p.add_argument("model_id", type=int)
    p.set_defaults(func=cmd_model)

    p = subparsers.add_parser("version", help="Get one model version by id")
    p.add_argument("version_id", type=int)
    p.set_defaults(func=cmd_version)

    p = subparsers.add_parser("by-hash", help="Look up model version by file hash")
    p.add_argument("hash_value")
    p.set_defaults(func=cmd_hash)

    p = subparsers.add_parser("creators", help="Search or list creators")
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int)
    p.add_argument("--cursor")
    p.set_defaults(func=cmd_creators)

    p = subparsers.add_parser("tags", help="Search or list tags")
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int)
    p.add_argument("--cursor")
    p.set_defaults(func=cmd_tags)

    p = subparsers.add_parser("images", help="Search or list images")
    p.add_argument("--post-id", type=int)
    p.add_argument("--model-id", type=int)
    p.add_argument("--model-version-id", type=int)
    p.add_argument("--username")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int)
    p.add_argument("--cursor")
    p.add_argument("--sort")
    p.add_argument("--period")
    p.add_argument("--nsfw", choices=["true", "false"])
    p.set_defaults(func=cmd_images)

    # ── Model Versions advanced ──

    p = subparsers.add_parser("by-hash-batch", help="Batch lookup model versions by hashes (POST)")
    p.add_argument("hashes", help="Comma-separated hash list")
    p.set_defaults(func=cmd_by_hash_batch)

    p = subparsers.add_parser("by-hash-ids", help="Batch hash → version IDs only (POST, lightweight)")
    p.add_argument("hashes", help="Comma-separated hash list")
    p.set_defaults(func=cmd_by_hash_ids)

    p = subparsers.add_parser("version-mini", help="Get lightweight model version info")
    p.add_argument("version_id", type=int)
    p.set_defaults(func=cmd_version_mini)

    # ── Users ──

    p = subparsers.add_parser("me", help="Get current user info (requires auth)")
    p.set_defaults(func=cmd_me)

    p = subparsers.add_parser("users", help="Search or list users")
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int)
    p.add_argument("--cursor")
    p.set_defaults(func=cmd_users)

    # ── Permissions ──

    p = subparsers.add_parser("permissions", help="Check user permissions")
    p.add_argument("--model-id", type=int)
    p.add_argument("--model-version-id", type=int)
    p.set_defaults(func=cmd_permissions)

    # ── Vault ──

    p = subparsers.add_parser("vault", help="Get or create your vault (membership required)")
    p.set_defaults(func=cmd_vault_get)

    p = subparsers.add_parser("vault-items", help="List all items in your vault")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--page", type=int)
    p.add_argument("--cursor")
    p.set_defaults(func=cmd_vault_all)

    p = subparsers.add_parser("vault-check", help="Check if model versions are in your vault")
    p.add_argument("version_ids", help="Comma-separated model version IDs")
    p.set_defaults(func=cmd_vault_check)

    p = subparsers.add_parser("vault-toggle", help="Add or remove a model version from vault")
    p.add_argument("version_id", type=int)
    p.set_defaults(func=cmd_vault_toggle)

    # ── Enums ──

    p = subparsers.add_parser("enums", help="List available enum values (model types, sort options, etc.)")
    p.set_defaults(func=cmd_enums)

    # ── Download helpers ──

    p = subparsers.add_parser("download-url", help="Build download URL (no actual download)")
    p.add_argument("version_id", type=int)
    p.add_argument("--type")
    p.add_argument("--format")
    p.add_argument("--size")
    p.add_argument("--fp")
    p.set_defaults(func=cmd_download_url)

    p = subparsers.add_parser("download", help="Download model file by version ID")
    p.add_argument("version_id", type=int)
    p.add_argument("--output", "-o", help="Output file path")
    p.add_argument("--comfyui-dir", help="ComfyUI root dir (auto-places in models/<type>/)")
    p.add_argument("--name", help="Custom filename")
    p.add_argument("--prefer", default="safetensors", help="Preferred file type (default: safetensors)")
    p.add_argument("--resume", action="store_true", help="Resume partial download")
    p.set_defaults(func=cmd_download)

    p = subparsers.add_parser("download-model", help="Download model by model ID (auto-picks latest version)")
    p.add_argument("model_id", type=int)
    p.add_argument("--version-name", help="Specific version name to download")
    p.add_argument("--output", "-o", help="Output file path")
    p.add_argument("--comfyui-dir", help="ComfyUI root dir (auto-places in models/<type>/)")
    p.add_argument("--name", help="Custom filename")
    p.add_argument("--prefer", default="safetensors", help="Preferred file type (default: safetensors)")
    p.add_argument("--resume", action="store_true", help="Resume partial download")
    p.set_defaults(func=cmd_download_model)

    args = parser.parse_args()
    # Set API host globally
    global BASE_URL, DOWNLOAD_BASE_URL
    BASE_URL, DOWNLOAD_BASE_URL = HOST_ALIASES.get(args.host, HOST_ALIASES["civitai.com"])
    try:
        args.func(args, args.token)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
