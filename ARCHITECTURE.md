# Alberto-portable v0.2 — Architettura operativa

## Scopo

Alberto-portable non deve limitarsi a descrivere Alberto. Deve conservare decisioni, motivazioni, alternative, risultati e verifiche reali; confrontare metodi diversi per tipo di compito; imparare quali ruoli assegnare a chi; e mantenere distinta la validazione finale di Alberto dalle metriche automatiche.

## Invarianti

1. Nessuna classifica globale dei modelli/metodi.
2. La scelta è sempre contestuale al task: dominio, rischio, reversibilità, bisogno di fonte canonica, costo/tempo e ruolo richiesto.
3. Le decisioni sono append-only: una decisione successiva può supersedere la precedente, non cancellarla.
4. Una decisione registra sempre il perché, le alternative e l'esito atteso.
5. L'outcome reale è separato dalla decisione originale.
6. La validazione di Alberto è una fonte distinta: non viene trasformata in un semplice test automatico.
7. Un metodo può essere adatto a un ruolo e inadatto a un altro sullo stesso task.
8. Le inferenze sul carattere restano separate dalle regole operative dei progetti.
9. Le evidenze negative restano visibili: errori, allucinazioni e build bocciate non vengono cancellati.
10. Nessun aggiornamento deve riscrivere le previsioni congelate o le risposte storiche.

## Strati

### 1. Decision ledger

`data/decisions.jsonl`

Ogni riga è una decisione autonoma con:
- `decision_id`
- data/contesto/task
- alternative considerate
- scelta
- ragioni
- evidenze disponibili
- rischio e reversibilità
- risultato atteso
- eventuale decisione superseded

### 2. Outcome ledger

`data/outcomes.jsonl`

Collega una decisione al risultato osservato senza modificare il record originale. Include:
- controlli tecnici
- regressioni
- artifact/build verificata
- note sull'esito
- validazione finale di Alberto, se avvenuta

### 3. Method observations

`data/method_observations.jsonl`

Non contiene un voto globale. Ogni osservazione è contestuale:
- metodo/modello
- `task_type`
- `role` (`explore`, `audit`, `implement`, `review`, `verify`, ecc.)
- accesso o meno alla fonte canonica
- risultato verificato
- allucinazioni/errori
- costo/tempo se noti
- eventuale esito della build
- eventuale validazione di Alberto

### 4. Router contestuale

`tools/alberto_portable.py route`

Il router non chiede "chi è migliore?". Chiede:
- che compito è?
- quale ruolo serve?
- quanto costa sbagliare?
- il task è reversibile?
- serve accesso alla fonte canonica?
- quali metodi hanno evidenza verificata per questa combinazione?

Restituisce una shortlist motivata e le prove usate. Se l'evidenza è insufficiente, lo dichiara.

### 5. Validazione di Alberto

La validazione finale di Alberto non viene inferita. Può essere:
- `accepted`
- `accepted_with_notes`
- `rejected`
- `not_tested`

Per build/prodotti operativi, `accepted` di Alberto vale come evidenza reale sull'idoneità del metodo per quel tipo di compito, ma non trasforma quel metodo nel "migliore" in assoluto.

## Flusso

1. `record-decision` — registra cosa si sta decidendo e perché.
2. Esecuzione del lavoro con uno o più metodi.
3. `record-method` — registra come si sono comportati i metodi nei ruoli usati.
4. `record-outcome` — registra risultato tecnico e prova reale di Alberto.
5. `route` — su un nuovo task consulta solo osservazioni pertinenti e propone ruoli/metodi in base all'esperienza accumulata.

## Criterio di apprendimento

Il sistema deve preferire evidenza specifica a generalizzazioni:

`stesso task_type + stesso role` > `stesso task_type` > evidenza generica.

Non usa mai una media globale come criterio unico.

## Distinzione persona / progetto

Per inferenze sul carattere umano, variabilità emotiva e contesto personale sono ammessi e devono mantenere confidenza/temporalità.

Per progetti operativi, regole e eccezioni devono essere esplicite, verificabili e stabili finché non vengono deliberatamente cambiate.

## Recovery

La repository deve permettere di ricostruire:
- quali decisioni furono prese;
- perché furono prese;
- quali metodi furono usati;
- cosa produssero realmente;
- cosa Alberto accettò o rifiutò;
- quale evidenza giustifica oggi una scelta di metodo per un nuovo task.

Se il router viene cancellato, i ledger JSONL restano leggibili come fonte canonica; il codice è ricostruibile, l'esperienza no.