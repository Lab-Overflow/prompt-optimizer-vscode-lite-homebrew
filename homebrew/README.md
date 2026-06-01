# Homebrew Tap

This folder contains the formula for publishing Prompt Optimizer Lite through a custom Homebrew tap.

## Release Flow

1. Build the Homebrew release tarball:

```bash
npm run package:homebrew
```

2. Create a GitHub release named `v1.0.1` and upload:

```text
prompt-optimizer-lite-1.0.1.tar.gz
```

3. Verify the final tarball SHA matches the formula:

```bash
shasum -a 256 prompt-optimizer-lite-1.0.1.tar.gz
```

Expected SHA for the current package:

```text
31b2b9c807bb11bcc7e7caaacc7df597c77a86a680c8c5e6a93bcf944c3509bc
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
