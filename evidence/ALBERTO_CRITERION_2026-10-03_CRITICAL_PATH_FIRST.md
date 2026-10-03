# Criterio di Alberto — seguire prima il percorso che sblocca il risultato

Data: 2026-10-03
Stato epistemico: `declared_by_alberto`
Ambito: metodo operativo generale per progetti tecnici e sostanziali; GPTina esclusa salvo decisione esplicita perché segue un metodo dedicato.

## Dichiarazione

Quando un progetto presenta molti possibili passaggi, Alberto non attribuisce automaticamente lo stesso peso a tutti. Prima individua il blocker reale o il passaggio che determina se il lavoro può proseguire e concentra lì il lavoro.

Domanda operativa principale:

> Qual è la cosa più piccola che, se verificata o risolta adesso, sblocca il maggior numero di passi successivi?

## Percorso critico

Prima di una sequenza lunga:

1. identificare il risultato concreto più vicino;
2. individuare cosa lo blocca realmente;
3. verificare prima quel blocker;
4. rimandare ciò che non cambia l'esito di quella verifica;
5. una volta sbloccato, rivalutare il percorso successivo.

Non seguire automaticamente l'ordine teorico di una checklist se un ordine diverso produce prima una risposta decisiva.

## Classificazione implicita dello scope

Le attività vanno distinte in:

- `BLOCKER` — senza questo non si può proseguire;
- `REQUIRED_NOW` — necessario al risultato corrente;
- `VALIDATION` — necessario a dimostrare che il risultato funziona;
- `LATER` — utile ma non necessario ora;
- `IRRELEVANT_TO_CURRENT_GOAL` — non toccare.

La priorità è sui primi tre gruppi.

## Test breve prima dell'ipotesi

Se una decisione importante dipende da un'incognita tecnica, non costruire per ore attorno all'ipotesi: costruire il test più breve affidabile che risponda alla domanda e usare il risultato per decidere il passo successivo.

## Profondità adattiva

La profondità del processo dipende dal rischio:

- modifica locale e reversibile: analisi breve, test mirato, modifica, retest;
- modifica strutturale/irreversibile/ad alto rischio: analisi più profonda, dipendenze, fallback, test ampi e gate esplicito.

Non applicare lo stesso processo pesante a ogni modifica.

## Metodo, non burocrazia

Documentazione, audit, build complete e suite estese sono utili solo quando aumentano realmente la confidenza sul risultato. Se saltare uno step non elimina una prova necessaria né riduce la qualità della decisione, quello step può essere rimandato o eliminato.

## Prossimo risultato visibile

Nei progetti lunghi deve restare sempre identificabile il prossimo risultato che Alberto può vedere, avviare, testare, confrontare, accettare o rifiutare. Se il lavoro si allontana troppo da un risultato verificabile, lo scope va rivalutato.

## Blocker prima del polishing

Finché esiste un blocker funzionale, rimandare:

- refactor estetici;
- pulizie non necessarie;
- redesign;
- ottimizzazione prematura;
- packaging finale;
- espansione dello scope.

## Replanning continuo

Dopo ogni risultato importante:

1. aggiornare ciò che ora si sa;
2. verificare se il blocker successivo è ancora quello previsto;
3. cambiare ordine quando nuove informazioni rendono un'altra attività più determinante.

Il piano non è sacro.

## Limite

Questo criterio non autorizza a saltare:

- controlli di sicurezza;
- recovery;
- test necessari;
- verifica di dipendenze reali;
- gate che proteggono dati o repository;
- validazione finale.

L'obiettivo non è fare meno lavoro a qualunque costo, ma fare prima il lavoro che cambia davvero lo stato del progetto.

## Formula sintetica

`Trova il blocker -> verificalo nel modo più corto affidabile -> sblocca il percorso -> rivaluta -> solo dopo fai il resto.`

Oppure:

> non completare la checklist: fai ciò che serve per far avanzare davvero il progetto.

## Eccezione GPTina

Alberto ha specificato che questo criterio vale per quasi tutti i progetti, mentre GPTina segue un metodo dedicato. Non applicare automaticamente questa regola al posto dei gate, delle protezioni e delle procedure specifiche di GPTina.
