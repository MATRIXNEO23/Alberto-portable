# Alberto-portable v0.3 — Architettura operativa

## Scopo

Alberto-portable conserva non solo decisioni e risultati, ma anche il percorso causale che collega evento, interpretazione, cambiamento di criterio, decisione, outcome e riflessione successiva. Deve poter distinguere ciò che è verificato, ciò che Alberto ha dichiarato, ciò che è osservato e ciò che è soltanto inferito.

## Invarianti

1. Nessuna classifica globale dei modelli/metodi.
2. Decisioni, outcome, riflessioni e archi causali preservano la storia; le correzioni sono append-only.
3. Una causa ignota non viene completata a intuito.
4. `declared_by_alberto` richiede parole reali attribuibili ad Alberto.
5. `verified` è riservato a fatti strutturali direttamente verificabili dalla provenance; non verifica interpretazioni personali.
6. Una fonte reale non prova automaticamente qualunque claim collegato ad essa.
7. I conflitti restano rappresentabili senza scelta automatica di una spiegazione.
8. Le metriche dei criteri sono derivate dai riferimenti reali e non diventano memoria canonica.
9. La validazione tecnica e quella di Alberto restano separate.
10. `PREDICTIONS_V0.1_FROZEN.md` non viene riscritto retroattivamente.

## Ledger

### Decisioni e outcome

`data/decisions.jsonl` e `data/outcomes.jsonl` mantengono la semantica v0.2: scelta, alternative, ragioni, esito atteso e risultato reale sono separati.

### Osservazioni sui metodi

`data/method_observations.jsonl` conserva evidenza contestuale per task e ruolo. Il router usa questa evidenza senza trasformarla in una reputazione globale del metodo.

### Reflections

`data/reflections.jsonl` registra:
- contesto e trigger;
- interpretazione e stato epistemico;
- eventuale cambiamento di criterio;
- causalità `declared`, `evidenced`, `multiple_candidates` o `unknown`;
- condizioni, eccezioni e implicazioni;
- provenance;
- `supersedes` quando una riflessione successiva corregge la precedente.

Un `verified` v0.3 usa `claim_kind=technical_ref_fact` e un `verified_fact` canonico derivato da una ref risolvibile. Questo evita di confondere “la fonte esiste” con “la fonte dimostra una frase arbitraria”.

### Criteria

`data/criteria.jsonl` separa:
- `strength`: `hypothesis`, `candidate`, `contextual_active`, `contested`, `deprecated`;
- `epistemic_basis`: `declared_by_alberto`, `observed`, `inferred`, `mixed`.

I contatori di osservazioni, contesti e stabilità temporale sono calcolati a query-time da `evidence_refs`; non sono fatti canonici memorizzati.

### Causal graph

`data/causal_links.jsonl` conserva archi espliciti e refutation. `trace-chain` attraversa solo relazioni realmente collegate alla radice richiesta, più relazioni strutturali verificabili come decisione→outcome e le catene `supersedes` delle riflessioni. I link refutati restano nello storico ma sono esclusi dal cammino attivo.

### Clarifications

`data/clarifications.jsonl` è una history append-only. `clarification_id` identifica la domanda; `clarification_event_id` identifica lo snapshot immutabile. Le sole transizioni valide sono `open→answered`, `open→cancelled`, `open→obsolete`.

`NEEDS_CLARIFICATION` usa exit code 3 e non scrive sul ledger target prima del blocco. La coda dei chiarimenti rimane invece auditabile.

## Causalità

La catena obiettivo è:

```text
evento -> interpretazione -> riflessione -> criterio -> decisione -> outcome -> nuova riflessione
```

Ogni relazione deve mantenere provenance e stato epistemico. Se esistono spiegazioni incompatibili, vengono conservate entrambe; non viene scelta automaticamente quella “più plausibile”.

## Recovery

Una ricostruzione deve poter recuperare:
- cosa si pensava prima;
- cosa è cambiato;
- perché è cambiato, se la causa è nota;
- cosa resta incerto;
- quali decisioni ne sono derivate;
- cosa è successo realmente;
- quale versione è corrente senza cancellare quella storica.
