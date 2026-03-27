#!/usr/bin/env node
"use strict";

/**
 * Postinstall script — downloads the arklint binary at install time
 * so the package directory is already owned by npm when writing.
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

const BINARY_VERSION = require("./package.json").binaryVersion;

const PLATFORM_MAP = {
  "linux-x64":    "arklint-linux-x86_64",
  "darwin-arm64": "arklint-darwin-arm64",
  "win32-x64":    "arklint-windows-x86_64.exe",
};

function getBinaryName() {
  const key = `${process.platform}-${process.arch}`;
  const name = PLATFORM_MAP[key];
  if (!name) {
    process.stderr.write(
      `arklint: no prebuilt binary for ${key} — install via pip instead.\n`
    );
    process.exit(0); // non-fatal: pip users don't need the binary
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
        if (fs.existsSync(dest)) fs.unlinkSync(dest);
        reject(err);
      });
    }

    get(url);
  });
}

async function main() {
  const binaryPath = getLocalBinaryPath();
  const binaryName = getBinaryName();
  const url = `https://github.com/Kaushik13k/arklint/releases/download/v${BINARY_VERSION}/${binaryName}`;

  process.stdout.write(`Downloading arklint v${BINARY_VERSION} for ${process.platform}-${process.arch}...\n`);

  fs.mkdirSync(path.join(__dirname, "bin"), { recursive: true });
  await download(url, binaryPath);

  if (process.platform !== "win32") {
    fs.chmodSync(binaryPath, 0o755);
  }

  process.stdout.write(`Done.\n`);
}

main().catch((err) => {
  // Non-fatal — user can still run arklint and it will re-attempt download
  process.stderr.write(`arklint postinstall warning: ${err.message}\n`);
  process.exit(0);
});
