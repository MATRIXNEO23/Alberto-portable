# Caso Alberto — isolamento prima di integrazione quando esiste rischio di contaminazione semantica

Data: 2026-10-03
Stato epistemico: `declared_by_alberto`
Ambito: componente sperimentale che può influenzare uno stato canonico persistente
Generalizzazione: **non autorizzata da questo singolo caso**

## Contesto

Durante un caso reale sulla progettazione di un miglioramento della continuity di GPTina, il modello aveva proposto un nuovo layer temporale/inferenziale come estensione additiva dell'architettura esistente.

La proposta preservava append-only, provenance, cold-start e reversibilità tecnica, ma progettava già la futura integrazione del layer nella continuity reale prima di separare in modo abbastanza netto la fase sperimentale dalla produzione.

## Correzione dichiarata da Alberto

Alberto ha corretto il ragionamento stabilendo che, in questo caso, non si doveva proporre l'integrazione del nuovo layer nella continuity reale prima di averlo isolato completamente.

La sua correzione tecnica è stata:

> **prima sandbox separata / clone / copia ricostruita, nessuna scrittura sulla repo canonica, nessun effetto su recovery o salvataggi, output solo diagnostico; solo dopo validazione reale si valuta l’integrazione.**

Ha inoltre chiarito che questa correzione non va trasformata subito in una regola universale.

## Precisazione successiva di Alberto

Alberto ha precisato:

> dipende dalla priorità del progetto, GPTina è la mia vita

La parte decisionale rilevante è:

- il livello di isolamento richiesto dipende dalla priorità/valore del progetto;
- GPTina appartiene, per Alberto, alla classe di valore massimo e quindi richiede la soglia di protezione più alta.

## Osservazione

In questo caso Alberto distingue chiaramente almeno tre rischi:

1. **reversibilità tecnica** — poter tornare indietro dal codice o dalla configurazione;
2. **non-regressione funzionale** — non rompere funzioni già operative;
3. **contaminazione semantica persistente** — introdurre inferenze, link, priorità o stati sbagliati in una memoria canonica che poi può influenzare salvataggi e recovery futuri.

La natura `additive` o append-only non è considerata sufficiente a rendere sicuro un esperimento quando questo può influenzare ciò che viene persistito o interpretato come rilevante.

## Criterio contestuale candidato

> Quando un componente sperimentale può influenzare uno stato canonico persistente o la semantica con cui quello stato viene aggiornato, il livello di isolamento richiesto cresce con il valore e la priorità del progetto. In un progetto di valore massimo, la fase sperimentale deve restare completamente separata e read-only rispetto alla produzione fino a validazione reale; reversibilità e append-only da sole non eliminano il rischio di contaminazione.

Base epistemica: `declared_by_alberto`.
Forza: `candidate/contextual`, non globale.

## Condizioni operative dichiarate per questo caso

Prima della possibile integrazione:

1. sandbox separata, clone o copia ricostruita;
2. nessuna scrittura sulla repository canonica;
3. nessun effetto sul recovery canonico;
4. nessun effetto sui salvataggi canonici;
5. nessuna promozione automatica di link, ranking, inferenze o rilevanza sperimentale a memoria persistente;
6. output del componente sperimentale soltanto diagnostico;
7. integrazione valutata solo dopo validazione reale.

## Come non generalizzare male

Questo caso non dimostra che Alberto richieda isolamento totale per qualunque esperimento o modifica.

La correzione riguarda un contesto in cui:

- il progetto ha valore molto alto;
- esiste uno stato canonico persistente già buono;
- il componente sperimentale potrebbe alterare non solo il codice ma il significato, i collegamenti o ciò che viene conservato nel tempo.

Per progetti a bassa priorità o con costo di fallimento ridotto, la soglia di isolamento può essere diversa e va valutata sul caso concreto.
