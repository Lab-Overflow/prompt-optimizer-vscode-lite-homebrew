class PromptOptimizerLite < Formula
  desc "Lightweight prompt optimizer CLI"
  homepage "https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew"
  url "https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew/releases/download/v1.0.0/prompt-optimizer-lite-1.0.0.tar.gz"
  sha256 "68bef1b72b6c22f16bf3fdb6bd2c6db77a8ace4d949fef39fc8fdcc0c28b2917"
  license "Apache-2.0"

  uses_from_macos "python"

  def install
    libexec.install "package.json"
    libexec.install "scripts"
    libexec.install "bin"

    bin.env_script_all_files libexec/"bin",
      PROMPT_OPTIMIZER_LITE_INSTALL_ROOT: libexec,
      PROMPT_OPTIMIZER_LITE_VERSION: version,
      PYTHON: "python3"
  end

  def caveats
    <<~EOS
      This formula installs the lightweight PromptOpt CLI only.

      Optional VS Code extension install:
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
