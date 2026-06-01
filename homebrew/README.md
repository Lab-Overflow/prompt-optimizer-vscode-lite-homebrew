# Homebrew Tap

This folder contains the formula for publishing Prompt Optimizer Lite through a custom Homebrew tap.

## Release Flow

1. Build the Homebrew release tarball:

```bash
npm run package:homebrew
```

2. Create a GitHub release named `v1.0.0` and upload:

```text
prompt-optimizer-lite-1.0.0.tar.gz
```

3. Verify the final tarball SHA matches the formula:

```bash
shasum -a 256 prompt-optimizer-lite-1.0.0.tar.gz
```

Expected SHA for the current package:

```text
68bef1b72b6c22f16bf3fdb6bd2c6db77a8ace4d949fef39fc8fdcc0c28b2917
```

4. Copy the formula into your tap repository:

```text
homebrew-prompt-optimizer/Formula/prompt-optimizer-lite.rb
```

Users can then install with:

```bash
brew tap Lab-Overflow/prompt-optimizer
brew install prompt-optimizer-lite
promptopt install-extension
promptopt doctor
```

The CLI exposes `promptopt`, `prompt-optimizer-mini`, and `prompt-optimizer-lite`. The Homebrew artifact contains only the CLI scripts, Python fallback, and templates; it does not ship the VSIX, Node dependencies, build output, icon assets, or model weights.
