# Agent ecosystem sources

Reviewed 2026-11-08. Reference-only candidates, not installed integrations.
Pinned revisions identify the proposed evaluation inputs, not compatibility proof.

| Source | Revision | Role and limits |
| --- | --- | --- |
| [milind-soni/OpenMausBot](https://github.com/milind-soni/OpenMausBot) | [d7ce39ea08e2](https://github.com/milind-soni/OpenMausBot/tree/d7ce39ea08e23bf39d6ec0496f9fef39edcd77ad) | Optional host; MCP task dispatch, bounded waiting and idempotent send IDs. Platform compatibility untested. |
| [ranxianglei/billion-context](https://github.com/ranxianglei/billion-context) | [354e21e23af4](https://github.com/ranxianglei/billion-context/tree/354e21e23af4f5dc10166c94c47f09f1e514899d) | Optional context experiment; compression does not replace durable checkpoints. License includes an additional attribution term. |
| [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) | [c1c8a8c14710](https://github.com/cloudflare/security-audit-skill/tree/c1c8a8c1471069fb0e188eeaff69b8e8db6564a8) | Audit methodology; Node validators and an OS-enforced sandbox required for the full upstream workflow. |
| [google/skills](https://github.com/google/skills) | [2194d3b8b1f3](https://github.com/google/skills/tree/2194d3b8b1f31975fef2f1a0ae6b9ab55bd7ceee) | Google product recipes; select per cloud task and inspect permissions, cost and prerequisites. |
| [anthropics/skills](https://github.com/anthropics/skills) | [2c5958ecac7c](https://github.com/anthropics/skills/tree/2c5958ecac7cee2b583967a2c4981d0f4a75c579) | Specialist skills and comparative skill evaluation; test host dependencies before use. |
| [mattpocock/skills](https://github.com/mattpocock/skills) | [4ae2317ddb22](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d) | Engineering methods: diagnosis, domain modeling, TDD and review. Keep one task orchestrator. |

Do not install all sources globally. Use task-specific selections, preserve upstream
licenses, and distinguish referenced methods from copied code and tested adapters.
Longhaul retains lifecycle ownership; Makeextreme retains deterministic execution;
FlowLore records provenance and recipe status. Existing Anthropic skill entries
remain individual entries; the new source entry describes the overall collection.
