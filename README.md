# 🧰 Content Toolkit MCP

> Your AI agent's Swiss Army knife for text and content operations.

[![MCP Server](https://img.shields.io/badge/MCP-Server-blue)](https://smithery.ai/servers/vishar-rumbling/content-toolkit-mcp)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Pro](https://img.shields.io/badge/Pro-%2419%2Fmo-blueviolet)](https://buy.stripe.com/14kg3reZT1Fv9H2288)

**11 pure-Python text processing tools. Zero API keys. Freemium with 50 free calls. $19/mo Pro unlimited.**

---

## 🎯 Why Content Toolkit?

AI agents constantly need to manipulate text — compare diffs, calculate stats, convert case, validate JSON, extract URLs, format tables. Instead of writing ad-hoc Python in every agent, Content Toolkit MCP gives you **11 battle-tested, production-ready tools** in a single MCP server.

Every tool is:
- **100% Python stdlib** — no external dependencies beyond `mcp`
- **Read-only, idempotent** — safe for any agent to call
- **Error-as-result** — never throws exceptions, always returns structured JSON
- **Rate-limited** — free tier with clear upgrade path

---

## 🛠️ Tools

| Tool | Description | Example Use Case |
|------|-------------|-----------------|
| `toolkit_diff` | Compare two texts (unified, inline, side-by-side) | Review code changes, compare versions |
| `toolkit_stats` | Word count, reading time, top words, density metrics | Analyze content quality, SEO stats |
| `toolkit_case_convert` | 10 format conversions: snake_case, camelCase, kebab, etc. | Normalize identifiers, reformat text |
| `toolkit_slugify` | Convert text to URL-friendly slugs | Generate SEO-friendly URLs |
| `toolkit_truncate` | Smart truncation with word-boundary ellipsis | Summarize long text for previews |
| `toolkit_regex` | Find/replace with regex flags (im, sx, multiline) | Extract patterns, clean data |
| `toolkit_markdown_to_text` | Strip markdown to clean plain text | Extract readable content from docs |
| `toolkit_sort_lines` | Sort (alpha, length, numeric, shuffle) + dedup | Organize lists, clean datasets |
| `toolkit_format_json` | Pretty-print, validate, minify, flatten JSON | Debug API responses, compact data |
| `toolkit_extract_urls` | Extract all URLs with domain/path/query parsing | Link extraction, domain analysis |
| `toolkit_format_table` | CSV/TSV → markdown tables, ASCII, JSON | Visualize data for reporting |

---

## 📦 Installation

### Smithery (Recommended)
```bash
npx smithery install content-toolkit-mcp --client claude
```

### Manual (Python)
```bash
git clone https://github.com/Rumblingb/content-toolkit-mcp.git
cd content-toolkit-mcp
pip install -r requirements.txt
python3 server.py
```

### Claude Desktop Config
```json
{
  "mcpServers": {
    "content-toolkit": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/path/to/content-toolkit-mcp"
    }
  }
}
```

---

## 💰 Pricing

| Tier | Price | Limits |
|------|-------|--------|
| **Free** | $0 | 50 calls per server start |
| **Pro** | $19/mo | Unlimited calls |

**[Upgrade to Pro →](https://buy.stripe.com/14kg3reZT1Fv9H2288)**

Pro users get:
- Unlimited calls across all 11 tools
- Priority support via GitHub Issues
- Access to new tools before free tier

---

## 🧪 Usage Examples

### Diff two texts
```json
{
  "tool": "toolkit_diff",
  "text1": "Hello world\nThis is line 2\nLine 3",
  "text2": "Hello world v2\nThis is line 2\nLine 3 modified",
  "format": "unified"
}
```

### Analyze text stats
```json
{
  "tool": "toolkit_stats",
  "text": "Your long article text here..."
}
```
Returns: word count, reading time, sentence count, top 20 words, avg word/sentence length.

### Convert case
```json
{
  "tool": "toolkit_case_convert",
  "text": "Convert this text",
  "target": "snake_case"
}
```
→ `convert_this_text`

### Pretty-print JSON
```json
{
  "tool": "toolkit_format_json",
  "text": "{\"key\":\"value\"}",
  "action": "pretty",
  "indent": 2
}
```

### Generate markdown table from CSV
```json
{
  "tool": "toolkit_format_table",
  "data": "Name,Age,City\nAlice,30,NYC\nBob,25,SF",
  "output": "markdown"
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         MCP Client (Claude, etc.)    │
└────────────┬────────────────────────┘
             │ JSON-RPC over stdio
┌────────────▼────────────────────────┐
│       Content Toolkit MCP Server     │
│                                      │
│  ┌──────────┐  ┌───────────┐        │
│  │ Rate Lim  │  │  Tool     │        │
│  │ (free 50) │  │  Registry │        │
│  └──────────┘  └─────┬─────┘        │
│                      │               │
│     ┌────────────────┼──────────┐    │
│     │                │          │    │
│  Diff │ Stats│Case │Regex│JSON│ ...  │
│       │      │Conv │     │    │      │
└───────┴──────┴──────┴─────┴────┴────┘
     All tools: Python stdlib only
```

---

## 🔄 Error Handling

All tools return errors INSIDE the response (never throw exceptions):
```json
{
  "status": "error",
  "isError": true,
  "error": "Invalid JSON: Expecting ',' delimiter",
  "next_steps": ["Check for trailing commas", "Validate brackets match"]
}
```

Rate limit exceeded:
```json
{
  "error": "Free tier limit (50 calls). Upgrade to Pro.",
  "isError": true,
  "next_steps": [
    "Buy Pro: https://buy.stripe.com/14kg3reZT1Fv9H2288",
    "Restart server to reset counter",
    "Use --pro-key PROL_AGENTPAY_DEMO for testing"
  ],
  "calls_used": 50,
  "limit": 50
}
```

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

**Part of the AgentPay Labs ecosystem** — [More MCP Servers](https://rumblingb.github.io/mcp-directory/)

[![smithery badge](https://smithery.ai/badge/vishar-rumbling/content-toolkit-mcp)](https://smithery.ai/servers/vishar-rumbling/content-toolkit-mcp)
