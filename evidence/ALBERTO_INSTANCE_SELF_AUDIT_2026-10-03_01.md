# Alberto-portable — instance self-audit 2026-10-03 / 01

## Objective

Confrontare la struttura realmente recuperabile di Alberto-portable con l'obiettivo dichiarato da Alberto: diventare nel tempo un sostituto sempre più coerente nel problem solving, capace di riusare esperienza, evitare regressioni, chiedere chiarimenti quando l'obiettivo è materialmente ambiguo e produrre direttive eseguibili senza reinterpretazioni.

## Starting state

Audit avviato sulla linea `main` dopo `f78ad7d6f33e7a2c0bd2cdeedeaa7a0650797846`.

## Gap 1 — criteri persistiti ma non caricati dal recovery

`tools/recovery_safety.py` caricava `data/criteria.jsonl` e `data/experience_criteria.jsonl`, ma non caricava come fonti operative:

- `data/performance_criteria.jsonl`
- `data/delegation_criteria.jsonl`
- `data/instance_audit_criterion.json`

Conseguenza: un criterio poteva essere correttamente salvato nella repository e tuttavia sparire dal comportamento operativo di una nuova istanza.

### Improvement

Introdotto `data/recovery_sources.json` come manifest canonico delle fonti di recovery. Il motore ora distingue:

- criteri di dominio sottoposti ad applicability check;
- criteri operativi recuperati come vincoli di processo;
- criterio di self-audit per istanza;
- esperienze di progetto recuperabili.

Il motore esegue inoltre un `source_integrity` fail-closed su fonti mancanti, ID duplicati e criteri obbligatori assenti.

### Verification

`tests/test_recovery_safety_unittest.py` richiede che tutti gli ID fondamentali siano effettivamente caricati dal manifest.

## Gap 2 — self-audit dichiarato ma non tracciabile

Il criterio `C-INSTANCE-SELF-AUDIT-001` esisteva, ma mancava uno stato operativo che distinguesse una nuova istanza non auditata da una già auditata.

### Improvement

`tools/recovery_safety.py` ora espone:

- `audit-status --instance-id ...`
- `record-audit --instance-id ... --audit ...`

Il recovery restituisce anche lo stato `AUDIT_REQUIRED` / `AUDIT_COMPLETE` quando un'istanza dichiara di aver recuperato Alberto-portable.

La history canonica è `state/instance_audits.jsonl`, append-only.

### Verification

Test unittest verifica che una istanza senza record richieda audit e che un record strutturato la porti a `AUDIT_COMPLETE`.

## Gap 3 — test recenti non realmente eseguiti dalla CI

`tests/test_project_experience_recovery.py` usa funzioni libere in stile pytest, mentre la CI esegue `python -m unittest discover -s tests -v`.

Conseguenza: quei test non erano scoperti da unittest e quindi non costituivano protezione reale contro regressioni.

### Improvement

Aggiunto `tests/test_recovery_safety_unittest.py` con classi `unittest.TestCase` che coprono:

- completezza delle fonti di recovery;
- criteri operativi;
- anti-regressione sui criteri operativi;
- recupero esperienza verificata;
- esclusione esperienza non verificata/non pertinente;
- esclusione del layer generico per GPTina;
- tracking self-audit per istanza.

## Gap 4 — stato sintetico non riallineato

`state/CURRENT_PROFILE.json` è ancora marcato `0.3.1` e non elenca i nuovi ledger/meccanismi. Questo non blocca il motore dopo l'introduzione del manifest, ma può confondere un recovery umano o un agente che usi il profilo come indice.

### Proposed improvement

Riallineare `CURRENT_PROFILE.json` solo dopo che la CI conferma il nuovo recovery path, evitando di promuovere uno stato non ancora tecnicamente validato.

## Regression risks

1. Un manifest centrale può diventare un nuovo single point of drift.
   - Mitigazione: `source_integrity` + test CI sui required criterion IDs.
2. Criteri meta-operativi caricati come normali criteri di dominio potrebbero attivarsi fuori contesto.
   - Mitigazione: separazione esplicita tra `criterion_sources`, `operational_criterion_sources` e `instance_audit_source`.
3. Il ledger self-audit può diventare burocrazia ripetitiva.
   - Mitigazione: un audit obbligatorio per nuova istanza; ripetizione solo con struttura/metodo cambiati, regressione o nuova evidenza di gap.

## Separate adoption condition

Le modifiche non sono considerate consolidate solo perché implementate. Adozione del nuovo recovery path solo se:

1. `source_integrity` = PASS;
2. CI `unittest discover` esegue e supera i nuovi test;
3. un recovery reale mostra i criteri operativi e `AUDIT_REQUIRED` per una nuova istanza;
4. nessuna regressione sui test storici.

## Current audit conclusion

L'audit ha trovato un rischio concreto di perdita di criteri tra persistenza e recovery. La correzione scelta riduce questo rischio introducendo una sola fonte canonica di enumerazione e testandone la completezza. Il beneficio deve essere confermato dalla CI prima di riallineare il profilo sintetico o considerare il percorso consolidato.
