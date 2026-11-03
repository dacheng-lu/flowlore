<p align="center">
  <img src="assets/logo.png" alt="FlowLore · 流谱 logo: a river-filled book, an f and an infinity loop within a gold compass" width="640">
</p>

# 流谱 · FlowLore

**Flows that work. Knowledge that connects.**  
**汇知识成谱，让工作成流。**  
**Wissen verbinden. Abläufe gestalten.**

**Sources you can trace · Patterns you can understand · Recipes you can verify**  
**来源可追溯 · 模式可理解 · 配方可验证**  
**Nachvollziehbare Quellen · Verständliche Muster · Überprüfbare Rezepte**

[English](#english) · [简体中文](#zh-cn) · [Deutsch](#deutsch)

[Sources / 来源目录 / Quellen](docs/SOURCES.md) · [Recipes / 配方草案 / Rezeptentwürfe](recipes/README.md) · [Goal / 项目目标 / Ziel](GOAL.md)

Catalog version: **0.1 · draft / 草稿 / Entwurf** · Licensing: **not yet specified / 尚未指定 / noch nicht festgelegt**

<a id="english"></a>
## English

**Choosing a project:** Use FlowLore to discover source-backed automation approaches and recipe drafts. Use [Longhaul](https://github.com/dacheng-lu/longhaul) for long-running coordination and decisions, and [Makeextreme](https://github.com/dacheng-lu/makeextreme) for known-stage execution with artifact checks.

FlowLore is a knowledge catalog for automation platforms, agent skills, web workflows and reusable patterns. It connects upstream references to practical guidance so humans and agents can find a starting point, understand dependencies and plan verification.

### Status

**v0.1 is a catalog draft.** Five automation sources, five web/HTML-related skills, five recipe drafts and a project goal are documented. No workflow engine, MCP server, third-party skill, browser integration or autonomous execution is bundled or tested. Reference links do not establish compatibility, endorsement or a working integration.

### When to use it

- Find tools and source material for an automation need.
- Compare the roles of workflow engines, agent skills and browser tooling.
- Turn an idea into a recipe with inputs, outputs, dependencies and validation criteria.

### Start here

1. Browse [automation platforms](docs/SOURCES.md#automation-platforms) and [web/HTML agent skills](docs/SOURCES.md#web-and-html-agent-skills).
2. Choose a [recipe draft](recipes/README.md) and read its upstream sources and validation requirements.
3. Test in an isolated environment with non-production data; record versions and evidence before calling a recipe verified.

### What is in the catalog

| Area | Contents | Status |
| --- | --- | --- |
| [Automation sources](docs/SOURCES.md#automation-platforms) | n8n, Huginn, Awesome n8n Templates, Activepieces, n8n-MCP | References only |
| [Web/HTML skills](docs/SOURCES.md#web-and-html-agent-skills) | Frontend Design, Webapp Testing, Web Artifacts Builder, Web Design Guidelines, Agent Browser | References only |
| [Recipe drafts](recipes/README.md) | Release digest, web change monitor, HTML report, workflow authoring, file classification | All draft; not verified |
| [Project goal](GOAL.md) | Scope, quality principles and next milestones | Planned work |

The selections cover complementary roles; “top five” is not a live ranking by stars or benchmark results.

### How the projects fit together

| Project | Responsibility |
| --- | --- |
| [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) | Long-horizon coordination, decisions, recovery and learning |
| [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) | Known-stage pipelines, resumable execution and artifact checks |
| **FlowLore · 流谱** | Sources, automation knowledge, reusable patterns and recipe drafts |

The projects are independent. No shared integration or automatic handoff is implemented.

### Next steps

The [roadmap in GOAL.md](GOAL.md#next-milestones) starts with a machine-readable catalog, then one reproducibly tested recipe, search and evaluation of a read-only agent interface. The proposed first recipe is a [GitHub release digest](recipes/README.md).

### Working principles

Prefer an API, feed or webhook when practical, then browser automation. Treat external content as untrusted input. Check permissions, duplicate writes and actual results. Keep source references, local adaptations and verified recipes clearly distinguished.

[Back to top](#流谱--flowlore) · [简体中文](#zh-cn) · [Deutsch](#deutsch)

<a id="zh-cn"></a>
## 简体中文

**如何选择项目：** 用 FlowLore 查找有出处的自动化方案与配方草案；用 [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) 协调长途任务与决策；用 [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) 执行阶段明确、可通过产物检查的流程。

FlowLore 是面向人与智能体的自动化知识目录，汇集自动化平台、Agent Skills、网页工作流与可复用模式。它将上游来源与实践说明连接起来，帮助你找到起点、理解依赖，并设计验证方法。

### 当前状态

**v0.1 为目录草稿。** 已收录五个自动化来源、五个网页／HTML 相关技能、五个配方草案和项目目标。尚未内置或验证执行引擎、MCP 服务、第三方技能、浏览器集成或自主执行能力。收录链接不代表已集成、兼容或获得上游背书。

### 适用场景

- 为自动化需求寻找工具、来源与实现思路。
- 理解工作流引擎、智能体技能和浏览器工具各自的用途。
- 将想法整理为包含输入、输出、依赖和验收条件的配方。

### 从这里开始

1. 浏览[自动化平台](docs/SOURCES.md#automation-platforms)和[网页／HTML 技能](docs/SOURCES.md#web-and-html-agent-skills)。
2. 选择一个[配方草案](recipes/README.md)，阅读原始来源、前提条件和待验证事项。
3. 在隔离环境中使用非生产数据测试，记录版本与结果证据，再决定能否标记为已验证。

### 目录内容

| 分类 | 内容 | 状态 |
| --- | --- | --- |
| [自动化来源](docs/SOURCES.md#automation-platforms) | n8n、Huginn、Awesome n8n Templates、Activepieces、n8n-MCP | 仅作参考来源 |
| [网页／HTML 技能](docs/SOURCES.md#web-and-html-agent-skills) | Frontend Design、Webapp Testing、Web Artifacts Builder、Web Design Guidelines、Agent Browser | 仅作参考来源 |
| [配方草案](recipes/README.md) | 发布摘要、网页变更监控、HTML 报告、工作流编写助手、文件分类 | 均为草案，尚未验证 |
| [项目目标](GOAL.md) | 范围、质量原则与后续里程碑 | 后续计划 |

“五个精选”强调能力互补，不是实时星标榜单或性能排名。

### 三个项目的分工

| 项目 | 职责 |
| --- | --- |
| [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) | 长途任务协调、决策、恢复与学习 |
| [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) | 已知阶段执行、断点恢复与产物验收 |
| **FlowLore · 流谱** | 来源、自动化知识、可复用模式与配方草案 |

三个项目各自独立，目前没有实现共享集成或自动交接。

### 下一步

按照 [GOAL.md](GOAL.md#next-milestones)，依次推进机器可读目录、一个可复现验证的配方、检索能力，以及只读智能体接口的评估。首个建议实现的是 [GitHub 发布摘要](recipes/README.md)。

### 使用原则

优先考虑 API、Feed 或 Webhook，再考虑浏览器自动化。外部内容作为不可信输入处理；检查操作权限、重复写入和实际结果。明确区分来源引用、本地改编与经过验证的配方。

[返回顶部](#流谱--flowlore) · [English](#english) · [Deutsch](#deutsch)

<a id="deutsch"></a>
## Deutsch

**Das passende Projekt wählen:** FlowLore hilft bei der Suche nach quellenbasierten Automatisierungsansätzen und Rezeptentwürfen. [Longhaul](https://github.com/dacheng-lu/longhaul) koordiniert langfristige Aufgaben und Entscheidungen. [Makeextreme](https://github.com/dacheng-lu/makeextreme) führt bekannte Arbeitsschritte mit Prüfungen der Ergebnisse aus.

FlowLore ist ein Wissenskatalog für Automatisierungsplattformen, Agent Skills, Web-Workflows und wiederverwendbare Muster. Er verbindet Originalquellen mit praktischen Hinweisen, damit Menschen und Agenten einen Einstieg finden, Abhängigkeiten verstehen und Prüfungen planen können.

### Aktueller Stand

**Version 0.1 ist ein Katalogentwurf.** Dokumentiert sind fünf Automatisierungsquellen, fünf Web-/HTML-bezogene Skills, fünf Rezeptentwürfe und das Projektziel. Eine Workflow-Engine, ein MCP-Server, fremde Skills, Browser-Integrationen oder autonome Ausführung sind weder mitgeliefert noch getestet. Ein Quellenlink belegt keine Kompatibilität, Empfehlung durch den Anbieter oder funktionierende Integration.

### Einsatzgebiete

- Werkzeuge und Quellen für eine Automatisierungsaufgabe finden.
- Die Rollen von Workflow-Engines, Agent Skills und Browser-Werkzeugen vergleichen.
- Eine Idee als Rezept mit Eingaben, Ausgaben, Abhängigkeiten und Prüfkriterien beschreiben.

### Einstieg

1. Die [Automatisierungsplattformen](docs/SOURCES.md#automation-platforms) und [Web-/HTML-Skills](docs/SOURCES.md#web-and-html-agent-skills) durchsehen.
2. Einen [Rezeptentwurf](recipes/README.md) auswählen und seine Originalquellen sowie offenen Prüfpunkte lesen.
3. In einer isolierten Umgebung mit Testdaten prüfen; Versionen und Nachweise dokumentieren, bevor ein Rezept als verifiziert gilt.

### Inhalt des Katalogs

| Bereich | Inhalt | Status |
| --- | --- | --- |
| [Automatisierungsquellen](docs/SOURCES.md#automation-platforms) | n8n, Huginn, Awesome n8n Templates, Activepieces, n8n-MCP | Nur Referenzen |
| [Web-/HTML-Skills](docs/SOURCES.md#web-and-html-agent-skills) | Frontend Design, Webapp Testing, Web Artifacts Builder, Web Design Guidelines, Agent Browser | Nur Referenzen |
| [Rezeptentwürfe](recipes/README.md) | Release-Zusammenfassung, Web-Änderungsmonitor, HTML-Bericht, Workflow-Autor, Dateiklassifizierung | Entwürfe; nicht verifiziert |
| [Projektziel](GOAL.md) | Umfang, Qualitätsprinzipien und nächste Meilensteine | Geplante Arbeit |

Die Auswahl deckt ergänzende Rollen ab; sie ist keine aktuelle Rangliste nach Sternen oder Benchmark-Ergebnissen.

### Zusammenspiel der Projekte

| Projekt | Verantwortung |
| --- | --- |
| [Longhaul · 远航](https://github.com/dacheng-lu/longhaul) | Langfristige Koordination, Entscheidungen, Wiederaufnahme und Lernen |
| [Makeextreme · 登峰](https://github.com/dacheng-lu/makeextreme) | Bekannte Prozessschritte, wiederaufnehmbare Ausführung und Ergebnisprüfungen |
| **FlowLore · 流谱** | Quellen, Automatisierungswissen, Muster und Rezeptentwürfe |

Die Projekte sind unabhängig. Eine gemeinsame Integration oder automatische Übergabe ist nicht implementiert.

### Nächste Schritte

Die [Meilensteine in GOAL.md](GOAL.md#next-milestones) beginnen mit einem maschinenlesbaren Katalog und einem reproduzierbar getesteten Rezept. Danach folgen Suche und die Prüfung einer lesenden Agent-Schnittstelle. Als erster Kandidat ist eine [GitHub-Release-Zusammenfassung](recipes/README.md) vorgesehen.

### Arbeitsprinzipien

Wenn praktikabel, zuerst API, Feed oder Webhook nutzen, danach Browser-Automatisierung. Externe Inhalte als nicht vertrauenswürdige Eingaben behandeln. Berechtigungen, doppelte Schreibvorgänge und tatsächliche Ergebnisse prüfen. Quellenreferenzen, eigene Anpassungen und verifizierte Rezepte unterscheiden.

[Zurück nach oben](#流谱--flowlore) · [English](#english) · [简体中文](#zh-cn)

## Attribution and licensing / 来源与许可 / Quellen und Lizenzen

Third-party projects are linked, not bundled. Review each upstream's license, version and dependencies before copying or installation. **FlowLore's own licensing is not yet specified.**

第三方项目仅提供链接，未打包收录。复制或安装前请核对上游许可、版本与依赖。**FlowLore 自身尚未指定许可证。**

Fremde Projekte werden verlinkt, nicht mitgeliefert. Vor dem Kopieren oder Installieren sind Lizenz, Version und Abhängigkeiten der Originalquelle zu prüfen. **Für FlowLore selbst ist noch keine Lizenz festgelegt.**
