# Cryptography Security Release 2.4.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare and publish a draft pull request for the focused `spindle-token` 2.4.1 security release.

**Architecture:** This is a packaging-only release. Raise the direct `cryptography` floor, synchronize the two package-version declarations, document the remediated upstream security issues and platform compatibility change, regenerate the Poetry lock, then verify the complete distributable.

**Tech Stack:** Python 3.13, Poetry 2.4.1, cryptography 49.0.0, PySpark 3.5.2, SDKMAN Temurin 17, MkDocs, Git, GitHub CLI.

## Global Constraints

- Release version is exactly `2.4.1`.
- `cryptography` must be constrained to `>=49.0.0,<50.0.0` and lock to 49.0.0.
- Do not change runtime behavior or public APIs.
- Do not change `README.md`; installation and usage are unchanged.
- Do not tag, publish to PyPI, deploy documentation, or publish a GitHub release before merge.

---

### Task 1: Synchronize release metadata and notes

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/spindle_token/__init__.py`
- Modify: `tests/test_import_surface.py`
- Modify: `tests/test_packaging_integration.py`
- Modify: `CHANGELOG.md`
- Modify: `poetry.lock`

**Interfaces:**
- Consumes: existing package version 2.4.0 and locked cryptography 46.0.6
- Produces: consistent 2.4.1 package metadata and operator-facing release notes

- [x] **Step 1: Change both package-version declarations to 2.4.1**

Set `project.version`, `spindle_token.__version__`, and the import-surface
version assertion to `2.4.1`. Make the packaging integration test derive wheel
and metadata paths from `spindle_token.__version__` so it validates the current
release artifact instead of a stale hard-coded version.

- [x] **Step 2: Add the 2.4.1 changelog entry**

Add a `Security and Compatibility` section that states:

- `cryptography` is upgraded to 49.0.0 or newer within major version 49.
- The raised floor excludes vulnerable wildcard DNS SAN handling under
  constrained CAs, while noting that the previous 46.0.6 lock already contained
  that verifier fix.
- The lock upgrade includes the CVE-2026-39892 buffer-overflow fix first shipped
  in cryptography 46.0.7.
- The official wheels include the OpenSSL security updates first shipped in
  cryptography 48.0.1.
- Upstream 49.0.0 removes macOS x86-64 and 32-bit Windows wheels.

- [x] **Step 3: Regenerate and validate the Poetry lock**

Run:

```bash
poetry lock
poetry check --lock
```

Expected: the lock is consistent, `spindle-token` metadata is 2.4.1, and cryptography remains 49.0.0.

### Task 2: Verify the release candidate

**Files:**
- Verify: all tracked project files
- Generated and removed after inspection: `dist/`, `site/`

**Interfaces:**
- Consumes: Task 1 release metadata
- Produces: a tested wheel/sdist and verified documentation build

- [x] **Step 1: Verify dependency versions and runtime OpenSSL**

Run a Python assertion that confirms the declared floor, locked version 49.0.0, installed version 49.0.0, and OpenSSL backend 4.0.1.

- [x] **Step 2: Run the full suite under JDK 17**

```bash
JAVA_HOME=/Users/erikdreyer/.sdkman/candidates/java/17.0.20-tem poetry run pytest
```

Expected: 68 tests pass.

- [x] **Step 3: Run formatting, build, and docs checks**

```bash
poetry run black --check .
poetry build
poetry run mkdocs build
```

Expected: all commands exit zero.

- [x] **Step 4: Inspect artifacts and diff hygiene**

Confirm wheel metadata reports version 2.4.1 and dependency `cryptography <50.0.0,>=49.0.0`; then remove only the generated `dist/` and `site/` directories and run `git diff --check`.

### Task 3: Publish the draft pull request

**Files:**
- Commit: `CHANGELOG.md`, `pyproject.toml`, `poetry.lock`,
  `src/spindle_token/__init__.py`, `tests/test_import_surface.py`,
  `tests/test_packaging_integration.py`, the release design, and this plan

**Interfaces:**
- Consumes: verified release candidate from Task 2
- Produces: pushed branch and draft PR against `main`

- [ ] **Step 1: Review and stage only release files**

Run `git status -sb` and inspect the complete diff before staging explicit paths.

- [ ] **Step 2: Commit the release preparation**

```bash
git commit -m "chore: prepare 2.4.1 security release"
```

- [ ] **Step 3: Push and open a draft PR**

Push `agent/release-2.4.1` to `origin` and open a draft PR against `main` explaining the security fixes, compatibility impact, reachability assessment, and verification evidence.
