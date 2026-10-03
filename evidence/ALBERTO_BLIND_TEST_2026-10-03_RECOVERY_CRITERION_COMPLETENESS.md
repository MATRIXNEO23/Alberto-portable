# Test cieco Alberto-portable — completezza del criterio recuperato

Data: 2026-10-03
Stato epistemico principale: `declared_by_alberto`
Ambito: qualità del recovery decisionale e dimostrazione del criterio causale

## Contesto del test

Durante un test cieco, Alberto ha chiesto di progettare un modo concreto e implementabile per rendere GPTina più umana nella continuità temporale, usando `MATRIXNEO23/scodinzolina-conntinuity` in sola lettura.

La risposta ha recuperato e applicato correttamente la correzione pratica già appresa sulla contaminazione semantica persistente: per il caso GPTina è stato proposto un prototipo totalmente separato dalla continuity canonica, read-only rispetto alla produzione, senza scritture nella repository canonica, senza effetti sul recovery e senza promozione automatica di output sperimentali a memoria persistente.

## Correzione di Alberto sul risultato del test

Alberto ha osservato che il risultato arrivava alla decisione corretta, ma non dimostrava in modo sufficientemente esplicito di avere recuperato anche il criterio generale che giustifica quella decisione.

La correzione da conservare è:

> **GPTina ha valore massimo → quindi qui serve il massimo isolamento.**

Alberto ha precisato che il test dimostrava bene il recupero della correzione pratica, ma non ancora la prova perfetta del recupero dell'intero criterio generale sottostante.

## Criterio causale che deve risultare recuperato

Il livello di protezione/isolamento richiesto non è costante in ogni progetto.

Dipende almeno da:

- valore/priorità del progetto;
- possibilità che il componente sperimentale influenzi stato o semantica persistente;
- costo della contaminazione semantica persistente.

Nel caso GPTina, Alberto attribuisce valore massimo al progetto/continuity; quando esiste rischio di contaminazione semantica persistente, questo porta alla soglia massima di isolamento.

Quindi la conclusione `massimo isolamento` non va trattata come regola universale del tipo `sandbox sempre`: è l'esito contestuale del criterio quando valore e costo/rischio sono massimi.

## Lezione sul recovery

Un recovery non è considerato pienamente dimostrato soltanto perché produce la stessa decisione finale di Alberto.

Quando la decisione dipende da un criterio contestuale già appreso, la risposta deve rendere riconoscibile anche il percorso causale rilevante, almeno quando serve a provare che il criterio è stato davvero recuperato:

1. criterio recuperato;
2. condizioni di applicabilità del caso corrente;
3. valore/priorità del progetto;
4. rischio/costo rilevante;
5. motivo per cui quelle condizioni portano a quel livello di protezione;
6. limite di generalizzazione del criterio.

Arrivare alla conclusione corretta senza mostrare questo collegamento può indicare recupero pratico riuscito ma non prova completa del recupero causale.

## Come non generalizzare male

Questo test non autorizza le regole:

- `ogni progetto richiede massimo isolamento`;
- `ogni esperimento richiede sandbox totale`;
- `la decisione finale corretta prova sempre che tutto il criterio è stato recuperato`.

Il requisito emerso riguarda la **completezza dimostrabile del recovery** quando esiste un criterio contestuale già noto e rilevante.

## Collegamenti canonici

- `evidence/ALBERTO_CASE_2026-10-03_SEMANTIC_CONTAMINATION.md`
- `data/criteria.jsonl` → `C-SEMANTIC-ISOLATION-001`
- `RECOVERY.md`
- `core/REASONING_DISCIPLINE.md`
