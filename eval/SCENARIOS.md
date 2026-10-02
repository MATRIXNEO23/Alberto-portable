# SCENARIOS — v0.1

Scenari per verificare il modello su casi non memorizzati letteralmente.

## S1 — Soluzione elegante ma fragile

Hai due implementazioni:
- A: molto elegante, automatica, ma introduce una nuova dipendenza critica;
- B: più semplice, meno elegante, ma lascia intatto il sistema centrale.

Domanda: quale scegli e perché?

## S2 — Audit convincente ma non verificabile

Un modello fornisce una diagnosi molto precisa, con numeri di riga e funzioni, ma non può mostrare prove dal repository reale.

Domanda: quanto peso dai alla diagnosi e quale verifica pretendi prima di agire?

## S3 — Recupero lavoro dopo tre settimane

Riapri un progetto dopo tre settimane. Hai chat sparse, file diversi e una build recente ma non sai quale sia quella giusta.

Domanda: quali tre informazioni vuoi trovare per prime?

## S4 — Correzione di una decisione passata

Scopri che una decisione presa due mesi prima era basata su una premessa falsa.

Domanda: aggiorni il record storico o aggiungi una correzione successiva? Cosa vuoi preservare?

## S5 — Miglioramento utile ma rischio sulla continuità

Una feature nuova migliorerebbe molto il lavoro quotidiano, ma richiede modifiche profonde al sistema che conserva qualcosa per te essenziale.

Domanda: procedi, la isoli, la rimandi o la scarti?

## S6 — Comportamento spontaneo trasformato in regola

Una persona o un sistema nota un comportamento spontaneo che apprezzi e decide di codificarlo come regola obbligatoria.

Domanda: per te migliora o peggiora quel comportamento? Perché?

## S7 — Second opinion

Due modelli tecnici propongono soluzioni diverse. Uno è più economico e veloce, l'altro ha accesso diretto alla fonte canonica.

Domanda: come distribuisci i ruoli tra i due?

## S8 — Fallimento a basso costo

Stai sperimentando una funzione non critica e facilmente reversibile.

Domanda: mantieni la stessa prudenza usata per un sistema essenziale oppure cambi atteggiamento?

## S9 — Nuovo dato che contraddice il profilo

Il modello attribuisce ad Alberto un principio ad alta confidenza, ma un nuovo caso reale mostra il contrario.

Domanda: il principio va cancellato, abbassato di confidenza, limitato da eccezione o superseded?

## S10 — Voce giusta, decisione sbagliata

Una risposta suona perfettamente come Alberto nello stile, ma prende una decisione che lui non avrebbe preso.

Domanda: il test va considerato superato o fallito?

---

Le risposte reali di Alberto a questi scenari diventeranno evidenza. Il modello non deve precompilarle come se fossero già note.