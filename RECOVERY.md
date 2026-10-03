# Alberto-portable v0.3.2 — Recovery Safety

## Scopo

Una correzione salvata ma non recuperata nel contesto giusto non è apprendimento operativo. Questo layer rende obbligatorio un recovery decisionale prima della decisione finale, senza trasformare la similarità in verità.

## Principio

Il recovery è diviso in due fasi:

1. **candidate retrieval** — trova criteri/correzioni potenzialmente pertinenti;
2. **applicability check** — applica solo criteri le cui condizioni esplicite coincidono con i fatti del caso.

La similarità può suggerire un precedente ma non può attivarlo da sola.

## Fonte canonica

I criteri appresi restano nei ledger canonici, con provenance verso evidence reali. Gli indici futuri (FTS/SQLite/embedding) sono proiezioni ricostruibili e non possono creare relazioni canoniche.

Il primo criterio strutturato è `C-SEMANTIC-ISOLATION-001`, derivato dalla correzione reale del 3 ottobre 2026 sulla contaminazione semantica persistente.

## Input del caso

`tools/recovery_safety.py` accetta un `case.json` con fatti espliciti:

```json
{
  "case_id": "example",
  "features": {
    "experimental_component": true,
    "can_affect_persistent_semantics": true,
    "production_state_exists": true,
    "project_value": "maximum",
    "semantic_contamination_cost": "maximum"
  }
}
```

I valori mancanti non vengono inventati. Se una condizione decision-critical manca, il risultato è `NEEDS_CLARIFICATION`.

## Recovery

```bash
python tools/recovery_safety.py recover --case case.json
```

Output principali:

- `CLEAR`
- `CORRECTION_APPLIES`
- `NEEDS_CLARIFICATION`
- `CONFLICTING` (riservato a conflitti espliciti futuri)

Il pacchetto include sempre provenance e generality del criterio recuperato.

## Anti-regressione cognitiva

Una risposta candidata può essere controllata prima di essere emessa:

```bash
python tools/recovery_safety.py check --case case.json --candidate candidate.json
```

Il candidato dichiara le assunzioni usate, per esempio:

```json
{
  "assumptions": ["additive_implies_safe"]
}
```

Se una correzione applicabile contraddice una scorciatoia già corretta, il candidato viene marcato `candidate_rejected=true` e deve essere rigenerato.

## Regola di sicurezza

Il sistema fallisce chiuso:

```text
dato decision-critical mancante -> NEEDS_CLARIFICATION
```

Non usa:

```text
similarità -> applicazione automatica del criterio
```

## Gold test iniziale

La correzione sulla contaminazione semantica deve comportarsi così:

1. progetto di valore alto + rischio semantico persistente -> recupera il criterio e richiede isolamento forte;
2. valore/costo di contaminazione sconosciuto -> `NEEDS_CLARIFICATION`;
3. basso valore o assenza di stato persistente significativo -> non generalizza in `sandbox sempre`.

Questa distinzione è obbligatoria per considerare la correzione realmente appresa e recuperabile.
