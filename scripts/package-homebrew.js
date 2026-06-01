#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const version = pkg.version;
const archiveName = `prompt-optimizer-lite-${version}.tar.gz`;
const archivePath = path.join(root, archiveName);

const files = [
  "package.json",
  "LICENSE",
  "README.md",
  "bin/promptopt",
  "bin/prompt-optimizer-mini",
  "bin/prompt-optimizer-lite",
  "scripts/fallback_optimize.py",
  "scripts/few_shot_templates.json",
  "scripts/local_model_manager.py",
];

for (const file of files) {
  if (!fs.existsSync(path.join(root, file))) {
    console.error(`Missing Homebrew package file: ${file}`);
    process.exit(1);
  }
}

if (fs.existsSync(archivePath)) {
  fs.unlinkSync(archivePath);
}

const result = spawnSync("tar", ["-czf", archiveName, ...files], {
  cwd: root,
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  throw result.error;
}

if (result.status !== 0) {
  process.exit(result.status || 1);
}

const size = fs.statSync(archivePath).size;
console.log(`Packaged ${archiveName} (${size} bytes)`);
