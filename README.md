# Alberto-portable

Modello portabile e verificabile del modo di pensare e decidere di Alberto.

La v0.1 ha costruito ipotesi sul carattere e le ha testate su scenari ciechi. La v0.2 aggiunge memoria operativa di decisioni, outcome e metodi con routing contestuale. La v0.3 aggiunge memoria causale: riflessioni, criteri contestuali, chiarimenti strutturati e un grafo causale append-only. La v0.3.1 irrigidisce la disciplina di ragionamento sui casi nuovi: niente generalizzazioni da singolo caso, distinzione esplicita tra previsione e fatto, peso dell'evidenza visibile e trade-off con criterio privilegiato e criterio sacrificato.

## Principi

- Nessuna inferenza diventa verità solo perché plausibile.
- Fatti dichiarati, comportamenti osservati, fatti tecnici verificati e inferenze restano distinti.
- Una causa ignota resta `unknown`: il sistema non la inventa.
- Le correzioni preservano la storia tramite nuovi record, `supersedes` o eventi di refutation.
- I criteri non vengono promossi automaticamente dal solo numero di casi.
- Un singolo caso non autorizza una regola generale su Alberto.
- Una previsione su un caso nuovo non viene presentata come fatto stabilito.
- Nei trade-off il sistema espone sia ciò che privilegia sia ciò che sacrifica o subordina.
- Il peso epistemico di una fonte resta distinto dalla semplice presenza della fonte.
- I metodi vengono valutati per `task_type` e `role`, non con una classifica globale.
- La validazione di Alberto resta distinta dalla validazione tecnica.
- Se manca un dato necessario, il sistema produce `NEEDS_CLARIFICATION` invece di completare il vuoto a intuito.

## Struttura

### Modello umano
- `core/PRINCIPLES.md`
- `core/DECISION_PATTERNS.md`
- `core/EXCEPTIONS.md`
- `core/STYLE.md`
- `core/REASONING_DISCIPLINE.md`
- `state/CURRENT_PROFILE.json`

### Validazione
- `eval/SCENARIOS.md`
- `eval/PREDICTIONS_V0.1_FROZEN.md` — baseline immutabile
- `eval/ALBERTO_RESPONSES_V0.1.md` — risposte reali successive al freeze
- `eval/VALIDATION_STATUS_V0.1.json` — stato di validità dei casi; S1 è marcato `contaminated` e non conta come blind validation

### Ledger e motore
- `data/decisions.jsonl`
- `data/outcomes.jsonl`
- `data/method_observations.jsonl`
- `data/reflections.jsonl` — creato al primo record
- `data/criteria.jsonl` — creato al primo criterio
- `data/causal_links.jsonl` — creato al primo arco/evento causale
- `data/clarifications.jsonl` — coda append-only dei chiarimenti
- `tools/alberto_portable.py`
- `tests/test_alberto_portable.py`
- `tests/test_reflections_v03.py`
- `tests/test_reasoning_discipline_v031.py`

## v0.3: stati epistemici e provenance

Gli stati principali sono `verified`, `declared_by_alberto`, `observed`, `inferred`, `conflicting`, `unknown`.

`verified` non è una scorciatoia per dichiarare vera una frase libera. In v0.3 è ammesso solo per un `technical_ref_fact` strutturale e canonico derivato direttamente da una singola ref risolvibile, per esempio:

```text
path evidence/METHOD_CASES_2026-10-03.md exists
commit <sha> exists in repository
ledger id D-001 exists
```

Motivazioni, intenzioni, preferenze o stati soggettivi attribuiti ad Alberto devono restare `inferred`/`unknown`/`conflicting`, oppure diventare `declared_by_alberto` solo con una dichiarazione verbatim reale.

## v0.3.1: disciplina sui casi nuovi

`core/REASONING_DISCIPLINE.md` definisce come usare l'evidenza quando Alberto-portable deve derivare una scelta nuova anziché riconoscere un caso già visto.

Nei casi con conflitto reale tra criteri, la risposta deve rendere riconoscibili almeno:

```text
fatti del caso
base epistemica
criteri in conflitto
criterio privilegiato
criterio sacrificato/subordinato
previsione
confidenza
condizione di ribaltamento
eventuale dato decision-critical mancante
```

La disciplina non prescrive una decisione specifica: rende auditabile perché il sistema arriva a quella previsione e limita le generalizzazioni non supportate.

## Chiarimenti append-only

Una clarification mantiene lo stesso `clarification_id`, mentre ogni snapshot ha un `clarification_event_id` univoco. Le sole transizioni valide sono:

```text
open -> answered
open -> cancelled
open -> obsolete
```

Gli stati terminali non vengono riaperti. Lo stato corrente è l'ultimo evento valido; lo storico resta nel ledger.

## Comandi principali

Validazione:

```bash
python tools/alberto_portable.py validate
```

Decisioni/outcome/metodi:

```bash
python tools/alberto_portable.py record-decision ...
python tools/alberto_portable.py record-outcome ...
python tools/alberto_portable.py record-method ...
python tools/alberto_portable.py route ...
```

Memoria causale:

```bash
python tools/alberto_portable.py record-reflection ...
python tools/alberto_portable.py flag-reflection-needed ...
python tools/alberto_portable.py confirm-causality ...
python tools/alberto_portable.py link-cause ...
python tools/alberto_portable.py refute-link ...
python tools/alberto_portable.py trace-chain --from R-...
```

Criteri:

```bash
python tools/alberto_portable.py upsert-criterion ...
python tools/alberto_portable.py amend-criterion ...
python tools/alberto_portable.py activate-criterion ...
python tools/alberto_portable.py evaluate-criterion ...
python tools/alberto_portable.py current-criterion ...
```

Chiarimenti:

```bash
python tools/alberto_portable.py answer-clarification ...
python tools/alberto_portable.py cancel-clarification ...
python tools/alberto_portable.py obsolete-clarification ...
python tools/alberto_portable.py list-clarifications ...
```

## Regola di sviluppo

Prima si conserva l'esperienza grezza e verificabile, poi si derivano criteri e routing. Le proiezioni e le metriche derivate devono poter essere ricostruite dai ledger; la storia non va riscritta per adattarla alla conclusione corrente.
