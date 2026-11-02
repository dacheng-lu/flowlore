<p align="center"><img src="assets/logo.png" width="360" alt="FlowLore logo: a book containing a flowing network" /></p>

# 流谱 · FlowLore

**Automation knowledge for humans and agents.**  
连接知识、工具与工作流，让自动化方案可以被理解、查找与验证。

[English](#english) · [简体中文](#简体中文) · [Deutsch](#deutsch) · [GOAL](GOAL.md) · [Sources](docs/SOURCES.md)

## English

FlowLore is an early-stage knowledge catalog for automation platforms, agent skills, web workflows and reusable patterns. It connects source links to practical guidance so a person or an agent can find a starting point for a task.

**Status: v0.1 draft.** This repository contains curated references and proposed recipes. No workflow engine, MCP server, third-party skill, browser integration or autonomous execution is bundled or tested. Reference links do not imply endorsement or compatibility.

### Start here

1. Browse [automation sources](docs/SOURCES.md#automation-platforms) and [web/HTML skills](docs/SOURCES.md#web-and-html-agent-skills).
2. Select a [recipe draft](recipes/README.md), check its assumptions, and consult the original source before use.
3. For execution, choose a suitable environment and test with non-production data. Record versions and evidence before treating a recipe as tested.

### How it fits

| Project | Responsibility |
|---|---|
| [Longhaul](https://github.com/dacheng-lu/longhaul) | Long-horizon coordination, decisions and learning |
| [Makeextreme](https://github.com/dacheng-lu/makeextreme) | Execution of known stages and artifact checks |
| FlowLore | Automation and web knowledge, sources, patterns and recipes |

These projects are independent; no shared integration or automatic handoff is implemented.

## 简体中文

FlowLore 汇集自动化平台、Agent Skills、网页操作与可复用工作流的知识，让人和智能体能根据需求找到**有出处的方案**。

**当前为 v0.1 草稿**：已经建立来源目录、网页 Skills 清单、配方草案和目标文档；尚未部署执行引擎、安装第三方技能、建立 MCP 接口或完成端到端工作流测试。

- [五个自动化项目与五个网页相关 Skills](docs/SOURCES.md)
- [配方草案与状态](recipes/README.md)
- [项目目标与路线](GOAL.md)

推荐优先使用 API、Feed 或 Webhook；需要使用网页时，再考虑浏览器自动化。网页内容和第三方模板应作为不可信输入处理；外部操作要检查权限、重复执行和实际结果。

## Deutsch

FlowLore sammelt Quellen, Muster und Rezeptentwürfe für Automatisierung, Agent Skills und Web-Workflows. Die Version 0.1 ist ein Wissenskatalog; sie installiert keine fremden Skills und führt keine Workflows aus. Einstieg: [Quellen](docs/SOURCES.md), [Rezepte](recipes/README.md), [Ziele](GOAL.md).

## Attribution

Third-party projects are linked, not included. Review each upstream's current terms, version and dependencies before installation or copying. FlowLore's own licensing is not yet specified.
