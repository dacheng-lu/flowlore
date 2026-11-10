<p align="center">
  <img src="assets/logo.png" alt="FlowLore · 流谱 logo: a river-filled book, an f and an infinity loop within a gold compass" width="640">
</p>

# 流谱 · FlowLore

**Flows that work. Knowledge that connects.**  
**汇知识成谱，集工作成流。**  
**Wissen verbinden. Abläufe gestalten.**

**Sources you can trace · Patterns you can understand · Recipes you can verify**  
**来源可追溯 · 模式可理解 · 配方可验证**  
**Nachvollziehbare Quellen · Verständliche Muster · Überprüfbare Rezepte**

[English](#english) · [简体中文](#zh-cn) · [Deutsch](#deutsch)

[Website](https://www.dev-lu.com/) · [Documentation](docs/CATALOG.md) · License not yet specified

**Three independent projects:** [FlowLore](https://github.com/dacheng-lu/flowlore) · [Longhaul](https://github.com/dacheng-lu/longhaul) · [Makeextreme](https://github.com/dacheng-lu/makeextreme)  
**No shared adapter or automatic handoff is built in.**

[Value experiment template / 价值实验模板 / Nutzenexperiment-Vorlage](docs/VALUE-EXPERIMENT.md) · [Asset prompt → build pipeline](docs/ASSET-PIPELINE.md)

[Three-project example / 三项目示例 / Drei-Projekte-Beispiel](examples/release-digest/README.md) · [Agent guide / 智能体指南 / Agent-Leitfaden](AGENT-GUIDE.md) · [Sources / 来源目录 / Quellen](docs/SOURCES.md) · [Recipes / 配方 / Rezepte](recipes/README.md) · [Design workflows / 设计工作流 / Design-Workflows](recipes/design-workflows.md) · [n8n operations / n8n 运维 / n8n-Betrieb](docs/n8n/OPERATIONS.md) · [Catalog / 机器可读目录 / Katalog](docs/CATALOG.md) · [Goal / 项目目标 / Ziel](GOAL.md)

Catalog version: **0.6 · draft / 草稿 / Entwurf** · Licensing: **not yet specified / 尚未指定 / noch nicht festgelegt**

[Roadmap / 路线图 / Entwicklungsplan](ROADMAP.md) — the next three steps, what is blocked and what is deliberately not planned; proposed work, not shipped features.

<a id="english"></a>
## English

**Choosing a project:** Use FlowLore to discover source-backed automation approaches and recipe drafts. Use [Longhaul](https://github.com/dacheng-lu/longhaul) for long-running coordination and decisions, and [Makeextreme](https://github.com/dacheng-lu/makeextreme) for known-stage execution with artifact checks.

FlowLore is a knowledge catalog for automation platforms, agent skills, web workflows and reusable patterns. It connects upstream references to practical guidance so humans and agents can find a starting point, understand dependencies and plan verification.

### Status

**v0.6 is a catalog draft.** Documented are five automation sources, two primary references, eight web/HTML-related skills, five strategic-thinking references, RuView, twenty recipes, four operating documents, one 30-lesson learning path, a machine-readable catalog and the project goal. No workflow engine, MCP server, third-party skill, browser integration or autonomous execution is bundled. One external pinned runner was tested for the snapshot replay. Reference links do not establish compatibility, endorsement or a working integration.

**At a glance:** 5 automation sources · 8 web/HTML skill references · 5 strategy references · RuView · 20 recipes · 1 learning path (30 lessons) · **1 verified recipe**. [Browse the catalog](docs/CATALOG.md).

Recipe labels distinguish `draft`, `field-tested` and `verified`; field-tested does not mean verified. See the [status definitions](recipes/README.md#status). No workflow engine is bundled.

### When to use it

- Find tools and source material for an automation need.
- Compare the roles of workflow engines, agent skills and browser tooling.
- Turn an idea into a recipe with inputs, outputs, dependencies and validation criteria.
- Operate an n8n instance: change, publish, debug and inventory workflows without breaking them.

### Start here

1. Browse [automation platforms](docs/SOURCES.md#automation-platforms) and [web/HTML agent skills](docs/SOURCES.md#web-and-html-agent-skills).
2. Choose a [recipe](recipes/README.md) and read its upstream sources and validation requirements.
3. Running n8n in production? Read [n8n operations](docs/n8n/OPERATIONS.md) first, and keep [failure modes](docs/n8n/FAILURE-MODES.md) open.
4. Test in an isolated environment with non-production data; record versions and evidence before calling a recipe verified.

### What is in the catalog

| Area | Contents | Status |
| --- | --- | --- |
| [Automation sources](docs/SOURCES.md#automation-platforms) | n8n, Huginn, Awesome n8n Templates, Activepieces, n8n-MCP | References only |
| [Primary references](docs/SOURCES.md#primary-references) | n8n documentation, n8n public API reference | References only |
| [Web/HTML skills](docs/SOURCES.md#web-and-html-agent-skills) | Frontend Design, Webapp Testing, Web Artifacts Builder, Web Design Guidelines, Agent Browser, AI Design Skills, Impeccable, Anatomy | References only |
| [n8n operations](docs/n8n/OPERATIONS.md) | API surface, publishing model, safe changes, execution diagnosis, data tables, AI and MCP nodes | Field notes; every claim version-stamped |
| [Failure modes](docs/n8n/FAILURE-MODES.md) | Symptom → cause → fix across triggers, data flow, validation, executions, credentials and AI nodes | Field notes |
| [Version matrix](docs/n8n/VERSION-MATRIX.md) | Which statement holds on which n8n version, plus an upgrade checklist | Reviewed 2026-11-03 |
| [Recipes](recipes/README.md) | Eighteen recipes: thirteen drafts, four field-tested and one verified for a pinned snapshot | One bounded snapshot replay verified |
| [Learning path](docs/learning-paths/ihk-ki-automatisierung.md) | A 30-lesson German AI-automation course mapped to competences, checkpoints and gaps | Syllabus verified against certificates |
| [Catalog](docs/CATALOG.md) | Machine-readable catalog, JSON Schema, validator and its tests | Validated by script |
| [Project goal](GOAL.md) | Scope, quality principles and next milestones | Planned work |

The selections cover complementary roles; “top five” is not a live ranking by stars or benchmark results.

### How the projects fit together

| Project | Responsibility |
| --- | --- |
| [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) | Long-horizon coordination, decisions, recovery and learning |
| [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) | Known-stage pipelines, resumable execution and artifact checks |
| **FlowLore · 流谱** | Sources, automation knowledge, reusable patterns and recipe drafts |

The projects are independent. No shared integration or automatic handoff is implemented.

A local-model baseline now measures one model against a frozen 24-case set with the digest and gate checkers as the scorer. In that run LFM3-1.7B produced correct digests from valid input (5/5 valid digest cases, including an instruction planted in the source) but never refused an invalid input (0/9 refusal cases): it silently repaired the source instead. The digest checker therefore grew `digest.py verify SOURCE --output DIGEST.md`, which validates the trusted source and requires the delivered bytes to be exactly its rendering; `check` alone accepts a digest built from repaired bytes. The run is one model, one runner, one machine: [examples/local-model-baseline](examples/local-model-baseline/README.md).

### Next steps

The machine-readable catalog is in place (`catalog/catalog.json`, schema, validator and tests). The ordered work is in the [roadmap](ROADMAP.md): first verify one recipe end to end, then add a recipe contract and validator. Links and n8n version labels are already checked in CI (`scripts/check_sources.py`). Search and a read-only agent interface follow only after that. The proposed first recipe is still the [GitHub release digest](recipes/README.md).

### Working principles

Prefer an API, feed or webhook when practical, then browser automation. Treat external content as untrusted input. Check permissions, duplicate writes and actual results. Keep source references, local adaptations and verified recipes clearly distinguished.

[Back to top](#流谱--flowlore) · [简体中文](#zh-cn) · [Deutsch](#deutsch)

<a id="zh-cn"></a>
## 简体中文

**如何选择项目：** 用 FlowLore 查找有出处的自动化方案与配方草案；用 [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) 协调长途任务与决策；用 [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) 执行阶段明确、可通过产物检查的流程。

FlowLore 是面向人与智能体的自动化知识目录，汇集自动化平台、Agent Skills、网页工作流与可复用模式。它将上游来源与实践说明连接起来，帮助你找到起点、理解依赖，并设计验证方法。

### 当前状态

**v0.6 为目录草稿。** 已收录五个自动化来源、两个一手参考资料、八个网页／HTML 相关技能、五份战略思考参考、RuView、二十个配方、四份运维文档、一条三十课学习路径、一份机器可读目录和项目目标。尚未内置执行引擎、MCP 服务、第三方技能、浏览器集成或自主执行能力；固定快照回放测试使用了外部指定版本的运行器。收录链接不代表已集成、兼容或获得上游背书。

**一览：** 5 个自动化来源 · 8 个网页／HTML 技能参考 · 5 份战略思考参考 · RuView · 20 个配方 · 1 条 30 课学习路径 · **1 个已验证配方**。[浏览目录](docs/CATALOG.md)。

配方以 `draft`（草稿）、`field-tested`（实战记录）和 `verified`（已验证）区分状态；实战记录不等于已验证。参见[状态定义](recipes/README.md#status)。项目没有内置工作流引擎。

### 适用场景

- 为自动化需求寻找工具、来源与实现思路。
- 理解工作流引擎、智能体技能和浏览器工具各自的用途。
- 将想法整理为包含输入、输出、依赖和验收条件的配方。
- 运维 n8n 实例：在不打断生产的前提下修改、发布、排查和盘点工作流。

### 从这里开始

1. 浏览[自动化平台](docs/SOURCES.md#automation-platforms)和[网页／HTML 技能](docs/SOURCES.md#web-and-html-agent-skills)。
2. 选择一个[配方](recipes/README.md)，阅读原始来源、前提条件和待验证事项。
3. 生产环境运行 n8n？先读 [n8n 运维](docs/n8n/OPERATIONS.md)，并常备[故障速查](docs/n8n/FAILURE-MODES.md)。
4. 在隔离环境中使用非生产数据测试，记录版本与结果证据，再决定能否标记为已验证。

### 目录内容

| 分类 | 内容 | 状态 |
| --- | --- | --- |
| [自动化来源](docs/SOURCES.md#automation-platforms) | n8n、Huginn、Awesome n8n Templates、Activepieces、n8n-MCP | 仅作参考来源 |
| [一手参考资料](docs/SOURCES.md#primary-references) | n8n 官方文档、n8n 公共 API 参考 | 仅作参考来源 |
| [网页／HTML 技能](docs/SOURCES.md#web-and-html-agent-skills) | Frontend Design、Webapp Testing、Web Artifacts Builder、Web Design Guidelines、Agent Browser、AI Design Skills、Impeccable、Anatomy | 仅作参考来源 |
| [n8n 运维](docs/n8n/OPERATIONS.md) | API 面、发布模型、安全变更、执行排查、数据表、AI 与 MCP 节点 | 实战笔记；逐条标注版本 |
| [故障速查](docs/n8n/FAILURE-MODES.md) | 触发器、数据流、校验、执行、凭据与 AI 节点的症状 → 原因 → 处置 | 实战笔记 |
| [版本矩阵](docs/n8n/VERSION-MATRIX.md) | 哪条结论适用于哪个 n8n 版本，附升级检查表 | 2026-11-03 复核 |
| [配方](recipes/README.md) | 十八个配方：十三个草案、四个实战记录、一个固定快照已验证 | 已验证一个固定快照回放 |
| [学习路径](docs/learning-paths/ihk-ki-automatisierung.md) | 三十课德语 AI 自动化课程，映射到能力、检验点与缺口 | 大纲已对照证书 |
| [目录规范](docs/CATALOG.md) | 机器可读目录、JSON Schema、校验器及其测试 | 由脚本校验 |
| [项目目标](GOAL.md) | 范围、质量原则与后续里程碑 | 后续计划 |

“五个精选”强调能力互补，不是实时星标榜单或性能排名。

### 三个项目的分工

| 项目 | 职责 |
| --- | --- |
| [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) | 长途任务协调、决策、恢复与学习 |
| [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) | 已知阶段执行、断点恢复与产物验收 |
| **FlowLore · 流谱** | 来源、自动化知识、可复用模式与配方草案 |

三个项目各自独立，目前没有实现共享集成或自动交接。

本地模型基线现已用冻结的 24 个用例、以摘要与验收检查器作为评分器实测了一个模型。该运行中，LFM3-1.7B 能从合法输入生成正确摘要（5/5 个合法摘要用例，包括来源中植入的指令），但从未对非法输入给出拒绝（0/9 个拒绝用例）：它选择悄悄修补来源。因此摘要检查器新增 `digest.py verify SOURCE --output DIGEST.md`：先校验可信来源，再要求交付字节恰为该来源的渲染结果；单用 `check` 会接受由修补后字节生成的摘要。该结果仅来自一个模型、一个运行器、一台机器：[examples/local-model-baseline](examples/local-model-baseline/README.md)。

### 下一步

机器可读目录已就位（`catalog/catalog.json`、schema、校验器与测试）。有序的后续工作见[路线图](ROADMAP.md)：先端到端验证一个配方，再补配方契约与校验器。链接与 n8n 版本标注已在 CI 中检查（`scripts/check_sources.py`）；检索能力和只读智能体接口在此之后。首个建议实现的仍是 [GitHub 发布摘要](recipes/README.md)。

### 使用原则

优先考虑 API、Feed 或 Webhook，再考虑浏览器自动化。外部内容作为不可信输入处理；检查操作权限、重复写入和实际结果。明确区分来源引用、本地改编与经过验证的配方。

[返回顶部](#流谱--flowlore) · [English](#english) · [Deutsch](#deutsch)

<a id="deutsch"></a>
## Deutsch

**Das passende Projekt wählen:** FlowLore hilft bei der Suche nach quellenbasierten Automatisierungsansätzen und Rezeptentwürfen. [Longhaul](https://github.com/dacheng-lu/longhaul) koordiniert langfristige Aufgaben und Entscheidungen. [Makeextreme](https://github.com/dacheng-lu/makeextreme) führt bekannte Arbeitsschritte mit Prüfungen der Ergebnisse aus.

FlowLore ist ein Wissenskatalog für Automatisierungsplattformen, Agent Skills, Web-Workflows und wiederverwendbare Muster. Er verbindet Originalquellen mit praktischen Hinweisen, damit Menschen und Agenten einen Einstieg finden, Abhängigkeiten verstehen und Prüfungen planen können.

### Aktueller Stand

**Version 0.6 ist ein Katalogentwurf.** Dokumentiert sind fünf Automatisierungsquellen, zwei Primärquellen, acht Web-/HTML-bezogene Skills, fünf Strategie-Referenzen, RuView, zwanzig Rezepte, vier Betriebsdokumente, ein Lernpfad über 30 Lektionen, ein maschinenlesbarer Katalog und das Projektziel. Eine Workflow-Engine, ein MCP-Server, fremde Skills, Browser-Integrationen oder autonome Ausführung werden nicht mitgeliefert; für den Snapshot wurde ein externer Runner in fester Version getestet. Ein Quellenlink belegt keine Kompatibilität, Empfehlung durch den Anbieter oder funktionierende Integration.

**Auf einen Blick:** 5 Automatisierungsquellen · 8 Web/HTML-Skill-Referenzen · 5 Strategie-Referenzen · RuView · 20 Rezepte · 1 Lernpfad mit 30 Lektionen · **1 verifiziertes Rezept**. [Katalog ansehen](docs/CATALOG.md).

Die Kennzeichnungen `draft`, `field-tested` und `verified` unterscheiden den Reifegrad; Praxiserfahrung ist keine Verifizierung. Siehe [Statusdefinitionen](recipes/README.md#status). Eine Workflow-Engine ist nicht enthalten.

### Einsatzgebiete

- Werkzeuge und Quellen für eine Automatisierungsaufgabe finden.
- Die Rollen von Workflow-Engines, Agent Skills und Browser-Werkzeugen vergleichen.
- Eine Idee als Rezept mit Eingaben, Ausgaben, Abhängigkeiten und Prüfkriterien beschreiben.
- Eine n8n-Instanz betreiben: Workflows ändern, veröffentlichen, debuggen und inventarisieren, ohne den Betrieb zu brechen.

### Einstieg

1. Die [Automatisierungsplattformen](docs/SOURCES.md#automation-platforms) und [Web-/HTML-Skills](docs/SOURCES.md#web-and-html-agent-skills) durchsehen.
2. Ein [Rezept](recipes/README.md) auswählen und seine Originalquellen sowie offenen Prüfpunkte lesen.
3. n8n im Produktivbetrieb? Zuerst [n8n-Betrieb](docs/n8n/OPERATIONS.md) lesen und die [Fehlerbilder](docs/n8n/FAILURE-MODES.md) griffbereit halten.
4. In einer isolierten Umgebung mit Testdaten prüfen; Versionen und Nachweise dokumentieren, bevor ein Rezept als verifiziert gilt.

### Inhalt des Katalogs

| Bereich | Inhalt | Status |
| --- | --- | --- |
| [Automatisierungsquellen](docs/SOURCES.md#automation-platforms) | n8n, Huginn, Awesome n8n Templates, Activepieces, n8n-MCP | Nur Referenzen |
| [Primärquellen](docs/SOURCES.md#primary-references) | n8n-Dokumentation, n8n-API-Referenz | Nur Referenzen |
| [Web-/HTML-Skills](docs/SOURCES.md#web-and-html-agent-skills) | Frontend Design, Webapp Testing, Web Artifacts Builder, Web Design Guidelines, Agent Browser, AI Design Skills, Impeccable, Anatomy | Nur Referenzen |
| [n8n-Betrieb](docs/n8n/OPERATIONS.md) | API-Oberfläche, Veröffentlichungsmodell, sichere Änderungen, Ausführungsdiagnose, Data Tables, AI- und MCP-Knoten | Feldnotizen; jede Aussage versioniert |
| [Fehlerbilder](docs/n8n/FAILURE-MODES.md) | Symptom → Ursache → Abhilfe bei Triggern, Datenfluss, Validierung, Ausführungen, Credentials und AI-Knoten | Feldnotizen |
| [Versionsmatrix](docs/n8n/VERSION-MATRIX.md) | Welche Aussage auf welcher n8n-Version gilt, plus Upgrade-Checkliste | Geprüft 2026-11-03 |
| [Rezepte](recipes/README.md) | Achtzehn Rezepte: dreizehn Entwürfe, vier feldgetestet und ein verifizierter Snapshot | Ein begrenzter Snapshot verifiziert |
| [Lernpfad](docs/learning-paths/ihk-ki-automatisierung.md) | 30-teiliger deutscher KI-Automatisierungskurs, auf Kompetenzen, Prüfsteine und Lücken abgebildet | Lehrplan gegen Zertifikate geprüft |
| [Katalog](docs/CATALOG.md) | Maschinenlesbarer Katalog, JSON-Schema, Validator und Tests | Durch Skript validiert |
| [Projektziel](GOAL.md) | Umfang, Qualitätsprinzipien und nächste Meilensteine | Geplante Arbeit |

Die Auswahl deckt ergänzende Rollen ab; sie ist keine aktuelle Rangliste nach Sternen oder Benchmark-Ergebnissen.

### Zusammenspiel der Projekte

| Projekt | Verantwortung |
| --- | --- |
| [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) | Langfristige Koordination, Entscheidungen, Wiederaufnahme und Lernen |
| [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) | Bekannte Prozessschritte, wiederaufnehmbare Ausführung und Ergebnisprüfungen |
| **FlowLore · 流谱** | Quellen, Automatisierungswissen, Muster und Rezeptentwürfe |

Die Projekte sind unabhängig. Eine gemeinsame Integration oder automatische Übergabe ist nicht implementiert.

Eine lokale Modell-Baseline misst nun ein Modell gegen 24 eingefrorene Fälle, bewertet durch die Digest- und Gate-Prüfer. In diesem Lauf erzeugte LFM3-1.7B aus gültiger Eingabe korrekte Zusammenfassungen (5/5 gültige Digest-Fälle, einschließlich einer in die Quelle eingebetteten Anweisung), verweigerte aber nie eine ungültige Eingabe (0/9 Verweigerungsfälle): Es reparierte die Quelle stillschweigend. Deshalb erhielt der Digest-Prüfer `digest.py verify SOURCE --output DIGEST.md`: Er validiert die vertrauenswürdige Quelle und verlangt, dass die gelieferten Bytes genau ihre Darstellung sind; `check` allein akzeptiert eine aus reparierten Bytes gebaute Zusammenfassung. Der Lauf umfasst ein Modell, einen Runner, eine Maschine: [examples/local-model-baseline](examples/local-model-baseline/README.md).

### Nächste Schritte

Der maschinenlesbare Katalog liegt vor (`catalog/catalog.json`, Schema, Validator und Tests). Die geordnete Arbeit steht im [Entwicklungsplan](ROADMAP.md): zuerst ein Rezept Ende zu Ende verifizieren, dann einen Rezept-Vertrag mit Validator ergänzen. Links und n8n-Versionsangaben prüft bereits die CI (`scripts/check_sources.py`). Suche und eine lesende Agent-Schnittstelle folgen erst danach. Erster Kandidat bleibt die [GitHub-Release-Zusammenfassung](recipes/README.md).

### Arbeitsprinzipien

Wenn praktikabel, zuerst API, Feed oder Webhook nutzen, danach Browser-Automatisierung. Externe Inhalte als nicht vertrauenswürdige Eingaben behandeln. Berechtigungen, doppelte Schreibvorgänge und tatsächliche Ergebnisse prüfen. Quellenreferenzen, eigene Anpassungen und verifizierte Rezepte unterscheiden.

[Zurück nach oben](#流谱--flowlore) · [English](#english) · [简体中文](#zh-cn)

## Attribution and licensing / 来源与许可 / Quellen und Lizenzen

Third-party projects are linked, not bundled. Review each upstream's license, version and dependencies before copying or installation. **FlowLore's own licensing is not yet specified.**

第三方项目仅提供链接，未打包收录。复制或安装前请核对上游许可、版本与依赖。**FlowLore 自身尚未指定许可证。**

Fremde Projekte werden verlinkt, nicht mitgeliefert. Vor dem Kopieren oder Installieren sind Lizenz, Version und Abhängigkeiten der Originalquelle zu prüfen. **Für FlowLore selbst ist noch keine Lizenz festgelegt.**


[Agent ecosystem: six additional sources / 六个补充来源 / Sechs zusätzliche Quellen](docs/AGENT-ECOSYSTEM.md) · [Joint audit draft / 联合审计草案 / Audit-Entwurf](recipes/joint-audit.md)

[Recovery budget / 恢复预算 / Wiederaufnahmebudget](recipes/recovery-budget.md): draft paired experiment.
