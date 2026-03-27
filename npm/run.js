#!/usr/bin/env node
"use strict";

const https = require("https");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const VERSION = require("./package.json").version;
const BINARY_VERSION = require("./package.json").binaryVersion || VERSION;

const PLATFORM_MAP = {
  "linux-x64":    "arklint-linux-x86_64",
  "darwin-arm64": "arklint-darwin-arm64",
  "win32-x64":    "arklint-windows-x86_64.exe",
};

function getBinaryName() {
  const key = `${process.platform}-${process.arch}`;
  const name = PLATFORM_MAP[key];
  if (!name) {
    throw new Error(
      `arklint does not have a prebuilt binary for ${key}.\n` +
      `Please install via pip: pip install arklint`
    );
  }
  return name;
}

function getLocalBinaryPath() {
  const ext = process.platform === "win32" ? ".exe" : "";
  return path.join(__dirname, "bin", `arklint${ext}`);
}

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);

    function get(url) {
      https.get(url, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          get(res.headers.location);
          return;
        }
        if (res.statusCode !== 200) {
          file.close();
          fs.unlinkSync(dest);
          reject(new Error(`Download failed with status ${res.statusCode}`));
          return;
        }
        res.pipe(file);
        file.on("finish", () => file.close(resolve));
      }).on("error", (err) => {
        file.close();
        fs.unlinkSync(dest);
        reject(err);
      });
    }

    get(url);
  });
}

function isBinaryStale(binaryPath) {
  if (!fs.existsSync(binaryPath)) return true;
  try {
    const result = spawnSync(binaryPath, ["--version"], { encoding: "utf8" });
    const output = (result.stdout || result.stderr || "").trim();
    return !output.includes(BINARY_VERSION);
  } catch {
    return true;
  }
}

async function main() {
  const binaryPath = getLocalBinaryPath();

  if (isBinaryStale(binaryPath)) {
    if (fs.existsSync(binaryPath)) fs.unlinkSync(binaryPath);
    const binaryName = getBinaryName();
    const url = `https://github.com/Kaushik13k/arklint/releases/download/v${BINARY_VERSION}/${binaryName}`;

    process.stderr.write(`Downloading arklint v${BINARY_VERSION} for ${process.platform}-${process.arch}...\n`);

    fs.mkdirSync(path.join(__dirname, "bin"), { recursive: true });
    await download(url, binaryPath);

    if (process.platform !== "win32") {
      fs.chmodSync(binaryPath, 0o755);
    }

    process.stderr.write(`Done.\n`);
  }

  const result = spawnSync(binaryPath, process.argv.slice(2), { stdio: "inherit" });
  process.exit(result.status ?? 1);
}

main().catch((err) => {
  process.stderr.write(`arklint error: ${err.message}\n`);
  process.exit(1);
});
