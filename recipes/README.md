# Recipe drafts

These are original designs inspired by the linked projects; they are **not imported workflows or verified integrations**. All are `draft` and require a suitable environment, credentials where applicable and testing.

| Recipe | Input → output | Sources | Validation needed |
|---|---|---|---|
| GitHub release digest | Repository list → linked release summary | [n8n](https://github.com/n8n-io/n8n), [Huginn](https://github.com/huginn/huginn) | Check version, deduplicate release IDs, preserve source links, handle API errors |
| Web change monitor | URL/feed → structured change record | [Huginn](https://github.com/huginn/huginn), [agent-browser](https://github.com/vercel-labs/agent-browser) | Ignore irrelevant layout changes, test inaccessible pages and retry bounds |
| HTML report | Structured data → accessible HTML preview | [frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design), [webapp-testing](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | Validate rendering, input escaping and links on desktop/mobile |
| Workflow authoring assistant | Intent → proposed n8n workflow | [n8n-MCP](https://github.com/czlonkowski/n8n-mcp), [n8n](https://github.com/n8n-io/n8n) | Match installed node versions and test safely before activation |
| File classification | Document → suggested category and destination | [Awesome n8n Templates](https://github.com/enescingoz/awesome-n8n-templates) | Preserve original, queue uncertain cases, verify duplicate handling |

Recommended first implementation: GitHub release digest, tested with a fixed engine version and a non-production source.
