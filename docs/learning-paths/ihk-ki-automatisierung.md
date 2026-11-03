# Lernpfad: KI-Automatisierungsexperte (IHK)

> **English abstract.** This page maps a 30-lesson German online course on AI automation
> (n8n-based) onto this catalog. Only the syllabus — the topic list printed on the
> participant certificates — is reproduced; course videos, slides and exercise solutions are
> not. The mapping, the competence statements and the checkpoints are editorial work.

**Status:** Lehrplan gegen zehn Teilnahmezertifikate geprüft (Ausstellungsdatum 19.10.2026).
Die **Lektionen selbst wurden nicht erneut gesichtet** — Aussagen über Inhalte stammen aus
dem Lehrplan, nicht aus dem Material. Wo der Kurs etwas nur anreißt, steht das ausdrücklich
dabei.

**Provenienz.** Ausbildungsreihe „KI-Automatisierungsexperte (IHK)“, 30 Online-Lektionen à
ca. 135–160 Minuten, Bildungsträger laut Zertifikat: IT-Service Akademie GmbH. Die Zertifikate
nennen je drei Lektionen die „inhaltlichen Schwerpunkte“; genau diese Stichpunkte stehen
unten in der Spalte **Schwerpunkte** und sind der einzige Teil dieser Seite, der aus dem
Kursmaterial stammt. Alles andere — Kompetenzformulierung, Zuordnung, Prüfsteine, Lücken —
ist Auswertung.

**Warum diese Seite hier steht.** Der Kurs lehrt *bauen*: Trigger, Agenten, Werkzeuge,
Muster. Er lehrt wenig *betreiben*: Veröffentlichen, Nachweisen, Zurückrollen, Rechte,
Kosten. FlowLore ergänzt genau diese zweite Hälfte. Wer den Kurs absolviert hat, findet in
[n8n/OPERATIONS.md](../n8n/OPERATIONS.md) die Antworten auf die Fragen, die in der
Zertifikatsprüfung nicht vorkommen.

## Lehrplan

| Teil | Schwerpunkte (Zertifikat) | Kompetenz nach dem Block | Bezug in FlowLore |
| --- | --- | --- | --- |
| 01–03 | Grundlagen KI · n8n Einführung und Grundlagen · Manual Trigger · Webhook Trigger · Chat Trigger | Eine Automatisierung anlegen und über drei verschiedene Auslöser starten; den Unterschied zwischen Test- und Produktionslauf erklären | [Rezept: Workflow-Autor](../../recipes/README.md#recipes); [Operations §2](../n8n/OPERATIONS.md#2-choose-the-interface) |
| 04–06 | AI Agent Node (Memory, Tools) · Error Handling · Challenge: AI Welcome Email Personalizer | Einem Agenten ein Gedächtnis und Werkzeuge geben; einen Fehlerfall sichtbar machen statt ihn zu verschlucken | [Operations §11](../n8n/OPERATIONS.md#11-ai-and-mcp-nodes), [§12](../n8n/OPERATIONS.md#12-error-handling-and-alerting) |
| 07–09 | Debugging · RAG-Systeme · AI Agent Node (HTTP Tooling / JSON) | Einen Lauf gliedern und die Bruchstelle finden; Wissen über Retrieval zuführen; API-Antworten als Werkzeug nutzbar machen | [Failure Modes](../n8n/FAILURE-MODES.md), [Operations §8](../n8n/OPERATIONS.md#8-diagnosing-an-execution) |
| 10–12 | Challenge: AI Welcome Email Personalizer · AI Math Quiz Evaluator · AI Name Formatter – Creative Nicknames · AI Social Media Post Generator | Vier Aufgaben mit vorgegebenen Erfolgskriterien selbstständig umsetzen; Ergebnisqualität statt „läuft“ beurteilen | [Rezept: HTML-Bericht](../../recipes/README.md#recipes) |
| 13–15 | Challenge: AI Social Media Post Generator · AI File Analyzer · Blog Writer Agent | Dateien als Eingabe verarbeiten; mehrstufige Textproduktion mit Prüfschritt aufbauen | [Rezept: Dateiklassifizierung](../../recipes/README.md#recipes) |
| 16–18 | Challenge: Perplexity Research Agent · Telegram Group AI Agent | Externe Recherche als Werkzeug einbinden; einen Bot in einer Gruppe betreiben (Rechte, Chat-ID, Antwortweg) | [Operations §11](../n8n/OPERATIONS.md#11-ai-and-mcp-nodes) |
| 19–21 | n8n: Sub Workflows · Multi Agent Workflows (Iterate Pipeline) | Verantwortlichkeiten in eigene Workflows schneiden und einen Datenvertrag zwischen Eltern und Kind formulieren | [Rezept: Agent-Werkzeug-Vertrag](../../recipes/README.md#agent-tool-contract) |
| 22–24 | AI Agent Node: Persistent Memory · Sub Workflows · Datenbanken / Datatables | Zustand über Läufe hinweg speichern; Konfiguration und Verlauf in Tabellen halten statt im Prompt | [Operations §10](../n8n/OPERATIONS.md#10-data-tables) |
| 25–27 | n8n: Multi Agent Workflows (Loop Pattern, Router Pattern) | Selbstkorrektur mit Abbruchbedingung; Spezialisten statt Alleskönner, Auswahl über einen Klassifizierer | [Rezept: Router-Spezialisten](../../recipes/README.md#router-with-specialists), [Rezept: Schleife mit Feedback](../../recipes/README.md#loop-with-feedback) |
| 28–30 | MCP Server / Client · Guardrails | Eigene Werkzeuge über MCP bereitstellen; Ein- und Ausgaben gegen Regeln prüfen, bevor sie wirken | [Operations §11](../n8n/OPERATIONS.md#11-ai-and-mcp-nodes) |

Die Challenges wiederholen sich über Blockgrenzen hinweg (z. B. *AI Social Media Post
Generator* in 10–12 und 13–15). Das ist kein Fehler im Zertifikat: die Aufgaben laufen über
mehrere Sitzungen und werden in der nächsten Dreiergruppe weitergeführt.

## Acht Muster, die der Kurs wiederholt

Diese Bauformen tauchen in mehreren Blöcken auf und sind der eigentliche übertragbare Kern —
nicht die einzelne Challenge.

1. **Auslöser wählen, nicht erzwingen.** Manual für Entwicklung, Webhook für Fremdsysteme,
   Chat für Menschen. Der Auslöser bestimmt die Datenform: ein Webhook v2 verschachtelt den
   Body unter `$json.body`, der Execute-Workflow-Trigger nicht.
2. **Agent = Modell + Gedächtnis + Werkzeuge.** Jedes Teil hängt an einer eigenen
   Verbindungsart (`ai_languageModel`, `ai_memory`, `ai_tool`). Fehlt eine davon, antwortet
   der Agent trotzdem — nur ohne das, was fehlt.
3. **Werkzeuge statt Prompt-Berge.** Alles, was deterministisch geht, gehört in die Kette;
   `$fromAI()` nur dort, wo das Modell wirklich wählen muss.
4. **Sub-Workflow als Vertrag.** Zuerst die Felder aufschreiben (`title`, `url`,
   `summary_hint`), dann bauen. Ein Kind-Workflow, der nicht veröffentlicht ist, lässt den
   Eltern-Workflow scheitern.
5. **Schleife mit Abbruchbedingung.** Prüfer → bei Ablehnung zurück zum Schreiber, mit dem
   Feedback-Feld. Die Obergrenze kommt aus einem eingebauten Zähler (`$runIndex`), nicht aus
   einer selbstgebauten Variable — und die Basis (0 oder 1) prüft man auf der eigenen
   Version nach.
6. **Router + Spezialisten.** Ein Klassifizierer verteilt auf drei Spezialisten, ein Merge
   führt zusammen. Spezialisten prompten leichter als ein Alleskönner.
7. **Persistenz entscheidet über Qualität.** Gedächtnis ohne stabilen Schlüssel ist ein
   Datenleck zwischen Sitzungen; Konfiguration in einer Tabelle ist ein Onboarding in einer
   Zeile.
8. **Leitplanken sind ein Zweig, kein Kommentar.** Guardrails liefern ein Ergebnis
   (`passed`, `reason`), und der abgelehnte Zweig muss sichtbar weiterlaufen — sonst ist die
   Prüfung Dekoration.

## Lernpfad in sechs Stufen

| Stufe | Lektionen | Übungsnachweis (was man vorzeigen kann) | Prüfstein |
| --- | --- | --- | --- |
| 1. Auslöser und Datenfluss | 01–03 | Ein Workflow, der über Webhook **und** Chat dieselbe Antwort liefert | Warum ist `$json.body.message` im Webhook-Fall nötig und im Chat-Fall falsch? |
| 2. Agent mit Gedächtnis | 04–06 | Ein Agent, der sich innerhalb einer Sitzung erinnert und zwischen zwei Sitzungen nicht | Woran erkennt man im Lauf, dass die Memory-Node gegriffen hat — und nicht das Modell? |
| 3. Fehlersuche und Wissen | 07–09 | Ein bewusst herbeigeführter Fehler, der im Error-Workflow mit lesbarer Meldung ankommt | Welcher Lauf zeigt `runData: {}`, und was bedeutet das? |
| 4. Aufgaben unter Kriterien | 10–18 | Zwei Challenges mit dokumentierten Erfolgskriterien und je einem Grenzfall | Woran misst man die Qualität eines LLM-Ergebnisses, ohne es zu „fühlen“? |
| 5. Architektur | 19–24 | Ein Orchestrator mit zwei Kind-Workflows und schriftlichem Datenvertrag | Was passiert, wenn der Kind-Workflow nicht veröffentlicht ist? |
| 6. Muster und Leitplanken | 25–30 | Router mit drei Spezialisten, Schleife mit Abbruch, Guardrail mit sichtbarem Ablehnungszweig | Wie viele Runden darf die Schleife laufen, und wo steht diese Zahl? |

## Was der Lehrplan nicht abdeckt

Diese Lücken sind keine Kritik am Kurs — ein Einstieg über 30 Lektionen kann sie nicht
füllen. Sie sind der Grund, warum FlowLore eine eigene Betriebsseite hat.

| Thema | Warum es im Betrieb zählt | Wo es hier steht |
| --- | --- | --- |
| Veröffentlichen und Versionieren | „Aktiv“ ist ein Zustand, kein Häkchen; eine Änderung kann ungetestet live gehen | [Operations §5–6](../n8n/OPERATIONS.md#5-writing-state) |
| Nachweis statt Eindruck | Ein grüner Lauf beweist keine Wirkung; Nebenwirkungen zählt man in den Zieldaten | [Operations §9](../n8n/OPERATIONS.md#9-changing-a-live-workflow) |
| Idempotenz | Ein wiederholter POST erzeugt den zweiten Datensatz | [Operations §5](../n8n/OPERATIONS.md#5-writing-state) |
| Rechte und Geheimnisse | Ein Workflow-Dump enthält Tokens, zweimal | [Operations §4](../n8n/OPERATIONS.md#4-reading-state-without-leaking-secrets) |
| Kosten und Grenzen | Ein RSS-Feed mit 20 Einträgen vor einem Agenten sind 20 Modellaufrufe | [Rezept: Schleife mit Feedback](../../recipes/README.md#loop-with-feedback) |
| Fehlerpfade als Testfälle | Der Grünpfad beweist nur, dass es läuft | [Operations §9](../n8n/OPERATIONS.md#9-changing-a-live-workflow) |

## Quellen

- Teilnahmezertifikate der Ausbildungsreihe „KI-Automatisierungsexperte (IHK)“, zehn Blöcke
  à drei Lektionen, ausgestellt am 19.10.2026 (nicht im Repository).
- Die Kursinhalte selbst (Videos, Folien, Aufgabenlösungen) sind **nicht** Gegenstand dieses
  Repositorys und werden hier nicht wiedergegeben.
- Technische Aussagen in der Spalte „Bezug“ sind gegen
  [docs.n8n.io](https://docs.n8n.io) geprüft; siehe [n8n/VERSION-MATRIX.md](../n8n/VERSION-MATRIX.md).
