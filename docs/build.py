#!/usr/bin/env python3
"""Build the Arklint docs site.

Reads Markdown files from content/, converts them to styled HTML matching
the Arklint design system, and injects them into template.html to produce
site/index.html.

Usage:
    pip install markdown pymdown-extensions
    python build.py
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown


ROOT = Path(__file__).parent
CONTENT_DIR = ROOT / "content"
TEMPLATE = ROOT / "template.html"
OUTPUT_DIR = ROOT / "site"


def md_to_html(text: str) -> str:
    md = markdown.Markdown(extensions=["fenced_code", "tables", "smarty"])
    return md.convert(text)


def style_code_blocks(html_str: str) -> str:
    def _replace(match):
        block = match.group(0)
        lang_m = re.search(r'class="language-(\w+)"', block)
        lang = lang_m.group(1) if lang_m else ""
        code_m = re.search(r'<code[^>]*>(.*?)</code>', block, re.DOTALL)
        if not code_m:
            return block
        raw = code_m.group(1)

        label_map = {"bash": "Terminal",
                     "yaml": ".arklint.yml", "json": "Config"}
        label = label_map.get(lang, "Code")

        if lang == "yaml":
            # Strings first - before key regex adds class="k" HTML attributes
            # (otherwise the string regex would match the "k" in class="k")
            raw = re.sub(r'(&quot;[^&]*?&quot;)',
                         r'<span class="s">\1</span>', raw)
            raw = re.sub(r"('(?:[^'\\\\]|\\\\.)*')",
                         r'<span class="s">\1</span>', raw)
            raw = re.sub(
                r'^(\s*)([\w-]+)(:)', r'\1<span class="k">\2\3</span>', raw, flags=re.MULTILINE)
            raw = re.sub(r'(#.*)$', r'<span class="c">\1</span>',
                         raw, flags=re.MULTILINE)

        if lang == "bash":
            lines = raw.split("\n")
            out = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("$ "):
                    cmd = stripped[2:]
                    out.append(
                        f'<span class="p">$ </span><span class="cmd">{cmd}</span>')
                elif stripped.startswith("#"):
                    out.append(f'<span class="c">{line}</span>')
                elif stripped == "":
                    out.append("")
                elif stripped.startswith("✗"):
                    out.append(f'<span class="fail">{line}</span>')
                elif stripped.startswith("⚠"):
                    out.append(f'<span class="warn">{line}</span>')
                elif stripped.startswith("✓"):
                    out.append(f'<span class="pass">{line}</span>')
                else:
                    out.append(f'<span class="dim">{line}</span>')
            raw = "\n".join(out)

        if lang == "json":
            raw = re.sub(r'(&quot;[^&]*?&quot;|"[^"]*?")\s*:',
                         r'<span class="k">\1</span>:', raw)
            raw = re.sub(r':\s*(&quot;[^&]*?&quot;|"[^"]*?")',
                         r': <span class="s">\1</span>', raw)

        return (
            f'<div class="cb"><div class="cb-h">'
            f'<span class="l">{label}</span><span class="r">{lang}</span>'
            f'</div><pre>{raw}</pre></div>'
        )

    return re.sub(r'<pre><code[^>]*>.*?</code></pre>', _replace, html_str, flags=re.DOTALL)


def style_tables(html_str: str) -> str:
    return html_str.replace("<table>", '<table class="ct">')


def style_inline_code(html_str: str) -> str:
    def _repl(m):
        return f'<code class="i">{m.group(1)}</code>'
    return re.sub(r'(?<!<pre>)<code>([^<]+)</code>', _repl, html_str)


def style_blockquotes_as_tips(html_str: str) -> str:
    tip_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>'
    return re.sub(
        r'<blockquote>\s*<p>(.*?)</p>\s*</blockquote>',
        rf'<div class="tip">{tip_svg}<span class="tip-body">\1</span></div>',
        html_str, flags=re.DOTALL,
    )


def convert_section(md_text: str, section_id: str) -> str:
    lines = md_text.strip().split("\n")
    title = ""
    lead = ""
    body_start = 0

    for i, line in enumerate(lines):
        if not title and line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            body_start = i + 1
            continue
        if title and not lead and line.strip() and not line.startswith("#") and not line.startswith("```") and not line.startswith("|") and not line.startswith("-") and not line.startswith(">"):
            lead = line.strip()
            body_start = i + 1
            break
        if title and (line.startswith("#") or line.startswith("```") or line.startswith("|") or line.startswith("-") or line.startswith(">")):
            body_start = i
            break

    body_md = "\n".join(lines[body_start:])
    # Downgrade ## → ### so section title stays h2, sub-sections become h3
    body_md = re.sub(r'^## ', '### ', body_md, flags=re.MULTILINE)

    body_html = md_to_html(body_md)
    body_html = style_code_blocks(body_html)
    body_html = style_tables(body_html)
    body_html = style_inline_code(body_html)
    body_html = style_blockquotes_as_tips(body_html)

    # Convert markdown formatting in lead
    lead = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', lead)
    lead = re.sub(r'\*(.+?)\*', r'<em>\1</em>', lead)

    title_html = f'  <h2>{title} <a href="#{section_id}" class="anchor">#</a></h2>'
    lead_html = f'  <p class="lead">{lead}</p>' if lead else ""

    return f'<section class="ds" id="{section_id}">\n{title_html}\n{lead_html}\n{body_html}\n</section>'


def convert_rules_section(md_text: str) -> str:
    lines = md_text.strip().split("\n")
    title = ""
    lead = ""
    body_start = 0

    for i, line in enumerate(lines):
        if not title and line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            body_start = i + 1
            continue
        if title and not lead and line.strip() and not line.startswith("#"):
            lead = line.strip()
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:])

    # Split by ## headings
    rule_sections = re.split(r'^## ', body, flags=re.MULTILINE)
    rule_sections = [s for s in rule_sections if s.strip()]

    cards_html = []
    for section in rule_sections:
        section_lines = section.strip().split("\n")
        heading = section_lines[0].strip()

        # Parse "type - Description"
        parts = heading.split(' - ', maxsplit=1)
        rule_type = parts[0].strip()
        rule_name = parts[1].strip() if len(parts) > 1 else rule_type

        type_to_id = {
            "boundary": "rule-boundary",
            "dependency": "rule-dependency",
            "file-pattern": "rule-file-pattern",
            "pattern-ban": "rule-pattern-ban",
            "layer-boundary": "rule-layer-boundary",
        }
        card_id = type_to_id.get(rule_type, f"rule-{rule_type}")

        rest_md = "\n".join(section_lines[1:]).strip()

        # Split description and code
        in_code = False
        desc_lines = []
        code_lines = []
        for line in rest_md.split("\n"):
            if line.startswith("```"):
                in_code = not in_code
                code_lines.append(line)
                continue
            if in_code:
                code_lines.append(line)
            else:
                desc_lines.append(line)

        desc = "\n".join(desc_lines).strip()
        code_md = "\n".join(code_lines).strip()

        desc_html = md_to_html(desc) if desc else ""
        desc_html = style_tables(desc_html)
        desc_text = re.sub(r'</?p>', '', desc_html).strip()

        code_html = md_to_html(code_md) if code_md else ""
        code_html = style_code_blocks(code_html)

        body_section = f'<div class="rc-body">{desc_html}</div>' if desc_html else ""
        card = (
            f'    <div class="rc" id="{card_id}">'
            f'<div class="rc-head"><span class="rb">{rule_type}</span>'
            f'<div class="ri"><h4>{rule_name}</h4></div></div>'
            f'{body_section}'
            f'{code_html}</div>'
        )
        cards_html.append(card)

    all_cards = "\n".join(cards_html)
    return (
        f'<section class="ds" id="rules">\n'
        f'  <h2>{title} <a href="#rules" class="anchor">#</a></h2>\n'
        f'  <p class="lead">{lead}</p>\n'
        f'  <div class="rc-list">\n{all_cards}\n  </div>\n'
        f'</section>'
    )


SECTIONS = [
    ("overview.md", "overview-section", False),
    ("installation.md", "installation", False),
    ("quickstart.md", "quickstart", False),
    ("rules.md", "rules", True),
    ("packs.md", "packs", False),
    ("cli.md", "cli", False),
    ("watch.md", "watch", False),
    ("diff.md", "diff", False),
    ("visualize.md", "visualize", False),
    ("mcp.md", "mcp", False),
    ("export.md", "export", False),
    ("learn.md", "learn", False),
    ("ci.md", "ci", False),
    ("github-action.md", "action", False),
    ("languages.md", "languages", False),
    ("contributing.md", "contributing", False),
]


def build() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    template = TEMPLATE.read_text()

    sections_html = []
    for filename, section_id, is_rules in SECTIONS:
        md_path = CONTENT_DIR / filename
        if not md_path.exists():
            print(f"  ⚠ Skipping {filename} (not found)")
            continue
        md_text = md_path.read_text()
        if is_rules:
            section_html = convert_rules_section(md_text)
        else:
            section_html = convert_section(md_text, section_id)
        sections_html.append(section_html)
        print(f"  ✓ {filename} → #{section_id}")

    all_sections = "\n\n".join(sections_html)
    output_html = template.replace("<!-- CONTENT_SECTIONS -->", all_sections)

    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(output_html)
    print(f"\n✓ Built site/index.html ({len(output_html):,} bytes)")


if __name__ == "__main__":
    print("Building Arklint docs...\n")
    build()
