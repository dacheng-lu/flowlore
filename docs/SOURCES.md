# Sources / 来源

Reviewed 2026-11-02. “Top 5” means curated selections for complementary coverage and community relevance, not a complete ranking by stars, installs or benchmark scores. Links are to upstream projects; they are not bundled or installed. Verify licenses, version compatibility and security before use.

## Automation platforms

| Source | Role in FlowLore | Integration status |
|---|---|---|
| [n8n](https://github.com/n8n-io/n8n) | Workflow engine, integrations and AI workflows | Reference only |
| [Huginn](https://github.com/huginn/huginn) | Monitoring and event-processing patterns | Reference only |
| [Awesome n8n Templates](https://github.com/enescingoz/awesome-n8n-templates) | Scenario and template discovery | Reference only; template-level provenance needs review |
| [Activepieces](https://github.com/activepieces/activepieces) | Alternative engine and connector patterns | Reference only |
| [n8n-MCP](https://github.com/czlonkowski/n8n-mcp) | Community MCP interface for n8n knowledge | Reference only; distinct from n8n's own MCP |

## Web and HTML agent skills

These five cover complementary parts of a web workflow. Their ranking is editorial, not a GitHub-wide popularity ranking; repository stars do not measure individual skills. Checked against the upstream `SKILL.md` files on 2026-11-02; Git blob hashes below identify the content reviewed, not a commit pin.

| Skill | Source | Use | Reviewed blob |
|---|---|---|---|
| Frontend Design | [Anthropic](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) | Visual direction and frontend design | `a5333457c414d20d625f307df945842c0952ecc3` |
| Webapp Testing | [Anthropic](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md) | Test local web applications with Playwright | `4726215301db64a0cc4d41fc3219c61f37a30f4a` |
| Web Artifacts Builder | [Anthropic](https://github.com/anthropics/skills/blob/main/skills/web-artifacts-builder/SKILL.md) | Complex Claude HTML artifacts using frontend tooling | `8b39b19f259b4216ecb07574741dd8eaa9863a07` |
| Web Design Guidelines | [Vercel](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) | Review UI code against web interface guidelines | `ceae92ab319216a68274168fba9b63b998b65997` |
| Agent Browser | [Vercel Labs](https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md) | Browser navigation, extraction and interaction | `67e8a49ad8d8e5874b9e3a5d802df68d5e5e7d76` |

The web design guidelines skill retrieves rules from a moving source; record the rules revision for reproducible audits. The HTML artifacts builder targets a specific Claude artifact workflow and is not a general-purpose browser automation tool. Browser automation requires a compatible runtime and site access.

### Additional design references (draft)

The following were added as recipe references, outside the original curated five. They have
not been installed or tested in FlowLore; consult their current upstream revisions and licenses.

| Source | Role | Status |
|---|---|---|
| [AI Design Skills](https://github.com/elayadesign/ai-design-skills) | Landing page planning and visual system | Draft reference |
| [Impeccable](https://github.com/pbakaus/impeccable) | Interface critique and design guidance | Draft reference |
| [Anatomy](https://github.com/wheresryan22/anatomy) | Interactive illustrations and explanations | Draft reference |

See the [design recipes](../recipes/design-workflows.md) for inputs, example and acceptance.

## Primary references

Not projects to evaluate but the sources this catalog checks technical claims against. Both
were read on 2026-11-03; the operational conclusions drawn from them are in
[n8n/OPERATIONS.md](n8n/OPERATIONS.md) and [n8n/VERSION-MATRIX.md](n8n/VERSION-MATRIX.md).

| Source | Role in FlowLore | Integration status |
|---|---|---|
| [n8n documentation](https://docs.n8n.io) | Vendor documentation: flow logic, node reference, error handling, data tables | Reference only |
| [n8n public API reference](https://docs.n8n.io/connect/n8n-api/api-reference.md) | Generated endpoint reference (API `1.1.1`) used for every API statement in this repository | Reference only |

## Attribution and licensing

No upstream code, prompts or workflows are copied into this catalog. Links and descriptions are editorial summaries, not vendor partnerships. Licenses can differ by repository, directory, template and release; check the source directly before copying or redistribution. n8n describes itself as fair-code; Activepieces distinguishes MIT community features from commercial enterprise features.
