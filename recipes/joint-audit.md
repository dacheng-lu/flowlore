# Joint audit records

Status: **draft**. The synthetic offline example tests record plumbing; it does
not verify a real vulnerability audit or justify marking this recipe verified.

Inputs: a reviewed checkout with fixed base/head commits, a coverage plan,
findings with three-state verdicts and local hashed evidence.
Outputs: validated record snapshot, derived report and explicit handoff.

1. Read [source choices and pinned revisions](../docs/AGENT-ECOSYSTEM.md).
2. In Longhaul, set scope, unresolved questions and separate acceptance criteria
   for coverage, record consistency and finding impact.
3. Gather and independently review evidence. Use the upstream Cloudflare workflow
   only when its sandbox/tool prerequisites hold. Otherwise retain unresolved leads.
4. Run Makeextreme's `examples/audit_ladder/records/new_task.py BUNDLE TASK`, then
   `python -m makeextreme run TASK`. This local format is not Cloudflare's schema.
5. Prepare the Longhaul `docs/audit-handoff.md` record; run its checker against the
   expected source head. Review semantic findings before checkpoint acceptance.
6. Publish versions, checks, failures and limitations. Do not infer a clean audit
   from a green schema check or from an empty findings list.

## Reproduce the offline integration

With sibling checkouts pinned to these tested implementation commits:

- Makeextreme: `1c827786c2632a782969882d357a031e784f6d08`
- Longhaul: `33226119dbaec9c0432911e25389a451af9ad83d`

```bash
cd makeextreme
python examples/audit_ladder/records/demo.py --longhaul ../longhaul
```

Expected: validate starts once, interrupted report starts twice, handoff passes,
report drift is rejected then repaired, source drift is rejected. The example
uses synthetic commit IDs and evidence, local temporary files and no model calls.
The example implementation lives in Makeextreme; do not copy the runner into this
catalog. Revalidate any later merged revisions before promoting this recipe.

Remaining validation: real-model effectiveness, reviewer independence, sandbox
boundary, durable cross-session recovery and public evidence review. OpenMausBot,
billion-context and Google deployment are optional future experiments, not part
of this fixture. No workflow engine or third-party skill is bundled here.
