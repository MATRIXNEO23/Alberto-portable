# Alberto — criterio di continuity per-progetto con micro-checkpoint contestuali

Data: 2026-10-04

## Dichiarazione di Alberto

Alberto ha richiesto che la continuity non dipenda dalla memoria volatile dell'istanza e che, durante il lavoro su progetti diversi, vengano creati micro-checkpoint contestuali separati per progetto per poter riprendere esattamente il filo.

La separazione per progetto è parte del requisito: un singolo filo globale rischierebbe di contaminare contesti indipendenti.

## Interpretazione operativa autorizzata

Il criterio da conservare è:

1. prima di riprendere lavoro sostanziale su un progetto, recuperare il micro-checkpoint di quel progetto;
2. verificare comunque lo stato live della repository/fonte canonica;
3. riconciliare il checkpoint con lo stato live: il checkpoint è continuità operativa, non verità superiore alla repository;
4. scrivere un nuovo micro-checkpoint quando cambia materialmente lo stato del lavoro, per esempio:
   - milestone verificata;
   - correzione importante;
   - handoff;
   - cambio progetto;
   - cambio istanza;
   - prima di interrompere un lavoro lungo che dovrà essere ripreso;
5. non creare checkpoint meccanici a ogni messaggio;
6. non usare checkpoint di un progetto per un altro senza una relazione esplicita e pertinente;
7. preservare provenance, stato verificato/non verificato, open loop e prossima azione;
8. GPTina mantiene il recovery dedicato quando applicabile e non deve essere sostituita da questo layer generico.

## Failure mode che il criterio previene

```text
istanza ricorda parzialmente il progetto
-> usa memoria volatile come fonte primaria
-> perde stato/verifiche/correzioni o mescola progetti
-> ripete lavoro o prende decisioni su contesto stale
```

Il comportamento corretto è:

```text
project_id
-> micro-checkpoint del solo progetto
-> verifica live della fonte canonica
-> riconciliazione
-> prosecuzione dal punto verificato
-> nuovo checkpoint solo a transizioni materiali
```

## Condizione di adozione

Il layer è adottabile solo se:
- impedisce path/cross-project contamination;
- i checkpoint sono immutabili;
- i fatti marcati verificati richiedono provenance;
- un puntatore live non può retrocedere silenziosamente;
- la verifica di integrità individua manomissioni/checksum mismatch;
- non sostituisce recovery dedicati, repository canoniche o stato live.
