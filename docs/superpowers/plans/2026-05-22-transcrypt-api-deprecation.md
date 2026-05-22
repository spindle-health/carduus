# Transcrypt API Deprecation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add `transcrypt_out()` and `transcrypt_in()` as the preferred public APIs while keeping the existing `transcode_out()` and `transcode_in()` APIs as deprecated compatibility wrappers.

**Architecture:** Keep the cryptographic behavior unchanged by routing the new APIs through the same Spark and OPPRL protocol code paths. Add canonical `transcrypt_*` names at the top-level module, Spark implementation layer, protocol extension surface, and CLI. Leave old `transcode_*` names in place with `DeprecationWarning` wrappers and documentation that points users to the new names.

**Tech Stack:** Python 3.10+, PySpark, Click, pytest, mkdocs/mkdocstrings/mkdocs-click.

---

## File Structure

- Modify `src/spindle_token/__init__.py`: expose `transcrypt_out` and `transcrypt_in`; keep deprecated `transcode_out` and `transcode_in` wrappers.
- Modify `src/spindle_token/_spark.py`: add canonical Spark-backed `transcrypt_out` and `transcrypt_in`; keep deprecated wrappers.
- Modify `src/spindle_token/core.py`: add `TokenProtocol.transcrypt_out` and `TokenProtocol.transcrypt_in` default methods without breaking existing custom protocols that only implement `transcode_*`.
- Modify `src/spindle_token/opprl/v0.py`, `src/spindle_token/opprl/v1.py`, `src/spindle_token/opprl/v2.py`: add explicit protocol `transcrypt_*` methods and keep `transcode_*` compatibility methods.
- Modify `src/spindle_token/_cli.py`: add `spindle-token transcrypt in/out`; keep `spindle-token transcode in/out` as deprecated CLI aliases.
- Modify tests in `tests/test_import_surface.py`, `tests/test_packaging_surface.py`, `tests/test_tokenize.py`, and `tests/test_cli.py`: cover preferred names and deprecated aliases.
- Modify docs in `README.md`, `docs/README.md`, `docs/guides/getting-started.md`, `docs/guides/migrating-from-carduus.md`, `docs/guides/custom-tokens.md`, `docs/cli.md`, Databricks notebooks, `PROTOCOL.md`, `docs/opprl/PROTOCOL.md`, and `CHANGELOG.md`.
- Do not modify `pyproject.toml` version or `src/spindle_token/__init__.py::__version__` in this work.

### Task 1: Public Python API Tests

**Files:**
- Modify: `tests/test_import_surface.py`
- Modify: `tests/test_tokenize.py`

- [x] **Step 1: Add import-surface expectations for new and old names**

Update the `spindle_token.__all__` assertion in `tests/test_import_surface.py` so the public API contains preferred names before deprecated names:

```python
assert spindle_token.__all__ == [
    "PiiAttribute",
    "Token",
    "TokenProtocol",
    "tokenize",
    "transcrypt_out",
    "transcrypt_in",
    "transcode_out",
    "transcode_in",
    "generate_pem_keys",
]
```

- [x] **Step 2: Run the import-surface test and verify it fails**

Run:

```bash
poetry run pytest tests/test_import_surface.py::test_base_package_imports_without_pyspark -q
```

Expected: fail because `transcrypt_out` and `transcrypt_in` are not exported yet.

- [x] **Step 3: Update Spark behavior tests to call preferred names**

In `tests/test_tokenize.py`, change the import to:

```python
from spindle_token import tokenize, transcrypt_out, transcrypt_in, transcode_out, transcode_in
```

Then update the main behavior, generator, null-safety, env-key, and key-validation tests so preferred-path assertions call `transcrypt_out` and `transcrypt_in`.

- [x] **Step 4: Add deprecated-wrapper warning tests**

Add focused tests near the existing transcrypt behavior tests:

```python
def test_transcode_out_deprecated_alias_warns(
    spark: SparkSession,
    private_key: bytes,
    acme_public_key: bytes,
):
    pii = spark.createDataFrame(
        [Row(first_name="Louis", last_name="Pasteur", gender="male", birth_date="1822-12-27")]
    )
    tokenized = tokenize(
        pii,
        col_mapping={
            v2.first_name: "first_name",
            v2.last_name: "last_name",
            v2.gender: "gender",
            v2.birth_date: "birth_date",
        },
        tokens=[v2.token1],
        private_key=private_key,
    )

    with pytest.warns(DeprecationWarning, match="transcode_out\\(\\) is deprecated"):
        actual = transcode_out(
            tokenized,
            [v2.token1],
            recipient_public_key=acme_public_key,
            private_key=private_key,
        )

    assert v2.token1.name in actual.columns


def test_transcode_in_deprecated_alias_warns(
    spark: SparkSession,
    private_key: bytes,
    acme_public_key: bytes,
    acme_private_key: bytes,
):
    pii = spark.createDataFrame(
        [Row(first_name="Louis", last_name="Pasteur", gender="male", birth_date="1822-12-27")]
    )
    tokenized = tokenize(
        pii,
        col_mapping={
            v2.first_name: "first_name",
            v2.last_name: "last_name",
            v2.gender: "gender",
            v2.birth_date: "birth_date",
        },
        tokens=[v2.token1],
        private_key=private_key,
    )
    ephemeral = transcrypt_out(
        tokenized,
        [v2.token1],
        recipient_public_key=acme_public_key,
        private_key=private_key,
    )

    with pytest.warns(DeprecationWarning, match="transcode_in\\(\\) is deprecated"):
        actual = transcode_in(ephemeral, [v2.token1], private_key=acme_private_key)

    assert v2.token1.name in actual.columns
```

- [x] **Step 5: Run targeted tests and verify they fail for missing implementation**

Run:

```bash
poetry run pytest tests/test_import_surface.py tests/test_tokenize.py -q
```

Expected: fail because preferred public APIs are not implemented yet.

### Task 2: Public Python API Implementation

**Files:**
- Modify: `src/spindle_token/__init__.py`
- Modify: `src/spindle_token/_spark.py`
- Modify: `src/spindle_token/core.py`
- Modify: `src/spindle_token/opprl/v0.py`
- Modify: `src/spindle_token/opprl/v1.py`
- Modify: `src/spindle_token/opprl/v2.py`

- [x] **Step 1: Add deprecation helper imports**

In `src/spindle_token/__init__.py` and `src/spindle_token/_spark.py`, import `warn`:

```python
from warnings import warn
```

- [x] **Step 2: Add preferred top-level API wrappers**

In `src/spindle_token/__init__.py`, export and implement:

```python
def transcrypt_out(
    df: DataFrame,
    tokens: Iterable[Token],
    recipient_public_key: bytes | None = None,
    private_key: bytes | None = None,
) -> DataFrame:
    return _spark_api().transcrypt_out(df, tokens, recipient_public_key, private_key)


def transcrypt_in(
    df: DataFrame,
    tokens: Iterable[Token],
    private_key: bytes | None = None,
) -> DataFrame:
    return _spark_api().transcrypt_in(df, tokens, private_key)
```

Then make `transcode_out` and `transcode_in` wrappers warn and delegate:

```python
warn(
    "transcode_out() is deprecated; use transcrypt_out() instead.",
    DeprecationWarning,
    stacklevel=2,
)
return transcrypt_out(df, tokens, recipient_public_key, private_key)
```

```python
warn(
    "transcode_in() is deprecated; use transcrypt_in() instead.",
    DeprecationWarning,
    stacklevel=2,
)
return transcrypt_in(df, tokens, private_key)
```

- [x] **Step 3: Add protocol extension default methods**

In `src/spindle_token/core.py`, add default methods to `TokenProtocol`:

```python
def transcrypt_out(self, token: Column) -> Column:
    """Transcrypts the given token into an ephemeral token."""
    return self.transcode_out(token)


def transcrypt_in(self, ephemeral_token: Column) -> Column:
    """Transcrypts the given ephemeral token into a normal token."""
    return self.transcode_in(ephemeral_token)
```

Keep `transcode_out` and `transcode_in` abstract for backwards compatibility with existing custom protocol implementations.

- [x] **Step 4: Add preferred Spark implementations**

In `src/spindle_token/_spark.py`, rename the implementation bodies to `transcrypt_out` and `transcrypt_in`. Inside those functions, call protocol methods by preferred names:

```python
token.name: protocols[token.protocol.factory_id].transcrypt_out(col(token.name))
```

```python
token.name: protocols[token.protocol.factory_id].transcrypt_in(col(token.name))
```

Keep `transcode_out` and `transcode_in` wrappers with `DeprecationWarning`.

- [x] **Step 5: Add explicit OPPRL preferred protocol methods**

In `src/spindle_token/opprl/v0.py`, `src/spindle_token/opprl/v1.py`, and `src/spindle_token/opprl/v2.py`, add `transcrypt_out` and `transcrypt_in` methods with the current implementation bodies. Keep `transcode_out` and `transcode_in` as compatibility methods delegating to the preferred methods.

- [x] **Step 6: Run targeted Python API tests**

Run:

```bash
poetry run pytest tests/test_import_surface.py tests/test_tokenize.py -q
```

Expected: pass.

### Task 3: CLI Tests and Implementation

**Files:**
- Modify: `tests/test_packaging_surface.py`
- Modify: `tests/test_cli.py`
- Modify: `src/spindle_token/_cli.py`

- [x] **Step 1: Update CLI help tests**

In `tests/test_packaging_surface.py`, assert preferred and deprecated command groups are visible:

```python
assert "transcrypt" in result.output
assert "transcode" in result.output
```

- [x] **Step 2: Update CLI behavior tests to use preferred command**

In `tests/test_cli.py`, change existing successful transcode command invocations from:

```python
"transcode",
```

to:

```python
"transcrypt",
```

Keep at least one focused deprecated alias test that invokes `["transcode", "out", ...]` and asserts the command still succeeds.

- [x] **Step 3: Run CLI tests and verify failure**

Run:

```bash
poetry run pytest tests/test_packaging_surface.py tests/test_cli.py -q
```

Expected: fail because the `transcrypt` command group does not exist yet.

- [x] **Step 4: Add CLI preferred group and deprecated alias**

In `src/spindle_token/_cli.py`, rename the implementation helper to `_run_transcrypt`, import preferred APIs, and add:

```python
@cli.group()
def transcrypt():
    """Prepare tokenized datasets to be sent or received."""
    pass
```

Register `out` and `in` under `transcrypt`. Then add `transcode` as a hidden or visibly deprecated compatibility group. Prefer visible compatibility for one release so users can discover the migration from `--help`.

- [x] **Step 5: Run CLI tests**

Run:

```bash
poetry run pytest tests/test_packaging_surface.py tests/test_cli.py -q
```

Expected: pass.

### Task 4: Documentation and Website Source

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/guides/getting-started.md`
- Modify: `docs/guides/migrating-from-carduus.md`
- Modify: `docs/guides/custom-tokens.md`
- Modify: `docs/cli.md`
- Modify: `docs/guides/databricks.ipynb`
- Modify: `docs/guides/databricks-spark35.ipynb`
- Modify: `docs/guides/databricks-spark4.ipynb`
- Modify: `PROTOCOL.md`
- Modify: `docs/opprl/PROTOCOL.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Update user-facing terminology**

Use "transcrypt" and "transcryption" for the public API and workflow naming. Keep old `transcode` wording only when discussing deprecated aliases or legacy references.

- [x] **Step 2: Update Python examples**

Replace:

```python
from spindle_token import transcode_out, transcode_in
```

with:

```python
from spindle_token import transcrypt_out, transcrypt_in
```

Replace `transcode_out(...)` and `transcode_in(...)` calls with `transcrypt_out(...)` and `transcrypt_in(...)`.

- [x] **Step 3: Update CLI examples and mkdocs-click config**

In `docs/cli.md`, document `spindle-token transcrypt` as the preferred command and call out `spindle-token transcode` as deprecated for compatibility. Update the mkdocs-click block to generate preferred command docs:

```markdown
::: mkdocs-click
    :module: spindle_token._cli
    :command: transcrypt
    :prog_name: spindle-token transcrypt
    :depth: 1
```

- [x] **Step 4: Update Carduus migration narrative**

Change the migration guide so it no longer says Spindle intentionally chose `transcode`. It should say Spindle now uses the `transcrypt_*` naming, with `transcode_*` retained as deprecated compatibility aliases.

- [x] **Step 5: Update protocol docs without breaking anchors**

Update section titles and prose to use "Transcrypting Tokens" where appropriate, but keep existing explicit anchors such as:

```markdown
# <a name="transcode"></a> 7. Transcrypting Tokens
## <a name="transcode_out"></a> 7.1 Data Flow: Custodian Tokens to Ephemeral Tokens
```

This preserves external links while changing visible terminology.

- [x] **Step 6: Add changelog entry without bumping package version**

Add an `## Unreleased` section to `CHANGELOG.md`:

```markdown
## Unreleased

### API

- Added `transcrypt_out()` and `transcrypt_in()` as the preferred names for
  preparing tokenized datasets for sharing and restoring received ephemeral
  tokens.
- Deprecated `transcode_out()` and `transcode_in()`; they remain available as
  compatibility aliases and emit `DeprecationWarning`.
- Added `spindle-token transcrypt` as the preferred CLI command while keeping
  `spindle-token transcode` as a deprecated compatibility command.
```

- [x] **Step 7: Run docs build**

Run:

```bash
poetry run mkdocs build
```

Expected: pass.

### Task 5: Full Verification

**Files:**
- No additional source edits unless verification finds failures.

- [x] **Step 1: Run formatting check**

Run:

```bash
poetry run black --check .
```

Expected: pass.

- [x] **Step 2: Run full test suite**

Run:

```bash
poetry run pytest
```

Expected: pass.

- [x] **Step 3: Check remaining old-name references**

Run:

```bash
rg -n "transcode|transcoding|transcoded" README.md docs src tests CHANGELOG.md PROTOCOL.md
```

Expected: remaining matches are only deprecated compatibility references, preserved anchors, historical Carduus material, or tests that explicitly cover aliases.

- [x] **Step 4: Check worktree status**

Run:

```bash
git status --short
```

Expected: only intentional files changed, plus any pre-existing unrelated `.gitignore` change.

