"""Tests for the language-aware import extractor (all 8 languages)."""
from __future__ import annotations

from pathlib import Path

import pytest

from arklint.parsers.imports import extract_imports


def _file(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ── Python ────────────────────────────────────────────────────────────────────

class TestPython:
    def test_simple_import(self, tmp_path):
        f = _file(tmp_path, "f.py", "import os\n")
        assert "os" in extract_imports(f)

    def test_from_import(self, tmp_path):
        f = _file(tmp_path, "f.py", "from sqlalchemy import Column\n")
        assert "sqlalchemy" in extract_imports(f)

    def test_dotted_from_import(self, tmp_path):
        f = _file(tmp_path, "f.py", "from sqlalchemy.orm import Session\n")
        assert "sqlalchemy.orm" in extract_imports(f)

    def test_multi_import(self, tmp_path):
        f = _file(tmp_path, "f.py", "import os, sys, json\n")
        result = extract_imports(f)
        assert "os" in result
        assert "sys" in result
        assert "json" in result

    def test_aliased_import(self, tmp_path):
        f = _file(tmp_path, "f.py", "import numpy as np\n")
        assert "numpy" in extract_imports(f)

    def test_deduplication(self, tmp_path):
        f = _file(tmp_path, "f.py", "import os\nimport os\n")
        assert extract_imports(f).count("os") == 1

    def test_no_imports(self, tmp_path):
        f = _file(tmp_path, "f.py", "x = 1\n")
        assert extract_imports(f) == []


# ── JavaScript / TypeScript ───────────────────────────────────────────────────

class TestJavaScript:
    def test_esm_import(self, tmp_path):
        f = _file(tmp_path, "f.js", "import React from 'react';\n")
        assert "react" in extract_imports(f)

    def test_esm_named_import(self, tmp_path):
        f = _file(tmp_path, "f.js", "import { useState } from 'react';\n")
        assert "react" in extract_imports(f)

    def test_require(self, tmp_path):
        f = _file(tmp_path, "f.js", "const express = require('express');\n")
        assert "express" in extract_imports(f)

    def test_dynamic_import(self, tmp_path):
        f = _file(tmp_path, "f.js", "const mod = import('lodash');\n")
        assert "lodash" in extract_imports(f)

    def test_typescript_file(self, tmp_path):
        f = _file(tmp_path, "f.ts", "import { Component } from '@angular/core';\n")
        assert "@angular/core" in extract_imports(f)

    def test_tsx_file(self, tmp_path):
        f = _file(tmp_path, "f.tsx", "import React from 'react';\n")
        assert "react" in extract_imports(f)

    def test_double_quotes(self, tmp_path):
        f = _file(tmp_path, "f.js", 'import axios from "axios";\n')
        assert "axios" in extract_imports(f)


# ── Go ────────────────────────────────────────────────────────────────────────

class TestGo:
    def test_single_import(self, tmp_path):
        f = _file(tmp_path, "f.go", 'import "fmt"\n')
        assert "fmt" in extract_imports(f)

    def test_block_import(self, tmp_path):
        f = _file(tmp_path, "f.go", 'import (\n\t"fmt"\n\t"os"\n)\n')
        result = extract_imports(f)
        assert "fmt" in result
        assert "os" in result

    def test_aliased_block_import(self, tmp_path):
        f = _file(tmp_path, "f.go", 'import (\n\t_ "github.com/lib/pq"\n)\n')
        assert "github.com/lib/pq" in extract_imports(f)

    def test_no_imports(self, tmp_path):
        f = _file(tmp_path, "f.go", "package main\nfunc main() {}\n")
        assert extract_imports(f) == []


# ── Ruby ──────────────────────────────────────────────────────────────────────

class TestRuby:
    def test_require(self, tmp_path):
        f = _file(tmp_path, "f.rb", "require 'rails'\n")
        assert "rails" in extract_imports(f)

    def test_require_double_quotes(self, tmp_path):
        f = _file(tmp_path, "f.rb", 'require "json"\n')
        assert "json" in extract_imports(f)

    def test_require_relative(self, tmp_path):
        f = _file(tmp_path, "f.rb", "require_relative 'models/user'\n")
        assert "models/user" in extract_imports(f)

    def test_no_imports(self, tmp_path):
        f = _file(tmp_path, "f.rb", "puts 'hello'\n")
        assert extract_imports(f) == []


# ── Rust ──────────────────────────────────────────────────────────────────────

class TestRust:
    def test_use_statement(self, tmp_path):
        f = _file(tmp_path, "f.rs", "use std::collections::HashMap;\n")
        assert "std" in extract_imports(f)

    def test_extern_crate(self, tmp_path):
        f = _file(tmp_path, "f.rs", "extern crate serde;\n")
        assert "serde" in extract_imports(f)

    def test_nested_use(self, tmp_path):
        f = _file(tmp_path, "f.rs", "use tokio::runtime::Runtime;\n")
        assert "tokio" in extract_imports(f)

    def test_no_imports(self, tmp_path):
        f = _file(tmp_path, "f.rs", "fn main() {}\n")
        assert extract_imports(f) == []


# ── Java ──────────────────────────────────────────────────────────────────────

class TestJava:
    def test_simple_import(self, tmp_path):
        f = _file(tmp_path, "f.java", "import java.util.List;\n")
        assert "java.util.List" in extract_imports(f)

    def test_static_import(self, tmp_path):
        f = _file(tmp_path, "f.java", "import static org.junit.Assert.assertEquals;\n")
        assert "org.junit.Assert.assertEquals" in extract_imports(f)

    def test_wildcard_import(self, tmp_path):
        f = _file(tmp_path, "f.java", "import java.util.*;\n")
        assert "java.util.*" in extract_imports(f)

    def test_no_imports(self, tmp_path):
        f = _file(tmp_path, "f.java", "public class Foo {}\n")
        assert extract_imports(f) == []


# ── C# ────────────────────────────────────────────────────────────────────────

class TestCSharp:
    def test_using_statement(self, tmp_path):
        f = _file(tmp_path, "f.cs", "using System.Linq;\n")
        assert "System.Linq" in extract_imports(f)

    def test_multiple_usings(self, tmp_path):
        f = _file(tmp_path, "f.cs", "using System;\nusing System.IO;\n")
        result = extract_imports(f)
        assert "System" in result
        assert "System.IO" in result

    def test_no_imports(self, tmp_path):
        f = _file(tmp_path, "f.cs", "namespace Foo { }\n")
        assert extract_imports(f) == []


# ── PHP ───────────────────────────────────────────────────────────────────────

class TestPHP:
    def test_use_statement(self, tmp_path):
        f = _file(tmp_path, "f.php", "use Illuminate\\Support\\Facades\\DB;\n")
        assert "Illuminate\\Support\\Facades\\DB" in extract_imports(f)

    def test_require(self, tmp_path):
        f = _file(tmp_path, "f.php", "require 'config.php';\n")
        assert "config.php" in extract_imports(f)

    def test_require_once(self, tmp_path):
        f = _file(tmp_path, "f.php", "require_once 'init.php';\n")
        assert "init.php" in extract_imports(f)


# ── Unknown extension ─────────────────────────────────────────────────────────

class TestUnknownExtension:
    def test_unknown_extension_returns_empty(self, tmp_path):
        f = _file(tmp_path, "f.xyz", "import something\n")
        assert extract_imports(f) == []

    def test_unreadable_file_returns_empty(self, tmp_path):
        f = tmp_path / "f.py"
        # Don't write it — file doesn't exist
        assert extract_imports(f) == []
