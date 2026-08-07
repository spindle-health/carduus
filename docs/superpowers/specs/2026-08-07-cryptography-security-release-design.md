# Cryptography Security Release 2.4.1 Design

## Goal

Publish a focused `spindle-token` 2.4.1 patch release that excludes vulnerable
`cryptography` versions and records the security impact clearly for operators.

## Scope

- Require `cryptography >=49.0.0,<50.0.0` and lock version 49.0.0.
- Bump the package version from 2.4.0 to 2.4.1 in `pyproject.toml` and
  `src/spindle_token/__init__.py`.
- Add a 2.4.1 security section to `CHANGELOG.md` covering the X.509 DNS
  name-constraint verifier flaw and the vulnerable OpenSSL bundled in older
  upstream wheels.
- Leave `README.md` unchanged because installation and public usage do not
  change.

## Compatibility

The application does not use `cryptography.x509` certificate-chain
verification, so reachability of the DNS name-constraint flaw is not
established. The dependency must still be upgraded because it is distributed
to consumers and also resolves the bundled OpenSSL vulnerability.

`cryptography` 49.0.0 no longer publishes macOS x86-64 or 32-bit Windows
wheels. This upstream platform change will be called out in the changelog.

## Verification

- `poetry check --lock`
- Confirm declared, locked, and installed `cryptography` versions exclude
  releases below 49.0.0.
- Run all tests with SDKMAN Temurin 17 because the locked Spark 3.5.2 runtime
  is incompatible with the machine's default Java 25.
- `poetry run black --check .`
- `poetry build`
- `poetry run mkdocs build`
- Review `git diff --check` and the complete release diff.

## Delivery

Commit the release-preparation changes on `agent/release-2.4.1`, push the
branch, and open a draft pull request against `main`. Tagging, PyPI publishing,
documentation deployment, and publishing the GitHub release happen only after
the pull request is reviewed and merged.
