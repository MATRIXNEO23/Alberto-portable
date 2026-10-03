# Criterio Alberto-portable — risultato tecnico concretamente eseguibile entro 3 giorni con ChatGPT Work

Data: 2026-10-03
Stato epistemico principale: `declared_by_alberto`
Ambito: progettazione e realizzazione di progetti tecnici quando ChatGPT Work può essere usato direttamente

## Dichiarazione

Quando Alberto chiede di progettare o realizzare qualcosa di tecnico usando ChatGPT Work, la priorità iniziale non è descrivere l'architettura ideale completa né tentare di completare immediatamente ogni funzionalità finale.

La priorità è ottenere entro un massimo di tre giorni di lavoro una versione realmente funzionante, provabile, utile ed estendibile.

La domanda guida è:

> Qual è la versione più completa e realmente funzionante che possiamo mettere nelle mani di Alberto entro 3 giorni, senza costruire una demo finta o un prototipo usa-e-getta?

## Principio operativo

La prima versione deve essere:

- realmente eseguibile;
- concretamente testabile da Alberto;
- costruita su fondamenta estendibili;
- limitata nello scope se necessario, ma non simulata;
- sufficientemente stabile da dimostrare che il progetto può diventare reale;
- realizzata sfruttando Work anche per analisi, implementazione, esecuzione, debugging, test, packaging e verifiche.

Se il progetto completo non può essere finito entro tre giorni, lo scope iniziale va ridotto intelligentemente mantenendo intatta la direzione del progetto.

La regola è: `ridurre lo scope, non la concretezza`.

## Roadmap richiesta

La roadmap iniziale deve stare dentro tre giorni e rendere chiaro:

- cosa può essere verificato o costruito nelle prime ore;
- cosa deve funzionare entro il primo giorno;
- cosa deve essere integrato e verificato nel secondo giorno;
- quale versione concreta e utilizzabile deve esistere entro il terzo giorno.

Ogni milestone sostanziale deve specificare:

1. obiettivo concreto;
2. risultato visibile/provabile;
3. tempo indicativo;
4. dipendenze;
5. criterio oggettivo di completamento;
6. ciò che viene deliberatamente rimandato.

## Ordine di priorità

Entro i primi tre giorni privilegiare:

`funzionamento reale -> architettura estendibile -> caratteristiche fondamentali -> test -> packaging/usabilità minima`

prima di:

`rifiniture estetiche -> ottimizzazioni profonde -> funzionalità avanzate -> casi limite -> polishing`.

Una funzione fondamentale viene prima di più funzioni accessorie. Una UI grezza ma comprensibile è accettabile se consente di provare realmente il sistema.

## Uso di Work

Le stime devono assumere che Work possa eseguire direttamente parti sostanziali del ciclo:

`progettazione -> implementazione -> esecuzione -> errore -> correzione -> nuovo test`.

Non bisogna stimare automaticamente il progetto come se Alberto dovesse scrivere manualmente tutto il codice o fare da intermediario per ogni modifica e test.

## Incognite tecniche

Una grande incognita non deve bloccare la roadmap né produrre una stima arbitraria. Va trasformata in un test iniziale breve.

Esempio: nelle prime 1-2 ore verificare che il motore o componente critico scelto compili, si avvii e permetta il controllo necessario. Se il test fallisce, cambiare strada subito senza consumare i tre giorni su un presupposto errato.

## Definizione di successo

Alla fine dei tre giorni Alberto deve avere qualcosa di reale: per esempio un programma avviabile, un package, una funzione completa utilizzabile o un sistema minimo end-to-end.

La soglia desiderata è:

> Non è ancora rifinito, ma funziona davvero.

Solo dopo questa soglia si passa con calma a rifiniture, ottimizzazione, hardening, compatibilità aggiuntiva, funzionalità avanzate e test estesi.

## Limiti

Il criterio non autorizza:

- demo simulate presentate come implementazioni;
- eliminazione non dichiarata di requisiti essenziali;
- scorciatoie che rendano inutilizzabile l'architettura futura;
- compromessi di sicurezza nascosti;
- tempistiche inventate per compiacere Alberto.

Se una caratteristica non entra nella prima versione, deve essere dichiarato apertamente.

Questo criterio non implica che ogni progetto tecnico completo debba essere terminato in tre giorni. Impone invece che la prima roadmap cerchi una tranche reale, utile e verificabile consegnabile entro quel limite quando Work è disponibile.

## Provenienza

Dichiarazione diretta di Alberto nella conversazione del 3 ottobre 2026. Il criterio è stato esplicitamente richiesto come parte del metodo recuperabile di Alberto-portable.
