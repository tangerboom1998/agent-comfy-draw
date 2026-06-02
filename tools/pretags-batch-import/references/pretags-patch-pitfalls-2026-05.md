# Pretags patch pitfalls — 2026-05 artstyle batch import

## Why this note exists
During artstyle batch insertion into `pretags.json`, a patch near the tail of the `画风` object produced:

- `JSONDecodeError: Extra data`

The immediate cause was not bad field values. The structure around the enclosing object boundary was damaged:
- the inserted block ended correctly,
- but the next key (`"像素2"`) was left outside the `画风` object because the `},` / object boundary shifted.

## What to do after every patch
1. Run `json.load()` on the whole `pretags.json` immediately.
2. Re-read the exact inserted keys and confirm:
   - key exists under the intended category (`画风` / `人物` / etc.)
   - `model file name`
   - `model hash`
   - `link`
   - `tag`
3. If patching near the tail of a large object, inspect the next existing key too, to confirm it is still inside the same object.

## Tail-of-object danger signs
These are especially risky when inserting new entries at the end of a category object:
- patch adds a new `},` but accidentally also closes the parent object
- next sibling key is still present in text, but no longer nested under the category
- patch tool reports success, but parse fails with `Extra data`

## Recovery pattern
If parse fails with `JSONDecodeError: Extra data` after a successful patch:
1. Read the surrounding lines around the insertion point.
2. Compare the final inserted entry with the next original key.
3. Restore the missing category key line / comma / closing brace ordering.
4. Re-run `json.load()`.
5. Re-check the inserted keys.

## Session-specific lessons from this batch
- For artstyle imports, validate by parsing the whole file, not by trusting patch diff.
- A successful patch does **not** prove the JSON object nesting remained valid.
- File-name based duplicate checking is still necessary even after successful insertion, because same model family may appear under near-identical stems.
