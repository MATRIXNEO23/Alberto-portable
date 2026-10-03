# Alberto-portable

Modello portabile e verificabile del modo di pensare e decidere di Alberto.

La v0.1 ha costruito ipotesi sul carattere e le ha testate su scenari ciechi. La v0.2 aggiunge un motore operativo: memoria delle decisioni, outcome reali, osservazioni sui metodi e routing contestuale per scegliere **chi usare per cosa**, non chi sia "migliore" in assoluto.

## Principi

- Nessuna inferenza diventa verità solo perché plausibile.
- Fatti dichiarati, comportamenti osservati e inferenze restano distinti.
- Stile e decisione restano separati.
- Le decisioni registrano sempre il perché, le alternative e l'esito atteso.
- Gli outcome reali non riscrivono la decisione originale: la completano come evidenza successiva.
- I modelli/metodi vengono valutati per `task_type` e `role`, non con una graduatoria globale.
- Le build provate da Alberto hanno una validazione separata dai test automatici.
- Un metodo può essere valido per esplorare e inadatto per verificare o modificare file.
- Il sistema deve poter spiegare quale evidenza ha usato per un routing.

## Struttura

### Modello umano
- `core/PRINCIPLES.md`
- `core/DECISION_PATTERNS.md`
- `core/EXCEPTIONS.md`
- `core/STYLE.md`
- `state/CURRENT_PROFILE.json`

### Validazione cieca
- `eval/SCENARIOS.md`
- `eval/PREDICTIONS_V0.1_FROZEN.md` — baseline immutabile
- `eval/ALBERTO_RESPONSES_V0.1.md` — risposte reali successive al freeze

### Motore decisionale v0.2
- `ARCHITECTURE.md` — invarianti e flusso
- `data/decisions.jsonl` — creato al primo record
- `data/outcomes.jsonl` — creato al primo outcome
- `data/method_observations.jsonl` — evidenza contestuale sui metodi
- `tools/alberto_portable.py` — CLI eseguibile
- `tests/test_alberto_portable.py` — regressioni minime

## Comandi

Validazione dati:

```bash
python tools/alberto_portable.py validate
```

Registrare una decisione:

```bash
python tools/alberto_portable.py record-decision \
  --decision-id D-001 \
  --task-type repo_audit \
  --context "Audit di una modifica critica" \
  --alternatives "metodo-a|metodo-b" \
  --choice "confronto incrociato" \
  --reasons "ridurre allucinazioni|proteggere componenti a cascata" \
  --risk high \
  --no-reversible \
  --expected-outcome "nessuna regressione"
```

Registrare l'esito e la prova reale di Alberto:

```bash
python tools/alberto_portable.py record-outcome \
  --outcome-id O-001 \
  --decision-id D-001 \
  --technical-result passed \
  --tests-passed \
  --alberto-validation accepted \
  --alberto-notes "provata la build finale: funziona"
```

Registrare un metodo nel ruolo specifico:

```bash
python tools/alberto_portable.py record-method \
  --observation-id M-001 \
  --method qwen \
  --task-type repo_audit \
  --role audit \
  --verified-result wrong \
  --hallucination \
  --build-result not_applicable \
  --alberto-validation not_tested
```

Chiedere il routing per un nuovo compito:

```bash
python tools/alberto_portable.py route \
  --task-type repo_audit \
  --role verify \
  --risk high \
  --no-reversible \
  --require-canonical
```

L'output è una shortlist basata sull'evidenza pertinente. Non è una classifica universale.

## Regola di sviluppo

Prima si conserva l'esperienza grezza, poi si derivano le preferenze. Se il codice di routing fosse sbagliato o venisse riscritto, i ledger append-only devono restare sufficienti a ricostruire perché Alberto aveva imparato a usare un metodo in un certo ruolo.