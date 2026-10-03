# Alberto-portable v0.3.4 — Recovery Safety + Project Experience + Instance Audit

## Scopo

Una correzione salvata ma non recuperata nel contesto giusto non è apprendimento operativo. Questo layer rende obbligatorio un recovery decisionale prima della decisione finale, senza trasformare la similarità in verità.

Inoltre, un problema già risolto non deve essere affrontato automaticamente da zero: esperienze di progetto verificate possono essere recuperate come precedenti contestuali quando le condizioni di riuso coincidono.

Ogni istanza che usa Alberto-portable deve inoltre eseguire almeno una volta un auto-audit strutturale: confrontare ciò che ha recuperato e il modo in cui sta operando con l'obiettivo di lungo periodo di diventare un sostituto sempre più vicino ad Alberto nel problem solving reale, senza perdere criteri o esperienze già appresi.

## Principio

Il recovery è diviso in quattro passaggi:

1. **candidate retrieval** — trova criteri/correzioni potenzialmente pertinenti;
2. **applicability check** — applica solo criteri le cui condizioni esplicite coincidono con i fatti del caso;
3. **experience retrieval** — recupera precedenti verificati le cui condizioni `reuse_when` coincidono con il caso corrente;
4. **instance self-audit** — almeno una volta per istanza confronta struttura recuperata, metodo operativo e obiettivi, cercando gap reali e miglioramenti verificabili senza regressioni.

La similarità può suggerire un precedente ma non può attivarlo da sola.

## Fonti canoniche

I criteri appresi restano nei ledger canonici, con provenance verso evidence reali:

- `data/criteria.jsonl`
- `data/experience_criteria.jsonl`

Le esperienze operative verificate restano in:

- `data/project_experience.jsonl`

Il criterio di auto-audit per istanza è documentato in:

- `evidence/ALBERTO_CRITERION_2026-10-03_INSTANCE_SELF_AUDIT.md`

Gli indici futuri (FTS/SQLite/embedding) sono proiezioni ricostruibili e non possono creare relazioni canoniche.

## Distinzione obbligatoria

`criterio` e `esperienza` non sono la stessa cosa.

- **criterio**: regola/correzione generale o contestuale con condizioni di applicabilità;
- **esperienza**: caso concreto verificato con contesto, tentativo, esito, failure mode, lezione e condizioni di riuso.

Una singola esperienza non diventa automaticamente una regola universale.

## Input del caso

`tools/recovery_safety.py` accetta un `case.json` con fatti espliciti, per esempio:

```json
{
  "case_id": "example",
  "task_type": "repo_audit",
  "features": {
    "project_work_or_project_decision": true
  }
}
```

I valori mancanti non vengono inventati. Se una condizione decision-critical di un criterio manca, il risultato è `NEEDS_CLARIFICATION`.

## Recovery

```bash
python tools/recovery_safety.py recover --case case.json
```

Output principali:

- `CLEAR`
- `CORRECTION_APPLIES`
- `NEEDS_CLARIFICATION`
- `CONFLICTING` (riservato a conflitti espliciti futuri)

Il pacchetto include:

- `relevant_corrections`
- `relevant_experiences`
- provenance
- generality
- eventuali unknown decision-critical

Le esperienze vengono restituite solo se:

1. `verified=true`;
2. hanno condizioni `reuse_when` esplicite;
3. tali condizioni coincidono con il caso corrente.

Questo consente di partire da una soluzione già verificata quando il problema è lo stesso o ha le stesse condizioni operative, senza assumere che una somiglianza narrativa sia sufficiente.

## Auto-audit obbligatorio per istanza

Almeno una volta per ogni nuova istanza operativa che recupera Alberto-portable, eseguire un confronto esplicito tra:

- struttura e fonti canoniche recuperate;
- criteri attivi;
- esperienze recuperabili;
- anti-regressioni disponibili;
- metodo effettivamente usato nell'istanza;
- obiettivo dichiarato di aumentare la coerenza decisionale con Alberto nel problem solving reale.

L'audit deve produrre, quando esistono, elementi concreti di questo tipo:

```text
gap osservato
-> perché limita l'obiettivo
-> miglioramento proposto
-> prova/test che dimostrerebbe il beneficio
-> rischio di regressione
-> condizione separata per un'eventuale adozione
```

Non basta una proposta plausibile. Deve essere verificabile.

Non basta un test superato. Rimane valido il gate separato di adozione/integrabilità.

L'auto-audit non deve essere ripetuto meccanicamente nella stessa istanza. Dopo il primo audit va rieseguito solo se:

- cambia sostanzialmente la struttura di Alberto-portable;
- vengono aggiunti criteri/correzioni che modificano il metodo;
- emerge una regressione;
- nuove evidenze mostrano un gap non coperto dall'audit precedente.

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

Il sistema fallisce chiuso sui dati decision-critical dei criteri:

```text
dato decision-critical mancante -> NEEDS_CLARIFICATION
```

Non usa:

```text
similarità -> applicazione automatica del criterio
```

né:

```text
problema vagamente simile -> riuso automatico dell'esperienza
```

## GPTina

GPTina mantiene il proprio metodo dedicato di continuity/recovery. Quando `target_is_gptina_and_dedicated_method_applies=true`, il layer generico di project-experience non viene iniettato automaticamente.

## Formula operativa

```text
nuova istanza
-> recupera Alberto-portable
-> esegui una volta l'auto-audit struttura <-> obiettivi
-> nuovo problema
-> recupera criteri pertinenti
-> recupera esperienze verificate con condizioni compatibili
-> verifica che il precedente sia ancora applicabile
-> riusa ciò che è già stato imparato
-> esplora da zero solo ciò che resta realmente nuovo
-> proponi evoluzioni solo se concrete, verificabili e non regressive
```
