class PromptOptimizerLite < Formula
  desc "Lightweight prompt optimizer CLI and VS Code extension installer"
  homepage "https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew"
  url "https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew/releases/download/v1.0.0/prompt-optimizer-mini-1.0.0.vsix"
  sha256 "a09ae551fa0849f9d829b9d84b52317ef391b91435e7b4dc74e808dbc47fdfaf"
  license "Apache-2.0"

  depends_on "python@3.12"

  def install
    libexec.install cached_download => "prompt-optimizer-mini-#{version}.vsix"
    libexec.install "extension/package.json"
    libexec.install "extension/scripts" => "scripts"
    libexec.install "extension/bin" => "bin"

    bin.env_script_all_files libexec/"bin",
      PROMPT_OPTIMIZER_LITE_INSTALL_ROOT: libexec,
      PROMPT_OPTIMIZER_LITE_VERSION: version,
      PROMPT_OPTIMIZER_LITE_VSIX: libexec/"prompt-optimizer-mini-#{version}.vsix",
      PYTHON: Formula["python@3.12"].opt_bin/"python3"
  end

  def caveats
    <<~EOS
      Install the VS Code extension after installing the CLI:
        prompt-optimizer-lite install-extension

      Useful commands:
        prompt-optimizer-lite doctor
        prompt-optimizer-lite status
        prompt-optimizer-lite render-prompt "请作为红队审查这个产品发布计划"
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/prompt-optimizer-mini version")
    assert_match "PromptOpt", shell_output("#{bin}/prompt-optimizer-mini --no-animation")
  end
end
