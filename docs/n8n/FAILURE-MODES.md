# n8n failure modes

Symptom → cause → check → fix. Every row here cost at least one debugging session on a
self-hosted instance (2.27.5–2.41.7); where a row depends on a specific version, the version
is named in it. The point of the page is the **check** column: it names the field or endpoint that distinguishes the cause
from the look-alike cause, so the next person does not have to guess.

Companion pages: [OPERATIONS.md](OPERATIONS.md) for the mechanics,
[VERSION-MATRIX.md](VERSION-MATRIX.md) for which behaviour belongs to which version.

## Triggers and routes

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| Webhook answers 404 "not registered" although the workflow shows as active | No version published, or the workflow was saved as a draft | `activeVersionId` on `GET /workflows/{id}` | `POST /workflows/{id}/activate` and probe again |
| 404 with JSON `{"message":"The requested webhook ... is not registered"}` vs. an HTML 404 page | JSON = n8n reached, route missing. HTML = no route there at all (wrong host/path) | Response content type | Fix the path; a JSON 404 is a routing problem inside n8n, HTML is usually a reverse proxy or wrong base URL |
| Webhook 200, but nothing happens | `responseMode` answers before the chain runs | Read the newest execution | Look for the first node with 0 items |
| Telegram-triggered workflow unreachable from outside | Telegram routes are `/webhook/<webhookId>/webhook` and require the secret token | `403 "Provided secret is not valid"` = right path, wrong secret; JSON 404 = wrong path | Test the chain through a webhook twin, not the live Telegram route |
| Form URL 404 | Path stored at top level instead of `options.path` | `GET` the node's `parameters.options.path` | Move it, republish |
| Two workflows, same webhook path, activation fails with 409 | Paths are unique among *active* workflows | The error names the conflict | Deactivate the old one first |
| Schedule workflow never runs | Workflow unpublished, or instance timezone differs | `settings.timezone`, execution `mode: trigger` | Publish; align timezone |

## Data flow

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| Later node sees `undefined` for a field that exists upstream | An HTTP or Data Table node replaced `$json` with its response | Print `$json` at the failing node | `$('Source node').item.json.<field>` |
| A read node runs N times and produces N× rows | Nodes execute once per input item | Item counts per node in `runData` | Fan reads out in parallel, join with `Merge (append)` |
| Chain ends early, status still `success` | A node emitted 0 items | First node with `outputs: []` | Filter later, or branch explicitly instead of relying on emptiness |
| Prompt contains `{{ $json.x }}` literally | Missing `=` prefix on the parameter | `parameters.text` starts with `=` | Add `=` |
| Expression works in the editor preview, fails in the run | Referenced node is not in this workflow (copy/paste) | `NodeOperationError: Referenced node doesn't exist` | Rewrite the reference for the target workflow |
| RSS/HTTP node returns one wrapper object instead of items | API returns `{ "devices": [...] }` as a single item | `runData` output shape | Expand in a code node, accept both shapes |
| A Code node drops the uploaded file | Code nodes return only `json`; `binary` is lost | Error "expects binary file data0" | Use a Set node with `includeOtherFields: true`, or move the code node after extraction |
| CSV analysis says "the file has one row" | CSV yields one item per row, code used `$input.first()` | Number of input items | `$input.all()` and join |

## Validation and configuration

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| Nothing ran at all; `runData` is `{}` | A required parameter is empty; validation happens before the first node | `resultData.error` names node and parameter | Fill it, or set `disabled: true` and document the step in `notes` |
| Node-level `onError` did not help | Validation errors bypass node error handling | Same as above | See above |
| Node works in the UI, fails via API | Body had a read-only field | `400 request/body must NOT have additional properties` | Strip `active, activeVersionId, versionId, isArchived, triggerCount, pinData, meta, tags, shared, activeVersion` |
| `PUT` succeeds but nothing changes at runtime | Change saved as draft, or an old version is published | `activeVersionId` vs `GET /workflows/{id}/versions` | Publish explicitly |
| Credentials disappear after `PUT` | Embedded credential `name` did not match the stored name exactly | Node comes back with `credentials: null` | Read the exact name from another workflow; re-read after `PUT` |
| Retry settings vanish from a scripted workflow | Build script filtered node keys against an incomplete allow-list | `retryOnFail`, `maxTries` absent in the readback | Use the documented node field list |
| Data Table update reports success but changed nothing | Filter matched 0 rows; `update` emits 0 items and `alwaysOutputData` hides it | Row count before/after | Assert the match count, not the node status |

## Executions and observability

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| Successful runs never appear in `GET /executions` | `settings.saveDataSuccessExecution: "none"` | The workflow's `settings` | Set `all` while debugging; remember to revert |
| `KeyError`/missing field reading execution detail | Payload shape differs per build (top level vs. under `data`) | Dump the response keys | Read defensively |
| Tool shows 0 items but clearly answered | Sub-node output lives in `data.ai_tool`, not `data.main` | Keys present in `data` | Read the channel that matches the connection type |
| Error workflow never fires | Not published, or the run was manual | Error workflow's `activeVersionId`; target execution `mode` | Publish it; test with a webhook "test bomb" |
| Error ticket contains an empty description | Handler still reads `$json.error.*` instead of `$json.execution.error.*` | The handler's expressions | Update to `execution.error.{message,stack}` |
| Execution stopped at a node that "looks fine" | Node was disabled | `disabled` on the node | Re-enable, or accept the skip |

## Access and credentials

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| `GET /credentials` answers 403 but writes work | Key scopes differ per operation | Try `POST /credentials` | Read credential names from workflows instead |
| `POST /credentials` rejects field names | Wrong names for that credential type | `GET /credentials/schema/<type>` | Use the schema's property names |
| `SSL Issue: consider using the 'Ignore SSL issues' option` | Certificate serves a different name — the API usually moved or the vendor is in maintenance | Error `description` with the host; `curl -sk -D -` on a nonsense path | Do not toggle ignore-SSL; check the vendor's status page first |
| OAuth node cannot use password grant | n8n `oAuth2Api` supports `authorizationCode`, `clientCredentials`, `pkce` only | Token request in the execution | Keep a password-grant token in an HTTP node, or use header auth |

## AI nodes

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| Agent answers "I got no data" while upstream is filled | Prompt field lacks `=` or `promptType` is `auto` behind a non-chat trigger | `parameters.promptType`, `parameters.text` | `define` + `={{ ... }}` |
| "Error in sub-node Simple Memory" | Memory `sessionKey` points at a node that does not exist in this workflow, or resolves to `undefined` | The memory node's `sessionKey` expression | Point it at the trigger's session/chat id |
| Agent ignores a tool | Tool lost its `ai_tool` connection during a `PUT` | `connections` keys | Re-attach and verify the readback |
| Tool call fails with `Received tool input did not match expected schema` | Every `$fromAI()` parameter is required, including "optional" ones | Tool schema in `tools/list` | Make "leave empty" the documented way to mean "all" |
| Model invents timestamps or session ids | Those values were exposed as `$fromAI()` fields | Written rows | Bind time/ids to `$now` and trigger fields |
| Workflow with two triggers behaves differently per trigger | Webhook nests the body under `$json.body`, Execute Workflow Trigger does not | The first node's output | Normalise once (`const src = j.body ?? j`) |
| Agent burns rounds calling a fetch tool it did not need | The same feed is already fetched deterministically earlier in the chain | `ai_tool` runs per round | Remove the redundant tool |
