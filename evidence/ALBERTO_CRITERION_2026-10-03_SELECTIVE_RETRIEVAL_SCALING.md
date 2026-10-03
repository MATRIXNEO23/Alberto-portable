# C-SELECTIVE-RETRIEVAL-SCALING-001

## Dichiarazione di Alberto

Con la crescita di criteri ed esperienze, il rischio principale diventa recuperare troppo e male. Alberto approva come criterio operativo che la memoria persistente possa crescere, ma ogni task debba attivare solo il sottoinsieme minimo di criteri ed esperienze realmente rilevanti alla decisione corrente.

Formula sintetica approvata:

> molta esperienza persistita, poca esperienza attivata, alta pertinenza.

## Significato operativo

- La crescita della repository non deve tradursi in crescita automatica del contesto recuperato.
- Recuperare solo criteri ed esperienze che possono cambiare materialmente una decisione o prevenire una regressione pertinente.
- Privilegiare specificita', compatibilita' col caso corrente, provenance e condizioni di riuso esplicite.
- Non usare la semplice appartenenza allo stesso task_type come sufficiente prova di pertinenza.
- Non trasformare il recovery in una checklist generale o in una procedura burocratica.
- Se due precedenti sono applicabili, preferire quello piu' specifico; usare il piu' generale solo quando aggiunge informazione decision-relevant non coperta dal precedente specifico.
- Conservare la capacita' di recuperare contesto aggiuntivo quando serve per risolvere un'incertezza concreta, ma non "per sicurezza" in modo indiscriminato.

## Anti-regressioni

Da rifiutare:

- caricare tutti i criteri solo perche' esistono;
- caricare tutte le esperienze dello stesso tipo di task;
- aumentare il contesto attivato proporzionalmente alla dimensione della repository;
- usare checklist crescenti come sostituto della selezione contestuale;
- privilegiare recall alto sacrificando sistematicamente la precisione;
- perdere un precedente altamente specifico perche' sommerso da molti precedenti generici.

## Relazione con criteri esistenti

Questo criterio rafforza C-EXPERIENCE-ACCUMULATION-001 e i fix gia' introdotti sulla precisione del retrieval. Non autorizza a saltare criteri obbligatori, safety gate, vincoli espliciti o il recovery dedicato di GPTina.
