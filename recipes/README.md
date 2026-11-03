# Recipes

Original designs inspired by the linked projects; **not imported workflows**. Every recipe
states what goes in, what comes out, what it depends on and what still has to be proven.

## Status

| Status | Meaning | What has to exist |
| --- | --- | --- |
| `draft` | Design only. Nobody has executed it. | — |
| `field-tested` | Executed on at least one real instance or workflow. | A dated evidence summary: version, what ran, what was **not** exercised |
| `verified` | Reproducible from pinned versions in an isolated environment. | Published artifact (export, test output) next to the evidence |

`field-tested` is not a polite word for verified. The evidence for these recipes is a
summary, because the instances, customer data and credentials behind them cannot be
published. No recipe in this repository is `verified` today; the first candidate is the
GitHub release digest, which needs no private infrastructure.

## Recipes

| Recipe | Status | Input → output | Sources | Validation needed |
| --- | --- | --- | --- | --- |
| [GitHub release digest](../examples/release-digest/README.md) | `draft` | Repository list → linked release summary | [n8n](https://github.com/n8n-io/n8n), [Huginn](https://github.com/huginn/huginn) | Check version, deduplicate release IDs, preserve source links, handle API errors |
| Web change monitor | `draft` | URL/feed → structured change record | [Huginn](https://github.com/huginn/huginn), [agent-browser](https://github.com/vercel-labs/agent-browser) | Ignore irrelevant layout changes, test inaccessible pages and retry bounds |
| HTML report | `draft` | Structured data → accessible HTML preview | [frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design), [webapp-testing](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | Validate rendering, input escaping and links on desktop/mobile |
| Workflow authoring assistant | `draft` | Intent → proposed n8n workflow | [n8n-MCP](https://github.com/czlonkowski/n8n-mcp), [n8n](https://github.com/n8n-io/n8n) | Match installed node versions and test safely before activation |
| File classification | `draft` | Document → suggested category and destination | [Awesome n8n Templates](https://github.com/enescingoz/awesome-n8n-templates) | Preserve original, queue uncertain cases, verify duplicate handling |
| [Safe change of a live workflow](#safe-change-of-a-live-workflow) | `field-tested` | Live workflow id + intended change → published change with before/after evidence | [n8n operations](../docs/n8n/OPERATIONS.md), [n8n API](https://docs.n8n.io/connect/n8n-api/api-reference.md) | Rollback path not yet exercised; needs a rehearsal on a throw-away instance |
| [Execution triage](#execution-triage) | `field-tested` | Workflow or execution id → named break point with evidence | [Failure modes](../docs/n8n/FAILURE-MODES.md), [n8n operations](../docs/n8n/OPERATIONS.md) | Repeat against `2.46.x` (field notes are `2.27`–`2.41`) |
| [Workflow inventory](#workflow-inventory) | `field-tested` | Instance URL + API key → workflow, node-type and credential-name inventory | [n8n API](https://docs.n8n.io/connect/n8n-api/api-reference.md) | Add a pagination test above 250 workflows |
| [Error workflow](#error-workflow) | `field-tested` | Workflow id to watch → alert with node, message and execution link | [n8n error handling](https://docs.n8n.io/build/flow-logic/handle-errors-gracefully.md) | Trigger-failure payload (`trigger.error`) not yet covered by a test case |
| [Agent tool contract](#agent-tool-contract) | `draft` | Sub-workflow with input schema → MCP or agent tool | [n8n MCP Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger.md), [course map](../docs/learning-paths/ihk-ki-automatisierung.md) | Test with two MCP clients; document what "empty" means per parameter |
| [Router with specialists](#router-with-specialists) | `draft` | Mixed request → answer from a specialist, merged | [n8n](https://github.com/n8n-io/n8n), [course map](../docs/learning-paths/ihk-ki-automatisierung.md) | Define the fallback when the classifier is unsure |
| [Loop with feedback](#loop-with-feedback) | `draft` | Draft + acceptance criteria → accepted text or a bounded failure | [n8n](https://github.com/n8n-io/n8n), [course map](../docs/learning-paths/ihk-ki-automatisierung.md) | Prove the counter stops the loop; measure cost per accepted result |

## Operations recipes

These four grew out of running self-hosted instances, not out of building new workflows. The
mechanics behind them are in [docs/n8n/OPERATIONS.md](../docs/n8n/OPERATIONS.md).

### Safe change of a live workflow

**Input:** a published workflow id and a change you can describe in one sentence.
**Output:** the same workflow, changed, with before/after evidence and a stored backup.
**Steps:** backup → code nodes as files → offline harness → webhook probe → test twin with
side-effect nodes disabled → prepare, don't publish → publish → read back → prove side effects
by counts, not status ([OPERATIONS §9](../docs/n8n/OPERATIONS.md#9-changing-a-live-workflow)).
**Evidence (`2026-10-30`, n8n `2.41.7`):** followed on a monthly billing chain; the twin run
exposed a period-boundary bug before switch-over. Rollback was prepared but never needed —
that path stays unproven.
**Failure path:** if the readback deviates (node count, `disabled` flags, credentials,
`settings.timezone`), write the backup back and publish again. Do not "fix forward" on a
billing chain.

### Execution triage

**Input:** a workflow id, or the id of a failed run.
**Output:** the first node that produced no output, with the reason, and the name of whatever
should have run after it.
**Steps:** status → error → `lastNodeExecuted` → per-node item counts → the channel that
matches the connection type ([OPERATIONS §8](../docs/n8n/OPERATIONS.md#8-diagnosing-an-execution)).
**Evidence (`2026-10-07`, `2.41.7`):** three cases that all looked like "the workflow is
broken" — a validation failure with `runData: {}`, a 0-item branch that ended a run with
`status: success`, and a tool whose output sat in `data.ai_tool` while `data.main` was empty.
**Failure path:** if the execution is missing entirely, check
`settings.saveDataSuccessExecution` before concluding the run never happened.

### Workflow inventory

**Input:** base URL and an API key. **Output:** every workflow with its node types, and the
credential names it references — never a secret.
**Steps:** `GET /workflows?limit=250` plus cursor → `GET /workflows/{id}` per item → aggregate
`nodes[].type` and `nodes[].credentials`. Where `GET /credentials` is forbidden, this is the
only credential inventory there is.
**Evidence (`2026-10-21`):** run across `2.27.5`, `2.31.5` and `2.41.7`; the metadata-only
output was safe to paste into a ticket.
**Failure path:** read-only means read-only — the script must not activate, publish or write.
If a key lacks the list scope, fall back to a database copy of the instance, not to a write.

### Error workflow

**Input:** the workflow to watch. **Output:** one alert per failed production execution, with
the failing node, the message and a link to the execution.
**Steps:** Error Trigger → format (`execution.error.message`, `execution.lastNodeExecuted`,
`execution.url`) → notify. Set `settings.errorWorkflow` on the target, **publish the
handler**, then prove it with a webhook "test bomb" that throws.
**Evidence (`2026-10-29`, `2.41.7`):** handler published, fired by the test bomb, ticket
contained the execution link. An unpublished handler had silently skipped every error before.
**Failure path:** a handler that still reads `$json.error.*` writes empty alerts and reports
success — that is the failure mode to test for first.

## Pattern recipes

Three structures a course can teach and that still need an operational edge before
production. The mapping to the course blocks is in the
[learning path](../docs/learning-paths/ihk-ki-automatisierung.md).

### Agent tool contract

**Input:** a sub-workflow with a written input schema. **Output:** the same work, callable as
a tool from an agent or an MCP client.
**Steps:** write the contract (`title`, `url`, `summary_hint`) before the graph → one
responsibility per tool → every `$fromAI()` field is mandatory by construction, so describe
"leave empty" as the way to mean "all" → test through the sub-workflow's own webhook before
attaching it.
**Failure path:** a tool that quietly returns nothing leaves the agent free to invent the
result. Return a shaped error instead.

### Router with specialists

**Input:** a request that could belong to more than one domain. **Output:** one answer from
one specialist, or an explicit "not my area".
**Steps:** classifier → Switch → specialist agent per branch → Merge. Keep the classifier's
output structured (`{domain, confidence}`) and route low confidence to a human branch.
**Failure path:** every Switch needs a fallback output; an unmatched request otherwise ends
the run with zero items and no error.

### Loop with feedback

**Input:** a draft and acceptance criteria. **Output:** an accepted draft, or a bounded
failure that names the last rejection.
**Steps:** writer → reviewer → IF accepted → done, else back to writer **with the rejection
reason**; cap the loop with the built-in run counter (`$runIndex`) and check on your own
version whether it starts at 0.
**Failure path:** the retry cap must live in the loop condition, not in a variable the writer
can overwrite; a loop without a cap is a cost incident waiting for a slow reviewer.

Recommended first implementation remains the GitHub release digest: it needs no private
infrastructure and can reach `verified` in one sitting.
