#!/usr/bin/env python3
"""Content Toolkit MCP Server — 11 text processing tools for AI agents.

Zero API keys. Pure Python stdlib + markdown. Freemium: 50 free calls, $19/mo unlimited.

Built for AgentPay Labs — the Swiss Army knife for text/data operations.
"""

import sys
import json
import re
import difflib
import urllib.parse
from collections import Counter

# ── Rate limiting ───────────────────────────────────────────────────────────
FREE_LIMIT = 50
PRO_KEYS = {"PROL_AGENTPAY_DEMO": "demo"}
STRIPE_LINK = "https://buy.stripe.com/14kg3reZT1Fv9H2288"

PRO_KEY = None
for i, arg in enumerate(sys.argv):
    if arg == "--pro-key" and i + 1 < len(sys.argv):
        PRO_KEY = sys.argv[i + 1]
IS_PRO = PRO_KEY in PRO_KEYS
call_counter = 0


def check_rate_limit():
    if IS_PRO:
        return None
    global call_counter
    call_counter += 1
    if call_counter > FREE_LIMIT:
        return {
            "error": f"Free tier limit ({FREE_LIMIT} calls). Upgrade to Pro ($19/mo unlimited).",
            "isError": True,
            "next_steps": [
                f"Buy Pro: {STRIPE_LINK}",
                "Restart server to reset counter",
                "Use --pro-key PROL_AGENTPAY_DEMO for testing",
            ],
            "calls_used": call_counter,
            "limit": FREE_LIMIT,
        }
    return None


# ── MCP Server ──────────────────────────────────────────────────────────────
# Direct MCP stdio (no FastMCP dependency for simplicity/portability)
import asyncio

CHARACTER_LIMIT = 25000


def truncate_response(text, limit=CHARACTER_LIMIT):
    if len(text) <= limit:
        return text, False
    half = limit // 2
    return text[:half] + f"\n\n... [truncated {len(text) - limit} characters. Use filters or pagination.] ...\n\n" + text[-half:], True


# ── Tool implementations ────────────────────────────────────────────────────


def toolkit_diff(params):
    """Compare two texts and return unified diff."""
    text1 = params.get("text1", "")
    text2 = params.get("text2", "")
    context_lines = int(params.get("context", 3))
    output_format = params.get("format", "unified")  # unified, inline, or side_by_side

    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    if not text1 and not text2:
        return {"status": "error", "isError": True, "next_steps": ["Provide at least one text string to compare."]}

    if output_format == "unified":
        diff = list(difflib.unified_diff(
            [l.rstrip("\n") for l in lines1],
            [l.rstrip("\n") for l in lines2],
            fromfile="original",
            tofile="modified",
            n=context_lines,
        ))
        diff_text = "\n".join(diff)
    elif output_format == "inline":
        diff_lines = []
        for line in difflib.Differ().compare(
            [l.rstrip("\n") for l in lines1],
            [l.rstrip("\n") for l in lines2],
        ):
            diff_lines.append(line)
        diff_text = "\n".join(diff_lines)
    else:
        # side_by_side: compute opcodes for stats
        sm = difflib.SequenceMatcher(None, text1, text2)
        stats = {
            "similarity_ratio": round(sm.ratio() * 100, 1),
            "added_lines": len([l for l in lines2 if l not in lines1]),
            "removed_lines": len([l for l in lines1 if l not in lines2]),
            "total_changes": sum(1 for tag, _, _, _, _ in sm.get_opcodes() if tag != "equal"),
        }
        # Also include a compact inline view
        diff_text = "\n".join(difflib.Differ().compare(
            [l.rstrip("\n") for l in lines1],
            [l.rstrip("\n") for l in lines2],
        ))
        diff_text = f"--- Side-by-Side Stats ---\n{json.dumps(stats, indent=2)}\n\n--- Inline View ---\n{diff_text}"

    truncated, was_truncated = truncate_response(diff_text)
    return {
        "status": "ok",
        "diff": truncated,
        "format": output_format,
        "original_lines": len(lines1),
        "modified_lines": len(lines2),
        "has_changes": diff_text != "",
        "truncated": was_truncated,
    }


def toolkit_stats(params):
    """Calculate text statistics."""
    text = params.get("text", "")
    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide text to analyze."]}

    words = text.split()
    lines = text.splitlines()
    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if s.strip()]
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))

    # Reading time (average 238 words per minute)
    word_count = len(words)
    reading_time_seconds = (word_count / 238) * 60
    reading_time_str = f"{int(reading_time_seconds // 60)}m {int(reading_time_seconds % 60)}s"

    # Unique words
    unique = len(set(w.lower().strip(".,!?;:\"'()[]{}") for w in words if w.strip(".,!?;:\"'()[]{}")))

    # Top words
    word_freq = Counter(w.lower().strip(".,!?;:\"'()[]{}") for w in words if len(w.strip(".,!?;:\"'()[]{}")) > 2)
    top_words = [{"word": w, "count": c} for w, c in word_freq.most_common(20)]

    # Paragraph count
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    return {
        "status": "ok",
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "words": word_count,
        "unique_words": unique,
        "lines": len(lines),
        "paragraphs": len(paragraphs),
        "sentences": len(sentences),
        "avg_word_length": round(chars_no_spaces / word_count, 1) if word_count else 0,
        "avg_sentence_length": round(word_count / len(sentences), 1) if sentences else 0,
        "reading_time": reading_time_str,
        "reading_time_seconds": round(reading_time_seconds, 1),
        "top_words": top_words,
    }


def toolkit_case_convert(params):
    """Convert text between case formats."""
    text = params.get("text", "")
    target = params.get("target", "snake_case").lower()

    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide text to convert."]}

    # Normalize: split on boundaries
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)", text)
    if not words:
        words = re.findall(r"[a-zA-Z0-9]+", text)
    if not words:
        words = [text]

    if target == "snake_case" or target == "snake":
        result = "_".join(w.lower() for w in words)
    elif target == "camelCase" or target == "camel":
        result = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    elif target == "PascalCase" or target == "pascal":
        result = "".join(w.capitalize() for w in words)
    elif target == "kebab-case" or target == "kebab":
        result = "-".join(w.lower() for w in words)
    elif target == "SCREAMING_SNAKE" or target == "screaming":
        result = "_".join(w.upper() for w in words)
    elif target == "Title Case" or target == "title":
        result = " ".join(w.capitalize() for w in words)
    elif target == "lowercase" or target == "lower":
        result = " ".join(w.lower() for w in words)
    elif target == "UPPERCASE" or target == "upper":
        result = " ".join(w.upper() for w in words)
    elif target == "dot.case" or target == "dot":
        result = ".".join(w.lower() for w in words)
    elif target == "Train-Case" or target == "train":
        result = "-".join(w.capitalize() for w in words)
    else:
        return {
            "status": "error",
            "isError": True,
            "next_steps": [
                "Supported targets: snake_case, camelCase, PascalCase, kebab-case, SCREAMING_SNAKE, Title Case, lowercase, UPPERCASE, dot.case, Train-Case"
            ],
        }

    return {"status": "ok", "original": text, "target": target, "result": result}


def toolkit_slugify(params):
    """Convert text to URL-friendly slug."""
    text = params.get("text", "")
    separator = params.get("separator", "-")

    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide text to slugify."]}

    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", separator, slug)
    slug = slug.strip(separator)

    return {"status": "ok", "original": text, "slug": slug, "separator": separator}


def toolkit_truncate(params):
    """Truncate text with smart word-boundary ellipsis."""
    text = params.get("text", "")
    max_length = int(params.get("max_length", 200))
    ellipsis = params.get("ellipsis", "...")
    word_boundary = params.get("word_boundary", "true").lower() != "false"

    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide text to truncate."]}

    original_length = len(text)
    if original_length <= max_length:
        return {"status": "ok", "text": text, "truncated": False, "original_length": original_length, "new_length": original_length}

    if word_boundary and max_length > len(ellipsis):
        cut = max_length - len(ellipsis)
        # Find last space within bounds
        truncated = text[:cut]
        last_space = truncated.rfind(" ")
        if last_space > cut // 2:
            truncated = truncated[:last_space]
        result = truncated + ellipsis
    else:
        result = text[:max_length - len(ellipsis)] + ellipsis

    return {"status": "ok", "text": result, "truncated": True, "original_length": original_length, "new_length": len(result)}


def toolkit_regex(params):
    """Find/replace using regex pattern."""
    text = params.get("text", "")
    pattern = params.get("pattern", "")
    replacement = params.get("replacement", None)
    flags_str = params.get("flags", "")
    limit = int(params.get("limit", 50))

    if not text or not pattern:
        return {"status": "error", "isError": True, "next_steps": ["Provide both 'text' and 'pattern' parameters."]}

    flag_map = {
        "i": re.IGNORECASE,
        "m": re.MULTILINE,
        "s": re.DOTALL,
        "x": re.VERBOSE,
    }
    flags = 0
    for f in flags_str:
        flags |= flag_map.get(f, 0)

    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        return {"status": "error", "isError": True, "next_steps": [f"Invalid regex pattern: {e}. Check your pattern syntax."]}

    if replacement is not None:
        if limit == 0:
            result = compiled.sub(replacement, text)
        else:
            result = compiled.sub(replacement, text, count=limit)
        matches_count = len(compiled.findall(text))
        return {"status": "ok", "action": "replace", "result": result, "matches_found": matches_count, "replacements_made": min(matches_count, limit) if limit else matches_count}
    else:
        matches = []
        for i, m in enumerate(compiled.finditer(text)):
            if i >= limit:
                break
            match_info = {"match": m.group(), "start": m.start(), "end": m.end()}
            if m.groups():
                match_info["groups"] = list(m.groups())
            if m.groupdict():
                match_info["named_groups"] = m.groupdict()
            matches.append(match_info)

        response = {"status": "ok", "action": "find", "pattern": pattern, "matches": matches, "match_count": len(matches)}
        if len(compiled.findall(text)) > limit:
            response["truncated"] = True
            response["total_matches"] = len(compiled.findall(text))
            response["message"] = f"Showing first {limit} of {response['total_matches']} matches. Increase 'limit' to see more."
        return response


def toolkit_markdown_to_text(params):
    """Strip markdown formatting to plain text."""
    text = params.get("text", "")
    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide markdown text to convert."]}

    # Built-in markdown stripper (no dependency needed)
    result = text
    # Remove code blocks
    result = re.sub(r"```[\s\S]*?```", lambda m: m.group(0).strip("`").strip(), result)
    # Remove inline code
    result = re.sub(r"`([^`]+)`", r"\1", result)
    # Headers
    result = re.sub(r"^#{1,6}\s+", "", result, flags=re.MULTILINE)
    # Bold/italic
    result = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", result)
    result = re.sub(r"\*\*(.+?)\*\*", r"\1", result)
    result = re.sub(r"\*(.+?)\*", r"\1", result)
    result = re.sub(r"___(.+?)___", r"\1", result)
    result = re.sub(r"__(.+?)__", r"\1", result)
    result = re.sub(r"_(.+?)_", r"\1", result)
    # Strikethrough
    result = re.sub(r"~~(.+?)~~", r"\1", result)
    # Links
    result = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", result)
    # Images
    result = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"[Image: \1]", result)
    # Blockquotes
    result = re.sub(r"^\s*>\s?", "", result, flags=re.MULTILINE)
    # Horizontal rules
    result = re.sub(r"^[-*_]{3,}\s*$", "", result, flags=re.MULTILINE)
    # Unordered lists
    result = re.sub(r"^\s*[-*+]\s+", "• ", result, flags=re.MULTILINE)
    # Ordered lists
    result = re.sub(r"^\s*\d+\.\s+", "", result, flags=re.MULTILINE)
    # Clean up extra whitespace
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = result.strip()

    return {"status": "ok", "text": result, "original_length": len(text), "converted_length": len(result)}


def toolkit_sort_lines(params):
    """Sort lines of text with options."""
    text = params.get("text", "")
    sort_by = params.get("sort_by", "alphabetical")  # alphabetical, length, reverse, shuffle, numeric
    remove_duplicates = params.get("remove_duplicates", "false").lower() != "false"
    case_sensitive = params.get("case_sensitive", "false").lower() != "false"

    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide text with lines to sort."]}

    lines = text.splitlines()
    original_count = len(lines)

    if remove_duplicates:
        seen = set()
        unique_lines = []
        for line in lines:
            key = line if case_sensitive else line.lower()
            if key not in seen:
                seen.add(key)
                unique_lines.append(line)
        lines = unique_lines

    if sort_by == "length":
        lines.sort(key=len)
    elif sort_by == "reverse":
        lines.sort(reverse=True, key=lambda x: x if case_sensitive else x.lower())
    elif sort_by == "shuffle":
        import random
        random.shuffle(lines)
    elif sort_by == "numeric":
        # Try to extract numbers for natural sort
        def num_key(s):
            nums = re.findall(r"\d+", s)
            return tuple(int(n) for n in nums) if nums else (0,)
        try:
            lines.sort(key=num_key)
        except Exception:
            lines.sort()
    else:  # alphabetical
        if case_sensitive:
            lines.sort()
        else:
            lines.sort(key=str.lower)

    return {
        "status": "ok",
        "text": "\n".join(lines),
        "original_lines": original_count,
        "result_lines": len(lines),
        "duplicates_removed": original_count - len(lines) if remove_duplicates else 0,
        "sort_by": sort_by,
    }


def toolkit_format_json(params):
    """Pretty-print, validate, or minify JSON."""
    text = params.get("text", "")
    action = params.get("action", "pretty")  # pretty, validate, minify, flatten
    indent = int(params.get("indent", 2))

    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide JSON text to format."]}

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "isError": True,
            "error": f"Invalid JSON: {e}",
            "position": {"line": e.lineno, "col": e.colno, "pos": e.pos},
            "next_steps": ["Check for trailing commas, unquoted keys, or unmatched brackets."],
        }

    if action == "validate":
        return {
            "status": "ok",
            "valid": True,
            "type": type(data).__name__,
            "top_level_keys": list(data.keys()) if isinstance(data, dict) else None,
            "size": len(text),
            "depth": _json_depth(data),
        }
    elif action == "minify":
        result = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    elif action == "flatten":
        flat = {}
        _flatten_json(data, "", flat)
        result = json.dumps(flat, indent=indent, ensure_ascii=False)
    else:  # pretty
        result = json.dumps(data, indent=indent, ensure_ascii=False)

    return {"status": "ok", "action": action, "result": result, "original_size": len(text), "new_size": len(result)}


def _json_depth(obj, current=0):
    if isinstance(obj, dict) and obj:
        return max(_json_depth(v, current + 1) for v in obj.values())
    if isinstance(obj, list) and obj:
        return max(_json_depth(v, current + 1) for v in obj)
    return current


def _flatten_json(obj, prefix, result):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                _flatten_json(v, new_key, result)
            else:
                result[new_key] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)):
                _flatten_json(v, new_key, result)
            else:
                result[new_key] = v
    else:
        result[prefix] = obj


def toolkit_extract_urls(params):
    """Extract all URLs from text."""
    text = params.get("text", "")
    include_params = params.get("include_params", "true").lower() != "false"

    if not text:
        return {"status": "error", "isError": True, "next_steps": ["Provide text to extract URLs from."]}

    url_pattern = re.compile(
        r"https?://[^\s<>\"')\]]+|www\.[^\s<>\"')\]]+",
        re.IGNORECASE,
    )
    urls = []
    seen = set()
    for m in url_pattern.finditer(text):
        url = m.group()
        if url not in seen:
            seen.add(url)
            parsed = urllib.parse.urlparse(url if "://" in url else f"http://{url}")
            entry = {
                "url": url,
                "scheme": parsed.scheme or "https",
                "domain": parsed.netloc or parsed.path.split("/")[0],
                "path": parsed.path if parsed.netloc else "/".join(parsed.path.split("/")[1:]),
            }
            if include_params and parsed.query:
                entry["query"] = parsed.query
                entry["query_params"] = dict(urllib.parse.parse_qsl(parsed.query))
            if parsed.fragment:
                entry["fragment"] = parsed.fragment
            urls.append(entry)

    return {
        "status": "ok",
        "urls": urls,
        "count": len(urls),
        "unique_domains": len(set(u["domain"] for u in urls)),
    }


def toolkit_format_table(params):
    """Format data as markdown or ASCII tables."""
    data_text = params.get("data", "")
    output_format = params.get("output", "markdown")  # markdown, ascii, csv, json
    delimiter = params.get("delimiter", ",")
    has_header = params.get("has_header", "true").lower() != "false"

    if not data_text:
        return {"status": "error", "isError": True, "next_steps": ["Provide table data (CSV, TSV, or pipe-delimited)."]}

    # Auto-detect delimiter
    if "\t" in data_text and delimiter == ",":
        delimiter = "\t"

    lines = [l.strip() for l in data_text.strip().splitlines() if l.strip()]
    if not lines:
        return {"status": "error", "isError": True, "next_steps": ["No data rows found."]}

    rows = [re.split(rf"\s*{re.escape(delimiter)}\s*", line) for line in lines]

    if not rows:
        return {"status": "error", "isError": True, "next_steps": ["Could not parse rows. Check delimiter."]}

    headers = rows[0] if has_header else [f"Col {i+1}" for i in range(len(rows[0]))]
    data_rows = rows[1:] if has_header else rows
    col_count = len(headers)

    # Pad short rows
    for row in data_rows:
        while len(row) < col_count:
            row.append("")

    if output_format == "csv":
        result = "\n".join(delimiter.join(row) for row in ([headers] + data_rows))
    elif output_format == "json":
        result = json.dumps([dict(zip(headers, row)) for row in data_rows], indent=2)
    elif output_format == "ascii":
        col_widths = [max(len(h), max((len(r[i]) for r in data_rows), default=0)) for i, h in enumerate(headers)]
        col_widths = [max(w, len(h)) for w, h in zip(col_widths, headers)]

        sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(f" {h:{w}} " for h, w in zip(headers, col_widths)) + "|"
        data_lines = ["|" + "|".join(f" {r[i]:{col_widths[i]}} " for i in range(col_count)) + "|" for r in data_rows]
        result = "\n".join([sep, header_row, sep] + data_lines + [sep])
    else:  # markdown
        header_row = "| " + " | ".join(headers) + " |"
        sep_row = "| " + " | ".join("---" for _ in headers) + " |"
        data_lines = ["| " + " | ".join(row) + " |" for row in data_rows]
        result = "\n".join([header_row, sep_row] + data_lines)

    return {
        "status": "ok",
        "output": output_format,
        "rows": len(data_rows),
        "columns": col_count,
        "headers": headers,
        "result": result,
    }


# ── MCP stdio server ────────────────────────────────────────────────────────

TOOLS = {
    "toolkit_diff": {
        "fn": toolkit_diff,
        "description": "Compare two texts and show differences (unified diff, inline, or side-by-side stats).",
        "schema": {
            "type": "object",
            "properties": {
                "text1": {"type": "string", "description": "First/original text"},
                "text2": {"type": "string", "description": "Second/modified text"},
                "context": {"type": "integer", "description": "Lines of context for unified diff", "default": 3},
                "format": {"type": "string", "enum": ["unified", "inline", "side_by_side"], "description": "Diff output format", "default": "unified"},
            },
            "required": ["text1", "text2"],
        },
    },
    "toolkit_stats": {
        "fn": toolkit_stats,
        "description": "Analyze text: word count, reading time, top words, sentence/paragraph counts, etc.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
            },
            "required": ["text"],
        },
    },
    "toolkit_case_convert": {
        "fn": toolkit_case_convert,
        "description": "Convert text between case formats: snake_case, camelCase, PascalCase, kebab-case, SCREAMING_SNAKE, Title Case, lowercase, UPPERCASE, dot.case, Train-Case.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert"},
                "target": {"type": "string", "description": "Target case format", "default": "snake_case"},
            },
            "required": ["text", "target"],
        },
    },
    "toolkit_slugify": {
        "fn": toolkit_slugify,
        "description": "Convert text to a URL-friendly slug (lowercase, spaces to hyphens, special chars removed).",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to slugify"},
                "separator": {"type": "string", "description": "Word separator character", "default": "-"},
            },
            "required": ["text"],
        },
    },
    "toolkit_truncate": {
        "fn": toolkit_truncate,
        "description": "Truncate text to max length with word-boundary-aware ellipsis.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to truncate"},
                "max_length": {"type": "integer", "description": "Maximum character length", "default": 200},
                "ellipsis": {"type": "string", "description": "Ellipsis string", "default": "..."},
                "word_boundary": {"type": "boolean", "description": "Truncate at word boundary if possible", "default": True},
            },
            "required": ["text"],
        },
    },
    "toolkit_regex": {
        "fn": toolkit_regex,
        "description": "Find or replace text using regex patterns. Supports flags: i (case-insensitive), m (multiline), s (dotall), x (verbose).",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to search in"},
                "pattern": {"type": "string", "description": "Regex pattern to match"},
                "replacement": {"type": "string", "description": "Replacement text (omit for find-only mode)"},
                "flags": {"type": "string", "description": "Regex flags: i, m, s, x (e.g., 'im' for case-insensitive multiline)"},
                "limit": {"type": "integer", "description": "Max matches to return/replace", "default": 50},
            },
            "required": ["text", "pattern"],
        },
    },
    "toolkit_markdown_to_text": {
        "fn": toolkit_markdown_to_text,
        "description": "Strip markdown formatting to produce clean plain text.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Markdown text to convert"},
            },
            "required": ["text"],
        },
    },
    "toolkit_sort_lines": {
        "fn": toolkit_sort_lines,
        "description": "Sort lines of text alphabetically, by length, reverse, numeric, or shuffle. Optional dedup.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text with lines to sort"},
                "sort_by": {"type": "string", "enum": ["alphabetical", "length", "reverse", "shuffle", "numeric"], "description": "Sort method", "default": "alphabetical"},
                "remove_duplicates": {"type": "boolean", "description": "Remove duplicate lines", "default": False},
                "case_sensitive": {"type": "boolean", "description": "Case-sensitive sorting", "default": False},
            },
            "required": ["text"],
        },
    },
    "toolkit_format_json": {
        "fn": toolkit_format_json,
        "description": "Pretty-print, validate, minify, or flatten JSON.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "JSON string to process"},
                "action": {"type": "string", "enum": ["pretty", "validate", "minify", "flatten"], "description": "What to do with the JSON", "default": "pretty"},
                "indent": {"type": "integer", "description": "Indentation spaces for pretty/flatten output", "default": 2},
            },
            "required": ["text"],
        },
    },
    "toolkit_extract_urls": {
        "fn": toolkit_extract_urls,
        "description": "Extract all URLs from text with domain, path, and query param parsing.",
        "schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text containing URLs"},
                "include_params": {"type": "boolean", "description": "Parse and include query parameters", "default": True},
            },
            "required": ["text"],
        },
    },
    "toolkit_format_table": {
        "fn": toolkit_format_table,
        "description": "Convert CSV/TSV/pipe data to markdown tables, ASCII tables, JSON, or CSV.",
        "schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Table data (CSV, TSV, or pipe-delimited)"},
                "output": {"type": "string", "enum": ["markdown", "ascii", "csv", "json"], "description": "Output format", "default": "markdown"},
                "delimiter": {"type": "string", "description": "Column delimiter", "default": ","},
                "has_header": {"type": "boolean", "description": "First row is header", "default": True},
            },
            "required": ["data"],
        },
    },
}


async def handle_request(request):
    """Process a single JSON-RPC request."""
    rid = request.get("id")
    method = request.get("method", "")

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "content-toolkit-mcp",
                    "version": "1.0.0",
                    "description": "11 text processing tools for AI agents — diff, stats, case convert, slug, truncate, regex, markdown-to-text, sort, JSON format, URL extract, table format. Zero API keys. Freemium: 50 calls free, $19/mo Pro.",
                },
            },
        })

    if method == "tools/list":
        tools_list = []
        for name, tool in TOOLS.items():
            tools_list.append({
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["schema"],
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
            })
        return json.dumps({"jsonrpc": "2.0", "id": rid, "result": {"tools": tools_list}})

    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        tool_params = request.get("params", {}).get("arguments", {})

        tool = TOOLS.get(tool_name)
        if not tool:
            return json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps({"error": f"Unknown tool: {tool_name}", "isError": True})}]},
            })

        # Rate limit check
        limit_check = check_rate_limit()
        if limit_check:
            return json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(limit_check)}]},
            })

        try:
            result = tool["fn"](tool_params)
        except Exception as e:
            result = {"status": "error", "isError": True, "error": str(e), "next_steps": ["Check input parameters.", "Report this issue if it persists."]}

        return json.dumps({
            "jsonrpc": "2.0", "id": rid,
            "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
        })

    if method == "notifications/initialized":
        return None  # No response for notifications

    return json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Method not found: {method}"}})


async def main():
    """MCP stdio main loop."""
    import sys

    # Write startup info to stderr (MCP protocol uses stdout for JSON-RPC)
    tier = "PRO (unlimited)" if IS_PRO else f"FREE ({FREE_LIMIT} calls)"
    print(f"Content Toolkit MCP v1.0.0 — {tier}", file=sys.stderr)
    print(f"Pro upgrade: {STRIPE_LINK}", file=sys.stderr)

    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    loop = asyncio.get_event_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)

    buffer = b""
    while True:
        try:
            data = await reader.read(65536)
            if not data:
                break
            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    request = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue

                response = await handle_request(request)
                if response:
                    writer.write((response + "\n").encode())
                    await writer.drain()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            break


if __name__ == "__main__":
    asyncio.run(main())
