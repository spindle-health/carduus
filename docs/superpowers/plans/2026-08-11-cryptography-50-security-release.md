# Cryptography 50 Security Release 2.4.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `spindle-token` 2.4.2 with a tested `cryptography >=50.0.0,<51.0.0` dependency contract.

**Architecture:** Keep the change packaging-only: prove the new release contract with existing import and built-wheel boundaries, synchronize release metadata and the Poetry lock, and verify the complete distributable. Deliver through the repository's pull-request gate, then tag and publish PyPI, documentation, and GitHub artifacts in dependency order.

**Tech Stack:** Python 3.13, Poetry 2, cryptography 50.0.0, PySpark 3.5.2, SDKMAN Temurin 17, pytest, MkDocs, Git, GitHub CLI, PyPI, Databricks.

## Global Constraints

- Release version is exactly `2.4.2`.
- Require `cryptography >=50.0.0,<51.0.0` and lock version 50.0.0.
- Keep runtime APIs and token behavior unchanged.
- Do not change installation or usage documentation unless verification identifies a user-visible change.
- Do not publish to PyPI until the built wheel passes the Databricks notebook gate.
- If PyPI publication fails, do not deploy documentation or publish the GitHub release.
- Never expose or persist PyPI or Databricks credentials in source, logs, documentation, or assistant output.

---

### Task 1: Make the v2.4.2 package contract executable

**Files:**
- Modify: `tests/test_import_surface.py`
- Modify: `tests/test_packaging_integration.py`
- Modify: `pyproject.toml`
- Modify: `src/spindle_token/__init__.py`
- Modify: `poetry.lock`
- Modify: `CHANGELOG.md`
- Commit: `docs/superpowers/plans/2026-08-11-cryptography-50-security-release.md`

**Interfaces:**
- Consumes: current version `2.4.1` and dependency range `cryptography >=49.0.0,<50.0.0`.
- Produces: import version `2.4.2` and wheel metadata containing `Requires-Dist: cryptography (>=50.0.0,<51.0.0)`.

- [x] **Step 1: Change the import-boundary assertion first**

In `tests/test_import_surface.py`, change only the subprocess assertion to:

```python
assert spindle_token.__version__ == "2.4.2"
```

- [x] **Step 2: Run the import test and verify RED**

Run:

```bash
poetry run pytest tests/test_import_surface.py::test_base_package_imports_without_pyspark -q
```

Expected: FAIL because the imported package still reports `2.4.1`.

- [x] **Step 3: Add the built-wheel dependency assertion first**

In `tests/test_packaging_integration.py`, add this assertion after reading `METADATA`:

```python
assert "Requires-Dist: cryptography (>=50.0.0,<51.0.0)" in metadata
```

- [x] **Step 4: Run the packaging test and verify RED**

Run:

```bash
poetry run pytest tests/test_packaging_integration.py::test_wheel_metadata_marks_pyspark_as_spark_extra_only -q
```

Expected: FAIL because the built wheel still declares `cryptography (>=49.0.0,<50.0.0)`.

- [x] **Step 5: Apply the minimal release metadata changes**

In `pyproject.toml`, set:

```toml
version = "2.4.2"
```

and:

```toml
"cryptography (>=50.0.0,<51.0.0)",
```

In `src/spindle_token/__init__.py`, set:

```python
__version__ = "2.4.2"
```

- [x] **Step 6: Add the focused changelog entry**

Insert the following before `## 2.4.1` in `CHANGELOG.md`:

```markdown
## 2.4.2

### Security and Compatibility

- Raised the minimum `cryptography` version to 50.0.0, which fixes
  CVE-2026-69247 by preventing distinguishable errors or timing during PKCS7
  encrypted-key unwrap from acting as a Bleichenbacher oracle.
- Adopted the upstream deprecation of finite-field Diffie-Hellman key exchange.
  `spindle-token` does not use the deprecated FFDH APIs.
```

- [x] **Step 7: Regenerate and validate the lock**

Run:

```bash
poetry lock
poetry check --lock
```

Expected: both commands exit zero and `poetry.lock` selects cryptography 50.0.0.

- [x] **Step 8: Run both release-contract tests and verify GREEN**

Run:

```bash
poetry run pytest tests/test_import_surface.py::test_base_package_imports_without_pyspark tests/test_packaging_integration.py::test_wheel_metadata_marks_pyspark_as_spark_extra_only -q
```

Expected: 2 tests pass.

- [x] **Step 9: Commit the tested release contract**

```bash
git add CHANGELOG.md pyproject.toml poetry.lock src/spindle_token/__init__.py tests/test_import_surface.py tests/test_packaging_integration.py docs/superpowers/plans/2026-08-11-cryptography-50-security-release.md
git diff --cached --check
git commit -m "chore: prepare 2.4.2 security release"
```

### Task 2: Verify the complete release candidate

**Files:**
- Verify: all tracked project files.
- Generate temporarily: `dist/`, `site/`.

**Interfaces:**
- Consumes: the v2.4.2 release contract from Task 1.
- Produces: verified wheel and sdist artifacts plus a successful Databricks notebook result.

- [ ] **Step 1: Confirm affected APIs are unreachable in production code**

Run:

```bash
rg -n "pkcs7|PKCS7|asymmetric\\.dh|Diffie|DHPrivate|DHPublic" src tests
```

Expected: no matches.

- [ ] **Step 2: Confirm declared, locked, and installed dependency state**

Run:

```bash
poetry install
poetry run python -c 'import cryptography, pathlib, tomllib; p=tomllib.loads(pathlib.Path("pyproject.toml").read_text()); lock=tomllib.loads(pathlib.Path("poetry.lock").read_text()); locked=next(x for x in lock["package"] if x["name"] == "cryptography"); assert p["project"]["version"] == "2.4.2"; assert "cryptography (>=50.0.0,<51.0.0)" in p["project"]["dependencies"]; assert locked["version"] == "50.0.0"; assert cryptography.__version__ == "50.0.0"; print(cryptography.__version__)'
```

Expected: exit zero and output `50.0.0`.

- [ ] **Step 3: Run the full test suite under JDK 17**

Run:

```bash
JAVA_HOME=/Users/erikdreyer/.sdkman/candidates/java/17.0.20-tem poetry run pytest
```

Expected: all tests pass with zero failures.

- [ ] **Step 4: Run formatting, package, and documentation checks**

Run:

```bash
poetry run black --check .
poetry build
poetry run mkdocs build --strict
```

Expected: each command exits zero; `dist/` contains one 2.4.2 wheel and one 2.4.2 source distribution.

- [ ] **Step 5: Inspect the built artifacts**

Run:

```bash
poetry run python -c 'import pathlib, tarfile, zipfile; d=pathlib.Path("dist"); w=next(d.glob("spindle_token-2.4.2-*.whl")); s=next(d.glob("spindle_token-2.4.2.tar.gz")); z=zipfile.ZipFile(w); m=z.read("spindle_token-2.4.2.dist-info/METADATA").decode(); assert "Version: 2.4.2" in m; assert "Requires-Dist: cryptography (>=50.0.0,<51.0.0)" in m; t=tarfile.open(s); assert any(n.endswith("/pyproject.toml") for n in t.getnames()); print(w, s)'
```

Expected: exit zero and the two artifact paths are printed.

- [ ] **Step 6: Pass the Databricks notebook release gate**

Install `dist/spindle_token-2.4.2-py3-none-any.whl` into the target Databricks environment and run `docs/guides/databricks.ipynb` end to end. Record confirmation that every cell completed successfully. The current CLI profile reports invalid authentication, so refresh it securely or complete this gate in the signed-in Databricks UI; do not place credentials in commands or chat.

- [ ] **Step 7: Check release diff hygiene**

Run:

```bash
git diff --check
git status --short --branch
git log -2 --oneline --decorate
```

Expected: no tracked release changes remain uncommitted; only ignored generated `dist/` and `site/` artifacts may exist.

### Task 3: Merge the focused release pull request

**Files:**
- Deliver: the two commits on `agent/release-2.4.2`.

**Interfaces:**
- Consumes: verified release candidate and successful Databricks gate.
- Produces: v2.4.2 release commit merged into `origin/main` with green CI.

- [ ] **Step 1: Push and create the pull request**

```bash
git push -u origin agent/release-2.4.2
gh pr create --base main --head agent/release-2.4.2 --title "chore: prepare 2.4.2 security release" --body "## Summary
- require cryptography 50.x to remediate CVE-2026-69247
- bump spindle-token to 2.4.2 and refresh the lock
- document and verify the compatibility boundary

## Verification
- full pytest suite under Temurin 17
- Black check
- wheel and sdist build plus metadata inspection
- strict MkDocs build
- Databricks notebook validation"
```

- [ ] **Step 2: Wait for and verify every required check**

Run:

```bash
gh pr checks --watch
```

Expected: all required checks pass.

- [ ] **Step 3: Merge through the protected branch**

Run:

```bash
gh pr merge --squash --delete-branch
git switch main
git pull --ff-only
```

Expected: the PR is merged, local `main` equals `origin/main`, and the merged commit contains version 2.4.2.

### Task 4: Publish and verify v2.4.2

**Files:**
- Publish: `dist/spindle_token-2.4.2-py3-none-any.whl`.
- Publish: `dist/spindle_token-2.4.2.tar.gz`.
- Deploy: generated MkDocs site.

**Interfaces:**
- Consumes: merged and verified v2.4.2 commit.
- Produces: immutable `v2.4.2` tag, PyPI release, deployed docs, and public GitHub release.

- [ ] **Step 1: Rebuild and reverify the merged release commit**

Run:

```bash
poetry install
JAVA_HOME=/Users/erikdreyer/.sdkman/candidates/java/17.0.20-tem poetry run pytest
poetry run black --check .
poetry build
poetry run mkdocs build --strict
git status --short --branch
```

Expected: tests and builds pass, the worktree is clean, and the artifacts are version 2.4.2.

- [ ] **Step 2: Create and push the annotated release tag**

Run:

```bash
git tag -a v2.4.2 -m "Release v2.4.2"
git push origin v2.4.2
git ls-remote --tags origin v2.4.2 v2.4.2^{}
```

Expected: the remote annotated tag peels to the verified `main` commit.

- [ ] **Step 3: Create and inspect the draft GitHub release**

Run:

```bash
gh release create v2.4.2 --draft --verify-tag --title v2.4.2 --notes "## Security and Compatibility

- Raised the minimum \`cryptography\` version to 50.0.0, which fixes CVE-2026-69247 by preventing distinguishable errors or timing during PKCS7 encrypted-key unwrap from acting as a Bleichenbacher oracle.
- Adopted the upstream deprecation of finite-field Diffie-Hellman key exchange. \`spindle-token\` does not use the deprecated FFDH APIs."
gh release view v2.4.2 --json isDraft,name,tagName,targetCommitish,url
```

Expected: a draft named and tagged `v2.4.2`, targeting the release commit, with only the 2.4.2 notes.

- [ ] **Step 4: Publish to PyPI**

Run without printing or changing stored credentials:

```bash
poetry publish --no-interaction
```

Expected: both the wheel and source distribution upload successfully. If authentication or upload fails, stop here.

- [ ] **Step 5: Verify PyPI before downstream publication**

Run:

```bash
curl -fsSL https://pypi.org/pypi/spindle-token/json | jq -e '.info.version == "2.4.2" and (.releases["2.4.2"] | length) == 2 and (any(.releases["2.4.2"][]; .packagetype == "bdist_wheel")) and (any(.releases["2.4.2"][]; .packagetype == "sdist"))'
```

Expected: `true` and exit zero.

- [ ] **Step 6: Deploy documentation and publish the GitHub release**

Run:

```bash
poetry run mkdocs gh-deploy
gh release edit v2.4.2 --draft=false
```

Expected: docs deploy succeeds and the GitHub release becomes public.

- [ ] **Step 7: Verify final public state**

Run:

```bash
gh release view v2.4.2 --json isDraft,isPrerelease,name,tagName,publishedAt,targetCommitish,url
curl -fsSL https://pypi.org/pypi/spindle-token/2.4.2/json | jq -e '.info.version == "2.4.2" and (.urls | length) == 2'
git status --short --branch
```

Expected: the GitHub release is public and non-prerelease, PyPI returns exactly two v2.4.2 artifacts, and `main` is clean and synchronized with `origin/main`.
