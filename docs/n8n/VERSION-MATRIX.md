# n8n version matrix

Which statement in this chapter is true on which version. Most n8n guidance on the internet
is undated, and a large share of the detours come from applying a behaviour that belongs to a
different build. Every row names its evidence: **spec** = the public API description fetched
from the instance documentation, **docs** = the vendor documentation page, **field** = a
self-hosted instance we operated.

Snapshot: documentation and API description read on **2026-11-03**, latest release
**n8n `2.46.4`** (2026-11-02). Field observations span **`2.27.5` → `2.41.7`**.

## How to find your version

| Route | Command | Notes |
| --- | --- | --- |
| Unauthenticated settings | `curl -s https://<host>/rest/settings` | Often open on self-hosted; exposes feature flags and sometimes the version |
| Editor bundle | grep `assets/index-*.js` for `n8n@<semver>` | Works without a login |
| Inside n8n | Settings → About | Requires a session |
| Container | `docker exec n8n n8n --version` | Requires host access |

## Claims and their range

| Claim | Evidence | Holds on | Note |
| --- | --- | --- | --- |
| Base path `/api/v1`, header `X-N8N-API-KEY` | spec 1.1.1 | all `1.x`/`2.x` public API | Bearer JWT and `n8n-auth` cookie are also accepted |
| `active` is deprecated; read `activeVersionId` | spec 1.1.1 | current `2.x` | Older builds still populate `active` |
| `PUT /workflows/{id}` requires `name, nodes, connections, settings` | spec 1.1.1 | current `2.x` | `settings` being required is newer than many recipes assume |
| `PUT` republishes a published workflow by default (`publishIfActive=true`) | spec 1.1.1 | current `2.4x`+ | On `2.41.7` a `PUT` did **not** republish (field) — deactivate/activate was required |
| `PUT ...?publishIfActive=false` saves a draft | spec 1.1.1 | current `2.4x`+ | Not available on older builds |
| `POST /workflows/{id}/activate` and `/publish` are the same operation, both accept `{versionId}` | spec 1.1.1 | current `2.4x`+ | Older builds accept activation without a body only |
| No `POST /workflows/{id}/run` | spec + field | all | Answers `405 {"message":"POST method not allowed"}`; manual-trigger workflows cannot be started via API |
| `POST /executions/{id}/retry` with `{loadWorkflow}` | spec 1.1.1 | current `2.x` | Newer than most field notes; verify on your build |
| `POST /executions/{id}/stop` | spec 1.1.1 | current `2.x` | — |
| `GET /executions/{id}?redactExecutionData=true` | spec 1.1.1 | current `2.x` | Use for tickets and reports |
| `Idempotency-Key` on POST | docs | **`2.45.0`+** | 12 h window, `422` on reuse with a different body, `409` while in progress |
| Workflow version history (`/history`, `/versions/{id}`) | spec 1.1.1 | current `2.x` | Cheapest answer to "what changed" |
| Workflow `nodeGroups` (frames) in the API | spec 1.1.1 | current `2.x` | — |
| `settings.callerPolicy` / `callerIds` on sub-workflows | spec 1.1.1 | current `2.x` | Restricts which workflows may call a sub-workflow |
| `settings.availableInMCP` | spec 1.1.1 | current `2.x` | Must be enabled per workflow for instance-level MCP |
| Error payload under `execution.error.{message,stack}` | docs + field | **`2.37`+** | `2.27.5` delivered top-level `error.*` |
| Trigger failures arrive under `trigger.error` | docs | current `2.x` | `execution.id` may be missing entirely |
| Error workflow must be published to run | field | `2.41.7` | An unpublished handler is silently skipped |
| Manual runs do not trigger the error workflow | field | `2.41.7` | Test with a webhook "test bomb" |
| `settings.saveDataSuccessExecution: "none"` hides successful runs | docs + field | `2.x` | "0 executions" is not "never ran" |
| Data tables (`/data-tables`, Data Table node) | docs + spec | `2.x` | 200 MiB default, `N8N_DATA_TABLES_MAX_SIZE_BYTES` |
| Data table `dryRun` / `returnData` on `DELETE /rows/delete` | spec 1.1.1 | current `2.x` | `filter` is a JSON string in the query |
| Code node cannot read data tables | docs | `2.x` | Use the Data Table node |
| MCP Server Trigger, streamable HTTP + SSE, no stdio | docs | current `2.x` | Endpoint `/mcp/<path>` |
| Instance-level MCP with per-workflow enablement | docs | **`2.33.0`+** (workflow tools `2.13.0`+) | `/mcp-server/http` |
| Guardrails node with Fail branch and Sanitize mode | docs | current `2.x` | LLM-based guardrails need a chat model connected |
| Branch order = canvas position, top to bottom, left to right | docs | workflows created **from `1.0`** | Pre-`1.0` workflows use round-robin across branches |
| `oAuth2Api` supports `authorizationCode`, `clientCredentials`, `pkce` only | docs + field | current `2.x` | No password grant |
| `n8n execute` cannot test error chains | field | `2.27`–`2.37` | CLI crashes with `DriverAlreadyReleasedError` |
| Webhook v2 nests the body under `$json.body`; form trigger exposes `formFields.values[].fieldName` | docs + field | `2.x` | Both change silently when a node's `typeVersion` changes |

## Upgrading from `2.27` to `2.4x` — what to re-check

1. **Error handler expressions.** `$json.error.*` → `$json.execution.error.*`. A handler that
   was never re-tested writes empty tickets and stays green.
2. **Activation.** `POST .../activate` may accept a body on your build; a 403 means the key
   lacks the scope, not that the UI is required.
3. **`PUT` semantics.** Check whether your build republishes on save (`publishIfActive`) or
   requires an explicit `deactivate` + `activate`.
4. **Node `typeVersion`s.** A workflow imported from an older instance keeps the old node
   version and the old parameter shape. Re-create nodes you intend to edit.
5. **API keys.** Scope handling differs between builds; `GET /credentials` may 403 while
   writes succeed.
6. **MCP.** Instance-level MCP is off by default and every workflow must be enabled
   individually.
