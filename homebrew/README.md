# Homebrew Tap

This folder contains the formula for publishing Prompt Optimizer Lite through a custom Homebrew tap.

## Release Flow

1. Build the VSIX:

```bash
npm run package
```

2. Create a GitHub release named `v1.0.0` and upload:

```text
prompt-optimizer-mini-1.0.0.vsix
```

3. Verify the final VSIX SHA matches the formula:

```bash
shasum -a 256 prompt-optimizer-mini-1.0.0.vsix
```

Expected SHA for the current package:

```text
a09ae551fa0849f9d829b9d84b52317ef391b91435e7b4dc74e808dbc47fdfaf
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

The CLI exposes `promptopt`, `prompt-optimizer-mini`, and `prompt-optimizer-lite`. Interactive commands show an ASCII startup animation and can also run local status and prompt rendering checks.
