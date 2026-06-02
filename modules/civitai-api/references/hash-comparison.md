# SHA256 vs AutoV2 Hash Comparison

## The Problem

CivitAI API returns **full 64-character SHA256** hashes. Local registries like `pretags.json` store **AutoV2 format** (first 10 characters of SHA256).

Using `==` to compare them will **always return False**, even when the files are identical.

## Reproduction (from actual session failure)

```python
# What the API returns:
civitai_hash = "D244DCA73C1DDAD927136FB23AEF63519CC46D5930D9ACDDBD..."  # 64 chars

# What pretags stores:
pretags_hash = "D244DCA73C"  # 10 chars (AutoV2)

# BUG: exact comparison
in_local = civitai_hash in known_hashes  # False! Always False!

# Result: 35 real matches across 19 tanger models were reported as "not in local"
# User caught the error: "不可能没有匹配，仔细对比hash"
```

## The Fix

```python
# CORRECT: prefix matching
in_local = any(civitai_hash.startswith(ph) for ph in known_hashes)

# Or normalize both to the same format
civitai_short = civitai_hash[:10]
in_local = civitai_short in known_hashes
```

## Hash Formats

| Format | Length | Example | Source |
|--------|--------|---------|--------|
| SHA256 full | 64 chars | `D244DCA73C1DDAD927136FB23AEF63519CC46D5930D9ACDDBD...` | CivitAI API |
| AutoV2 | 10 chars | `D244DCA73C` | First 10 of SHA256 |
| AutoV1 | 8 chars | `...` | Legacy, first 8 of SHA256 |
| AutoV3 | 12 chars | `...` | Newer format |

pretags.json uses **AutoV2** (10 chars).

## When This Bites

Any time you:
1. Fetch model data from CivitAI API
2. Compare its file hashes against a local registry
3. Use `==` instead of `startswith()` or slice normalization

The error is silent — no errors, just all False results. The only clue is "impossible zero matches" when you know some files must overlap.
