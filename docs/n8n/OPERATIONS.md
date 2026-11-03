# n8n operations

**Status:** field notes, not vendor documentation. Reviewed 2026-11-03 against
[docs.n8n.io](https://docs.n8n.io) and the public API description (`1.1.1`, shipped with
n8n `2.46.4`). Observations marked *field* were made while operating self-hosted instances
between `2.27.5` and `2.41.7`; they are labelled with the version they were seen on.

Read this when you have to change, publish, test or debug a workflow that other people
already depend on. For building a workflow from scratch, the vendor documentation is the
better teacher; this chapter is about the distance between "the graph looks right" and
"the thing actually runs".

## Contents

1. [The model that explains most surprises](#1-the-model-that-explains-most-surprises)
2. [Choose the interface](#2-choose-the-interface)
3. [Public API map](#3-public-api-map)
4. [Reading state without leaking secrets](#4-reading-state-without-leaking-secrets)
5. [Writing state](#5-writing-state)
6. [Publishing and verifying](#6-publishing-and-verifying)
7. [Starting a run for verification](#7-starting-a-run-for-verification)
8. [Diagnosing an execution](#8-diagnosing-an-execution)
9. [Changing a live workflow](#9-changing-a-live-workflow)
10. [Data tables](#10-data-tables)
11. [AI and MCP nodes](#11-ai-and-mcp-nodes)
12. [Error handling and alerting](#12-error-handling-and-alerting)
13. [Version detection and compatibility](#13-version-detection-and-compatibility)
14. [Checklists](#14-checklists)

---

## 1. The model that explains most surprises

Four statements carry most of the operational load:

- A workflow has a **definition** (nodes, connections, settings) and, once published, a
  **published version** identified by `activeVersionId`. In API `1.1.1` the old boolean
  `active` is deprecated — check `activeVersionId !== null` instead.
- **Triggers exist only while a version is published.** Webhook, schedule, form, chat, MCP
  and error routes register on publish and disappear on unpublish.
- An **execution** is a stored run. Whether it is stored at all is a workflow setting
  (`saveDataSuccessExecution`, `saveDataErrorExecution`), not a property of the run.
- **Editing is not publishing.** Depending on version and request, saving either republishes
  or leaves a draft (see `publishIfActive` in §5).

Almost every confusing symptom in [FAILURE-MODES.md](FAILURE-MODES.md) is one of those four
statements being violated: a webhook that answers 404 although the workflow "is active", a
new node that never executes, "no executions" for a workflow that clearly ran, or an
execution that used last week's definition.

## 2. Choose the interface

| Interface | Use for | Limits |
| --- | --- | --- |
| **UI** | Exploring, editing, credentials, one-off tests | Not scriptable, no diff, no audit trail of who changed what |
| **Public REST API** (`/api/v1`) | Inventory, create/update, publish, read executions, data tables | Some older builds lack scopes; body schema is strict (§5) |
| **Internal REST** (`/rest/...`) | Only what the public API does not expose (e.g. some activation flows on older builds) | Undocumented, session-cookie auth, changes between minor versions. Treat as unsupported |
| **CLI** (`n8n export`, `n8n import`) | Backups, bulk exports inside the container | Needs host access; `n8n execute` is for logic debugging, not for testing error chains |
| **MCP** | Letting a client (Claude Desktop, IDE) read/execute selected workflows | Tool surface is narrower than the API; enable per workflow |

Default order: **public API → CLI → internal REST → UI clicks**. Every UI step you cannot
replay is a step nobody can review later.

## 3. Public API map

Base `https://<host>/api/v1`. Every request carries the header `X-N8N-API-KEY`; its value is
the only secret involved. Authentication also accepts a bearer JWT or the `n8n-auth` cookie,
but API keys are the only mechanism meant for automation. Pagination is `limit` (max 250)
plus `cursor`/`nextCursor`.

| Resource | Operations (operations that matter for operations work, not the full list) |
| --- | --- |
| Workflows | `GET`/`POST /workflows`, `GET`/`PUT`/`DELETE /workflows/{id}`, `POST /workflows/{id}/archive` and `/unarchive`, `POST /workflows/{id}/activate` and `/deactivate`, `POST /workflows/{id}/publish` and `/unpublish`, `GET /workflows/{id}/history`, `GET /workflows/{id}/versions/{versionId}`, `PUT /workflows/{id}/tags`, `POST /workflows/{id}/transfer` |
| Executions | `GET /executions`, `GET /executions/{id}?includeData=true`, `POST /executions/{id}/retry`, `POST /executions/{id}/stop`, `DELETE /executions/{id}`, `GET` and `PUT /executions/{id}/tags` |
| Credentials | `GET`/`POST /credentials`, `GET`/`PATCH`/`DELETE /credentials/{id}`, `POST /credentials/{id}/test`, `GET /credentials/schema/{type}` |
| Data tables | `GET`/`POST /data-tables`, `PATCH /data-tables/{id}`, `GET`/`POST /data-tables/{id}/columns`, `GET`/`POST /data-tables/{id}/rows`, `POST /data-tables/{id}/rows/upsert`, `PATCH /data-tables/{id}/rows/update`, `DELETE /data-tables/{id}/rows/delete` and `/clear` |
| Other groups | projects, folders, tags, variables, users, audit, insights, source control — present in the API, not covered here |

Three details that are easy to miss:

- **`POST /workflows/{id}/publish` and `.../activate` are the same operation** with different
  names. Both accept an optional body `{versionId, name, description}`; without `versionId`
  the latest version is published.
- **`POST /executions/{id}/retry` exists.** There is still no "run this workflow" endpoint
  (§7), but a stored execution can be re-run, and `{loadWorkflow: true}` makes the retry use
  the *current* definition instead of the one that ran.
- **Version history is readable**: `GET /workflows/{id}/history` lists versions,
  `GET /workflows/{id}/versions/{versionId}` returns one. That is the cheapest way to
  answer "what changed since the incident".

## 4. Reading state without leaking secrets

A workflow read is not harmless output. `GET /workflows/{id}` returns
`nodes[].parameters`, which for HTTP nodes contains `headerParameters` and for some nodes
inline credentials. The published snapshot **`activeVersion.nodes[]` is a second copy** —
redacting only `nodes` still leaves the token in the payload.

Rules that survived contact with a real audit:

- Print **structure**, not parameters: node name, type, `typeVersion`, and the risk flags
  `disabled`, `onError`, `retryOnFail`, `maxTries`, `executeOnce`, `alwaysOutputData`.
  Method and URL are fine; header values only as length or prefix.
- When a dump is unavoidable, write it with placeholders and inject real values at request
  time; then grep the file for `Bearer`, `api_key`, `password` before it leaves the machine.
- `GET /executions/{id}` accepts `redactExecutionData=true`. Use it for tickets and reports.
- If `GET /credentials` is forbidden, build the credential inventory from the workflows:
  aggregate `nodes[].credentials` over all workflows. You get type, name and id — never the
  secret — and you learn the exact credential *name* a new node has to reference.

## 5. Writing state

### Create

- `POST /workflows` accepts an optional **`Idempotency-Key`** header (n8n `2.45.0` and
  later). The first successful response is kept for 12 hours and replayed for the same
  key; the same key with a different body answers `422`, a concurrent duplicate `409`.
  Without the header, a retried create produces a second workflow — which is exactly how
  duplicates appear in instances that are written by scripts.
- `description` is accepted by the current schema but was rejected by some `2.x` builds
  (*field*, `2.4x`). If a create fails with "Unrecognized key", drop the named fields and
  retry; the validator, not the recipe, decides.

### Update

`PUT /workflows/{id}` requires `name`, `nodes`, `connections` **and `settings`**. The body
schema also *lists* read-only fields — `id`, `active`, `activeVersionId`, `createdAt`,
`updatedAt`, `isArchived`, `versionId`, `triggerCount`, `pinData`, `meta`, `tags`,
`shared`, `activeVersion` — and rejects them on write. Round-tripping a `GET` response into
a `PUT` therefore fails until those keys are stripped. Round-trip scripts should keep an
allow-list, not a deny-list.

Two behaviours that differ by version and cost real time:

- **`publishIfActive` (query parameter, default `true`).** On a published workflow, a `PUT`
  publishes the new definition immediately. That is convenient and dangerous: the change
  goes live with no test. Send `publishIfActive=false` to keep the old version serving while
  you save a draft. On older builds this parameter does not exist and a `PUT` did **not**
  republish (*field*, `2.41.7`) — the running version stayed on `activeVersionId` until an
  explicit `deactivate` + `activate`. Check which behaviour your instance has before
  trusting either.
- **Node fields are restricted.** Allowed: `id, name, type, typeVersion, position,
  parameters, notes, notesInFlow, credentials, webhookId, disabled, onError,
  executeOnce, alwaysOutputData, retryOnFail, maxTries, waitBetweenTries,
  continueOnFail, customTelemetryTags`. A build script that filters node keys against an
  incomplete list drops `retryOnFail`/`maxTries` silently: the workflow still validates and
  simply stops retrying.
- **Connections are keyed by node *name*.** Renaming a node without rewriting the
  connection map produces `unknown_connection_target` — or, worse, a dangling branch that
  silently ends the run.
- **Credentials survive only with the exact stored name.** If the embedded credential
  `name` does not match the stored one character for character, the node comes back with
  `credentials: null` and fails at runtime with "Authorization failed" (*field*, `2.41.7`).
  Read the name from a workflow that already uses that credential, and re-read the workflow
  after every `PUT`.

### Deleting

`DELETE /workflows/{id}` is immediate and cascades to the published version. Archive
(`POST /workflows/{id}/archive`) is the reversible alternative and keeps the definition for
later inspection. For operations work, archive first; delete only on explicit instruction.

## 6. Publishing and verifying

Publishing is a state transition, and the only proof that it worked is a request against
the trigger.

| Trigger | Probe | What a good answer looks like |
| --- | --- | --- |
| Webhook (`responseMode: onReceived`) | `POST https://<host>/webhook/<path>` | `200 {"message":"Workflow was started"}` |
| Webhook (`responseMode: lastNode`) | same call | the response body of the last node |
| Form | `GET https://<host>/form/<path>` | HTML form; 404 means the route is not registered |
| Chat | `POST /webhook/<id>/chat` with `{action:"sendMessage",sessionId,chatInput}` | `{"output": "..."}` |
| MCP server trigger | `POST https://<host>/mcp/<path>` (JSON-RPC) | `400`/`403` prove routing; a JSON-RPC result proves the tool |
| Schedule | wait for the tick or read the next execution | an execution with `mode: trigger` |

A `200` from a webhook is **not** a success signal — n8n answers before the chain finishes,
and it answers `200` even when the first branch ends empty. The verification is always the
execution record (§8).

Form URLs are a special case: the route segment lives in `options.path`, not in a top-level
`path` field. With a top-level value the canonical `/form/<path>` route stays 404 while the
form is served at `/<path>` and `/form/<webhookId>` (*field*, `2.41.x`). After changing it,
republish, or the old route keeps serving.

## 7. Starting a run for verification

- **There is no run endpoint.** `POST /api/v1/workflows/{id}/run` answers
  `405 {"message":"POST method not allowed"}` and does not appear in API `1.1.1`. A
  workflow with only a Manual Trigger cannot be started over the API at all.
- Consequence for agents and CI: build the test workflow **with a webhook trigger from the
  start**. A two-node probe (Webhook → the node under test, `responseMode: lastNode`) returns
  the real API response to your `POST` and proves credential and filter syntax without
  running the production chain.
- A manual execution does **not** trigger the configured error workflow (*field*, `2.41.7`).
  Testing the error path therefore requires a production-mode execution — a webhook-triggered
  "test bomb" that throws on purpose.
- `POST /executions/{id}/retry` replays a stored execution. With `loadWorkflow: true` it
  uses the current definition, which makes it a practical way to re-run a failed job after a
  fix — but it is a *replay of the same input*, not a fresh trigger.

## 8. Diagnosing an execution

```text
GET /executions?workflowId=<id>&limit=5          → id, status, startedAt, mode
GET /executions/<id>?includeData=true            → resultData.runData
```

Read in this order:

1. `status` — `success`, `error`, `crashed`, `waiting`, `running`.
2. `resultData.error` — node name plus message. Absent on success by definition.
3. `resultData.lastNodeExecuted` — the last node that produced output.
4. `resultData.runData` — walk it in execution order and print **item counts per node**.

The detail payload shape varies by build: sometimes the fields sit at the top level, sometimes
one level down under `data` (*field*, `2.27.5` vs `2.41.x`). Read defensively before
concluding that a run is unreadable.

Signatures worth recognising:

| Signature | Meaning |
| --- | --- |
| `runData == {}` plus a populated `resultData.error` | **Validation failure** — a required parameter is empty, so *no node ran at all*. Node-level `onError` cannot rescue this |
| first node with `outputs: []` | the chain broke there; everything after it never ran |
| status `success`, no error, nothing downstream | a node emitted 0 items. That is a legal, silent end of run |
| node missing from `runData` | it was not reached (upstream 0 items) or it is disabled |
| execution absent from `GET /executions` | `settings.saveDataSuccessExecution: "none"` — the run happened and was not stored |

**Sub-nodes write to their own channel.** A tool attached via `ai_tool` stores its result
under `runData[node][i].data.ai_tool`; `data.main` is empty. The same holds for
`ai_languageModel`, `ai_memory`, `ai_embedding`. Counting only `main` reports "the tool
returned nothing" for a tool that worked. Print every channel key present in `data` before
judging a cluster node.

## 9. Changing a live workflow

The procedure below was used on a monthly billing chain. It is ordered so that the live
version keeps serving until every proof exists.

1. **Back up** the full `GET /workflows/{id}` JSON into the task folder, before anything else.
2. **Keep code nodes as files** (`code_<node>.js`) and inject them with a build script.
   Hand-editing JavaScript inside JSON is how `\n` becomes a literal line break inside a
   string and the run dies with "Invalid or unexpected token".
3. **Run the code offline first.** A harness with `new Function('$input','$','$json', code)`
   and stubs for `$('Node').all()/first()/item` executes each code node without n8n. Write an
   acceptance case for the happy path and for every fail-closed branch. This is the cheapest
   test in the whole chain and the only one that can run in CI.
4. **Fail closed.** A code node that skips an unmapped record silently drops work; one that
   throws stops the run before any write. For anything with money, inventory or customer data
   attached, throw with a readable message.
5. **Test the new integration node in isolation** (§7), then neutralise the probe: deactivate
   it *and* empty its nodes (`"nodes": []`, `"connections": {}`). A deactivated webhook that
   still exists is one activation away from being live again.
6. **Test the whole chain on a twin**: `GET` the production workflow, strip read-only fields,
   set `disabled: true` on the schedule trigger and every side-effect node, attach a unique
   webhook path, publish, fire, read the execution, unpublish.
7. **Prepare, do not publish.** Write the production JSON to a file. Publish only after the
   twin passed and the owner said go.
8. **Re-test the live version, not the build file.** After switching over, `GET` the
   production workflow again and compare with what you intended: `activeVersionId` not null,
   node count, `disabled` flags, `credentials` present, `settings.timezone`.
9. **Keep one workflow id.** A second switch-over script that creates "one more copy" leaves
   an inactive workflow and a stale version check behind. Modify the existing id, publish,
   read back; if the readback deviates, write the backup back and publish again.

Side effects are proven by **counts and hashes of the target data**, never by node status:
disabled nodes still report `status: success` and pass their input through.

## 10. Data tables

Data tables are n8n's built-in tabular storage and the right place for per-customer or
per-device configuration that would otherwise be hardcoded in a Code node.

- **Limits:** 200 MiB per instance by default (`N8N_DATA_TABLES_MAX_SIZE_BYTES`), tables are
  scoped to a project, and **a Code node cannot read them** — there is no built-in method.
  Use the Data Table node or the API.
- **Reserved columns:** `id`, `createdAt`, `updatedAt` are system columns; a table that
  declares one of them fails with "reserved".
- **API shapes:** insert takes `{"data": [ {...} ]}` — an array, not an object — and
  `returnType: "count" | "id" | "all"`. Update is `PATCH /rows/update` with
  `{"filter": {...}, "data": {...}}`; upsert is `POST /rows/upsert`; delete is
  `DELETE /rows/delete?filter=<json>&dryRun=true&returnData=false`, where all three are query
  parameters and `filter` is a JSON *string*.
- **`dryRun: true`** returns the before/after state without writing. Use it before every
  update; two entries per match (`dryRunState: before` / `after`) mean exactly one row.
- **In-workflow:** use the native `n8n-nodes-base.dataTable` node, never an HTTP Request node
  pointed at the instance's own public URL — that is a hairpin request through the internet
  and it hangs behind firewalls.
- **`get` returns one item per row**, which multiplies downstream items. Fan read nodes out in
  parallel and join with a Merge (`mode: append`) or dedupe explicitly.

Pattern that paid off: **config as rows**. A `kunden` table and a `drucker` table with an
`aktiv` flag mean onboarding a new customer is one inserted row — no workflow edit, no
redeploy, and the change is visible in the UI to whoever owns the data.

## 11. AI and MCP nodes

- **AI Agent output.** With `hasOutputParser: false` the agent returns a plain string in
  `$json.output` and *replaces* the input item — every upstream field is gone. Later nodes
  that need upstream data must use `$('Node').item.json.<field>`.
- **Sub-nodes connect by dedicated connection types** (`ai_languageModel`, `ai_memory`,
  `ai_tool`, `ai_embedding`, `ai_vectorStore`), each an own key in `connections`. A tool that
  lost its connection is never called and produces no error — the agent simply answers
  without it. Re-verify those keys after every `PUT`.
- **`promptType: "auto"` only reads `chatInput`.** Behind a Telegram or webhook trigger the
  prompt must be explicit: `promptType: "define"` plus `text: ={{ $json.message.text }}`.
  The leading `=` is what makes n8n evaluate the expression; without it the model receives
  the literal `{{ ... }}` and answers "I have no data".
- **`$fromAI()` hands the choice to the model.** Fine for text the model derives from the
  user's input; wrong for timestamps, session ids and URLs. Bind those to n8n expressions
  (`$now`, `$('Trigger').first().json.sessionId`) and give a fetch tool a fixed allow-list
  instead of a free URL field — otherwise a prompt-injected document steers the request.
- **Guardrails node** is a real gate, not a filter: `Check Text for Violations` routes
  violations to the **Fail** branch, `Sanitize Text` replaces PII, secrets and URLs with
  placeholders. It needs a chat model connected when an LLM-based guardrail is selected.
- **Two different MCP surfaces.** The *MCP Server Trigger node* exposes the tools of one
  workflow at `/mcp/<path>`. *Instance-level MCP* (Settings → MCP, from `2.33.0`; workflow
  building tools from `2.13.0`) exposes a `/mcp-server/http` endpoint where each workflow has
  to be enabled individually (`settings.availableInMCP`). All connected clients see all
  enabled workflows — there is no per-client scoping.

## 12. Error handling and alerting

- **Error workflow** = a workflow starting with the Error Trigger, referenced from the target
  workflow's `settings.errorWorkflow`. One handler can serve many workflows.
- **Payload** (n8n `2.x`): `$json.execution.error.message`, `.stack`, plus
  `$json.execution.id`, `.url`, `.lastNodeExecuted`, `.mode` and `$json.workflow.{id,name}`.
  Older builds delivered `$json.error.*`; a handler written for the old shape writes empty
  tickets and stays green. If the *trigger* itself failed, the payload arrives under
  `$json.trigger.error` and `execution.id` may be missing entirely.
- **The error workflow must be published**, otherwise it is silently not executed
  (*field*, `2.41.7`). After every edit: republish, then prove it with a test bomb.
- **Manual runs do not fire it** (§7). The test bomb is a webhook workflow that throws.
- **`retryOnFail` on reading nodes, never on creating ones.** A lost response from a POST
  looks like a failure while the record already exists; retrying creates the duplicate.
- **`onError: continueRegularOutput`** belongs on notification nodes, never on the step that
  writes the business record.
- **`Stop And Error`** is the supported way to fail on purpose — for example when a code node
  detects an implausible value and the run must not continue.

## 13. Version detection and compatibility

You cannot reason about behaviour without the version. Three ways to get it:

- `GET /rest/settings` — unauthenticated on many self-hosted instances; returns feature flags
  and sometimes the version.
- Editor HTML references a content-hashed bundle `assets/index-*.js`; the bundle contains
  `n8n@<semver>`.
- Inside a workflow: the node's `typeVersion` in the editor, or the instance version in
  Settings → About.

[VERSION-MATRIX.md](VERSION-MATRIX.md) lists which statement in this chapter was verified on
which version, and which ones are known to have changed.

## 14. Checklists

**Before publishing a change**

- [ ] Backup JSON saved outside the instance
- [ ] Code nodes run through the offline harness, fail-closed branches included
- [ ] Twin run passed, with side-effect nodes disabled
- [ ] `credentials` present on every node that needs one (read back after `PUT`)
- [ ] No required parameter left empty — a placeholder disables the whole run
- [ ] `settings.timezone` and `errorWorkflow` unchanged

**After publishing**

- [ ] `activeVersionId` not null, `GET` returns the node count you expect
- [ ] Trigger probed with a real request (not just "activated")
- [ ] Newest execution read: status, item counts, no 0-item stop
- [ ] Side effects proven by counts/hashes, not by node status

**Monthly, per instance**

- [ ] Workflow list diffed against the last export (`n8n export:workflow --backup`)
- [ ] Executions with `status: error` reviewed, not just counted
- [ ] Credential names referenced by workflows still exist
- [ ] Data table storage below the warning threshold

## Sources

- n8n API: [endpoint reference](https://docs.n8n.io/connect/n8n-api/api-reference.md),
  [idempotency](https://docs.n8n.io/connect/n8n-api/idempotency.md),
  [workflow](https://docs.n8n.io/connect/n8n-api/workflow.md)
- [Handle errors gracefully](https://docs.n8n.io/build/flow-logic/handle-errors-gracefully.md)
- [Understand execution order](https://docs.n8n.io/build/flow-logic/understand-execution-order.md)
- [Data tables](https://docs.n8n.io/build/work-with-data/data-tables.md)
- [MCP Server Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger.md),
  [instance-level MCP](https://docs.n8n.io/connect/connect-to-n8n-mcp-server.md)
- [Guardrails](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.guardrails.md)
