# Cryptography 50 Security Release 2.4.2 Design

## Goal

Publish a focused `spindle-token` 2.4.2 patch release that requires the
security-fixed `cryptography` 50 release line and completes the repository's
standard package, documentation, and GitHub publication workflow.

## Scope

- Require `cryptography >=50.0.0,<51.0.0` and lock version 50.0.0.
- Bump the package version from 2.4.1 to 2.4.2 in `pyproject.toml`,
  `src/spindle_token/__init__.py`, and version assertions.
- Add a 2.4.2 security and compatibility section to `CHANGELOG.md` covering
  CVE-2026-69247 and the upstream FFDH deprecation.
- Keep runtime APIs and token behavior unchanged unless verification exposes a
  compatibility problem that must be corrected for cryptography 50.0.0.
- Leave installation and usage documentation unchanged unless verification
  identifies a user-visible change.

## Dependency Policy

The published dependency range will be `cryptography >=50.0.0,<51.0.0`. This
preserves the repository's existing major-band policy: consumers receive
compatible 50.x fixes while a future cryptography major version requires an
explicitly tested spindle-token release.

Cryptography 50.0.0 fixes CVE-2026-69247 in PKCS7 decryption by preventing
distinguishable failures or timing during encrypted-key unwrap. The release
also deprecates finite-field Diffie-Hellman key exchange APIs. Spindle-token
does not intentionally use PKCS7 decryption or FFDH, so the upgrade is expected
to remain packaging-only; repository-wide searches and tests will verify that
assumption.

## Verification

- `poetry lock` and `poetry check --lock`.
- Confirm the declared range, locked version, installed version, and built
  wheel metadata all select cryptography 50.0.0 or a compatible 50.x release.
- Search the codebase for affected PKCS7 and FFDH APIs.
- Run the full test suite with SDKMAN Temurin 17, matching the established
  local Spark compatibility setup.
- Run `poetry run black --check .`.
- Build and inspect both wheel and source distribution with `poetry build`.
- Run `poetry run mkdocs build`.
- Install the built wheel in the target Databricks environment and run
  `docs/guides/databricks.ipynb` end to end.
- Review `git diff --check` and the complete release diff before delivery.

## Delivery

Prepare the release on `agent/release-2.4.2`, push it, and open a focused pull
request against `main`. After review and merge:

1. Confirm the merged commit and repeat the release verification required by
   `RELEASE.md`.
2. Create and push the annotated `v2.4.2` tag.
3. Create a draft GitHub release whose notes contain only the 2.4.2 changelog
   entry.
4. Publish the wheel and source distribution to PyPI.
5. Verify PyPI exposes version 2.4.2 with both artifacts before continuing.
6. Deploy the documentation site.
7. Publish the GitHub release and verify its public tag, title, notes, and
   target commit.

If package publication fails, stop without deploying documentation or
publishing the GitHub release. Never expose or persist PyPI credentials in
source, logs, documentation, or assistant output.
