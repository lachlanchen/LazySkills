---
name: npm-publishing
description: Use when preparing, packaging, testing, publishing, or troubleshooting npm packages, including scoped packages, CLI bins, npm 2FA/web login, env-file tokens, GitHub Actions trusted publishing, provenance, and post-publish install verification.
---

# npm Publishing

## Core Rule

Never expose credentials. Do not print, paste, commit, or log npm tokens, `.npmrc`, `.env`, OTPs, cookies, recovery codes, or full auth URLs after they are consumed. Prefer verified commands and registry checks over assumptions.

Use this skill when the user asks to make a repo installable through npm, publish a package, fix npm auth, add trusted publishing, or verify npm installation.

## Package Readiness

Inspect the repo before editing:

```bash
git status -sb
cat package.json
ls -la
```

For a CLI package, ensure `package.json` has the expected basics:

```json
{
  "name": "@scope/package-name",
  "version": "0.1.0",
  "bin": {
    "command-name": "bin/command-name.js"
  },
  "files": [
    "bin/",
    "src/",
    "README.md",
    "package.json"
  ],
  "scripts": {
    "test": "npm run check",
    "pack:dry-run": "npm pack --dry-run"
  }
}
```

Prefer a narrow `files` allowlist over a broad `.npmignore`. If using `.npmignore`, explicitly exclude generated output, caches, logs, local archives, `.env`, `.npmrc`, and secrets.

## Pre-Publish Checks

Run checks before every publish:

```bash
npm test
npm run pack:dry-run
npm pack --json
```

Inspect the dry-run tarball output. Block publish if it includes any of:

- `.env`, `.npmrc`, tokens, cookies, keys, OTPs, debug logs;
- generated caches such as `__pycache__`, `.pytest_cache`, `.DS_Store`;
- large private artifacts that do not belong in the package;
- files unrelated to the install surface.

If `npm pack` creates a local `.tgz`, delete it after inspection or confirm it is ignored before committing.

Check registry state:

```bash
npm view @scope/package-name version --json
npm whoami
```

`E404` from `npm view` means the package is not yet published. A published package needs a new version before another publish.

## Authentication

First test the current session:

```bash
npm whoami
```

If unauthenticated, use web login:

```bash
npm login --auth-type=web
```

If npm prints a browser URL and waits, tell the user to complete login or 2FA on a trusted device, then keep the CLI session alive. For publish-time approval, press Enter when npm asks to open the browser and wait for completion. If the auth URL expires, rerun the publish command to generate a fresh URL.

For token-based publishing, read tokens from an uncommitted env file without printing values:

```bash
NPM_TOKEN=...
NODE_AUTH_TOKEN=...
NPM_CONFIG_REGISTRY=https://registry.npmjs.org
```

Use a temporary npm config for token commands and delete it afterward:

```bash
TMP_NPMRC="$(mktemp)"
printf '//registry.npmjs.org/:_authToken=%s\n' "$NPM_TOKEN" > "$TMP_NPMRC"
NPM_CONFIG_USERCONFIG="$TMP_NPMRC" npm whoami
rm -f "$TMP_NPMRC"
```

If `whoami` returns `E401`, the token is invalid, expired, scoped incorrectly, or lacks registry access. Do not publish until auth succeeds.

## Publish Workflow

For public scoped packages:

```bash
npm publish --access public
```

For provenance-capable CI releases:

```bash
npm publish --access public --provenance
```

If npm requires publish authentication, share only the current approval URL with the user and wait. After success, verify the registry:

```bash
npm view @scope/package-name version dist.tarball --json
```

Then verify a real global install in a temporary prefix:

```bash
TMP_PREFIX="$(mktemp -d)"
npm install --prefix "$TMP_PREFIX" -g @scope/package-name
"$TMP_PREFIX/bin/command-name" --version
rm -rf "$TMP_PREFIX"
```

Report the package name, version, npm URL, install command, validation commands, and any remaining publishing setup.

## GitHub Actions Trusted Publishing

After the first package version exists, configure tokenless future releases with npm trusted publishing.

Workflow requirements:

```yaml
permissions:
  contents: read
  id-token: write
```

Publish job outline:

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-node@v4
  with:
    node-version: "22"
    registry-url: https://registry.npmjs.org
- run: npm install -g npm@^11.10.0
- run: npm test
- run: npm pack --dry-run
- run: npm publish --access public --provenance
```

Trusted publisher setup:

```bash
npm install -g npm@^11.10.0
npm trust github @scope/package-name --repo owner/repo --file npm-publish.yml
```

The npm CLI may require account-level 2FA and package write access. If it returns `E400` after saying 2FA is required without opening a browser flow, configure the trusted publisher from the npm package settings page with the same package, repository, and workflow filename.

## Common Failures

- `E401 Unauthorized`: login expired or token invalid; rerun `npm whoami` and refresh auth.
- `E403 Forbidden`: account lacks package/scope rights, package name is protected, or version already exists.
- `E404 Not Found` from `npm view`: package has not been published yet.
- `EPUBLISHCONFLICT`: version already exists; bump `version` and retry after checks.
- Expired 2FA web approval: rerun `npm publish` to get a fresh URL.
- Trusted publishing fails before first publish: npm requires the package to exist first.

## Completion Check

Before final response:

- working tree is clean or all edits are explained;
- package checks passed;
- registry shows the expected version;
- temp-prefix install works;
- docs and CI changes are committed and pushed if the user requested repository updates;
- no credentials or one-time auth material were committed or echoed.
