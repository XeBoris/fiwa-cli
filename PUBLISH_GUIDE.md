# PyPI Publishing Workflow Guide

## Overview

The `publish-pypi.yml` workflow automatically builds and publishes the FiWa CLI package to PyPI when you push to the `prod-local-only` branch.

## Trigger

**Branch**: `prod-local-only` (exclusive)

```yaml
on:
  push:
    branches: [ "prod-local-only" ]
  workflow_dispatch:  # Also allows manual triggering
```

This workflow ONLY runs when:
- You push to the `prod-local-only` branch
- You manually trigger it from GitHub Actions UI

## Workflow Steps

### 1. Build Package
- Cleans previous builds
- Builds wheel and source distribution
- Validates package with `twine check`

### 2. Test PyPI Upload (Optional)
- Publishes to Test PyPI first (if token configured)
- Allows testing installation before production publish
- Skipped if `TEST_PYPI_API_TOKEN` not set

### 3. PyPI Publication
- Publishes package to production PyPI
- Requires `PYPI_API_TOKEN` secret
- Fails if token not configured

### 4. GitHub Release
- Creates GitHub release with version tag
- Attaches built packages (wheel + source)
- Generates release notes

## Setup Required

### 1. Create PyPI API Token

#### For Production PyPI:
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: "fiwa-cli-github-actions"
4. Scope: "Entire account" or specific to "fiwa-cli" project
5. Copy the token (starts with `pypi-`)

#### For Test PyPI (Optional):
1. Go to https://test.pypi.org/manage/account/token/
2. Create token similar to above
3. Scope: "Entire account"

### 2. Add Secrets to GitHub Repository

1. Go to repository **Settings**
2. Navigate to **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

   **Secret 1: PYPI_API_TOKEN** (Required)
   - Name: `PYPI_API_TOKEN`
   - Value: `pypi-...` (your production PyPI token)

   **Secret 2: TEST_PYPI_API_TOKEN** (Optional)
   - Name: `TEST_PYPI_API_TOKEN`
   - Value: `pypi-...` (your Test PyPI token)

### 3. Verify Package Configuration

Ensure `pyproject.toml` has correct metadata:

```toml
[project]
name = "fiwa-cli"
version = "0.2.0"  # Update this before publishing
description = "Financial Workflow Application CLI"
readme = "README.md"
license = "MIT"
authors = [
    {name = "Boris Bauermeister", email = "Boris.Bauermeister@gmail.com"}
]

[project.urls]
Homepage = "https://github.com/Boris-Bauermeister/fiwa-cli"
Repository = "https://github.com/Boris-Bauermeister/fiwa-cli"
```

## Publishing Process

### Step 1: Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.3.0"  # Increment version
```

Commit:
```bash
git add pyproject.toml
git commit -m "Bump version to 0.3.0"
```

### Step 2: Create and Push to prod-local-only Branch

```bash
# Create branch from main
git checkout main
git pull origin main

# Create prod-local-only branch
git checkout -b prod-local-only

# Or update existing branch
git checkout prod-local-only
git merge main

# Push to trigger workflow
git push origin prod-local-only
```

### Step 3: Monitor Workflow

1. Go to **Actions** tab on GitHub
2. Click on **Publish to PyPI** workflow run
3. Watch progress:
   - ✓ Build package
   - ✓ Check with twine
   - ✓ Publish to Test PyPI (if configured)
   - ✓ Publish to PyPI
   - ✓ Create GitHub release

### Step 4: Verify Publication

```bash
# Check on PyPI
https://pypi.org/project/fiwa-cli/

# Test installation
pip install fiwa-cli==0.3.0

# Verify it works
fiwa --version
# Output: FiWa CLI version 0.3.0
```

### Step 5: Merge Back to Main (Optional)

```bash
git checkout main
git merge prod-local-only
git push origin main
```

## Manual Triggering

You can also manually trigger the workflow:

1. Go to **Actions** tab
2. Click **Publish to PyPI**
3. Click **Run workflow** button
4. Select branch: `prod-local-only`
5. Click **Run workflow**

## What Gets Published

```
dist/
├── fiwa_cli-0.2.0-py3-none-any.whl    # Wheel package
└── fiwa_cli-0.2.0.tar.gz              # Source distribution
```

Both files are:
- Published to PyPI
- Attached to GitHub release
- Available for download

## Version Management

The workflow automatically:
- Reads version from `pyproject.toml`
- Uses it for PyPI package
- Creates GitHub release tag (e.g., `v0.2.0`)
- No manual version editing needed in workflow

To publish new version:
1. Update version in `pyproject.toml` only
2. Push to `prod-local-only`
3. Workflow handles the rest

## Workflow Outputs

### On Success:
```
✓ Package built successfully!
✓ Package check passed
✓ Published to Test PyPI (if configured)
✓ Package published to PyPI successfully!
  Package: fiwa-cli
  Version: 0.2.0
  Install with: pip install fiwa-cli

✓ GitHub release created: v0.2.0
```

### On Failure (Missing Token):
```
❌ PYPI_API_TOKEN not set!
   Cannot publish to PyPI without token.

To publish to PyPI:
  1. Create API token at https://pypi.org/manage/account/token/
  2. Add as repository secret: PYPI_API_TOKEN
  3. Re-run this workflow
```

## Troubleshooting

### Build Fails

**Check**:
- `pyproject.toml` is valid
- All required files are included
- No syntax errors in source code

**Test locally**:
```bash
make clean
make build
twine check dist/*
```

### PyPI Upload Fails

**Possible causes**:
1. Version already exists on PyPI (can't overwrite)
   - **Solution**: Increment version in pyproject.toml

2. Invalid API token
   - **Solution**: Regenerate token and update secret

3. Package name already taken
   - **Solution**: Change name in pyproject.toml

### Test PyPI Skipped

If you see "TEST_PYPI_API_TOKEN not set - skipping":
- This is **optional** - workflow continues
- Add token if you want to test on Test PyPI first
- Not required for production publishing

### GitHub Release Fails

**Check**:
- Tag `v0.2.0` doesn't already exist
- `GITHUB_TOKEN` has write permissions (automatic)

**Solution**:
- Delete existing tag/release if updating
- Or increment version number

## Best Practices

### Before Publishing:

```bash
# 1. Update version
# Edit pyproject.toml: version = "0.3.0"

# 2. Update CHANGELOG
# Document changes in CHANGELOG.md

# 3. Test locally
make clean
make build
make test
make docs-build

# 4. Test installation from local build
pip install dist/fiwa_cli-0.3.0-py3-none-any.whl
fiwa --version

# 5. Push to prod-local-only
git checkout -b prod-local-only
git add .
git commit -m "Release v0.3.0"
git push origin prod-local-only

# 6. Monitor workflow in Actions tab

# 7. Verify on PyPI
# Visit: https://pypi.org/project/fiwa-cli/

# 8. Test from PyPI
pip install fiwa-cli==0.3.0
```

### Versioning Strategy:

Follow Semantic Versioning (SemVer):
- **Major** (1.0.0): Breaking changes
- **Minor** (0.3.0): New features, backwards compatible
- **Patch** (0.2.1): Bug fixes

Example progression:
```
0.1.0 → Initial release
0.2.0 → Added reports feature
0.2.1 → Fixed bug in reports
0.3.0 → Added settings screen
1.0.0 → Stable release, breaking API changes
```

## Security

### API Token Security:
- ✅ Tokens stored as GitHub secrets (encrypted)
- ✅ Not visible in workflow logs
- ✅ Limited scope (package-specific recommended)
- ✅ Can be revoked anytime

### What NOT to Do:
- ❌ Don't commit tokens to repository
- ❌ Don't share tokens publicly
- ❌ Don't use account-wide tokens if possible
- ❌ Don't reuse tokens across projects

## Alternative: Manual Publishing

If you prefer manual control:

```bash
# Build package
make build

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Summary

✅ **Workflow**: `publish-pypi.yml` created  
✅ **Trigger**: Only on `prod-local-only` branch  
✅ **Auto-version**: Reads from pyproject.toml  
✅ **Test PyPI**: Optional dry run  
✅ **Production PyPI**: Automatic publish  
✅ **GitHub Release**: Automatic with artifacts  
✅ **Security**: Token-based authentication  

**Setup secrets and push to `prod-local-only` to publish!**
