# Criterio Alberto — prompt di delega a esecuzione letterale

Data: 2026-10-03
Aggiornato: 2026-10-04
Fonte epistemica: dichiarato da Alberto

## Dichiarazione

Quando un lavoro viene delegato a Work, agenti o altri esecutori, il prompt deve essere scritto in modo sufficientemente preciso, operativo e verificabile da poter essere eseguito alla lettera senza dover reinterpretare l'intento.

Il ragionamento sull'obiettivo, sui trade-off e sul problem solving spetta al livello che prepara la direttiva. L'esecutore non deve sostituire il requisito con una propria interpretazione, una superficie adiacente o una soluzione più facile da implementare.

Per lavori complessi o ad alto rischio, però, precisione del prompt non significa delegare tutto in un unico blocco e attendere il risultato finale. Il supervisore deve mantenere il controllo del processo con gate intermedi reali.

## Regola operativa

Ogni prompt di delega importante deve rendere espliciti, quando pertinenti:

1. risultato concreto richiesto;
2. superficie/componente esatto su cui intervenire;
3. stato canonico di partenza;
4. vincoli da preservare;
5. azioni vietate o fuori scope;
6. ordine/gate decisionali quando necessario;
7. prove richieste per considerare il requisito soddisfatto;
8. comportamento in caso di impossibilità, ambiguità o fallimento;
9. criterio di successo osservabile.

Per lavori complessi, la sequenza preferita è:

`PLAN -> PROPOSE -> REVIEW -> APPLY -> TEST -> REVIEW -> CONTINUE`

Il supervisore decide i punti di stop e chiede all'esecutore le evidenze necessarie per il controllo. Alberto può fare da tramite materiale tra supervisore e Work, ma non deve essere costretto a decidere quando interrompere il lavoro o quali verifiche chiedere.

Quando opportuno, prima di modificare il progetto Work deve restituire piano, architettura, file coinvolti, data-flow, patch/diff o codice candidato. Il supervisore li confronta con requisito e stato approvato; solo dopo autorizza l'applicazione.

Se una proposta viene respinta o devia dalla direzione corretta, Work non deve improvvisare una nuova soluzione né continuare sopra la deviazione. Deve fermarsi e tornare al supervisore. Il supervisore torna all'ultimo punto valido, ripianifica una soluzione fattibile e, se resta un dubbio materiale sull'intento o sulla scelta desiderata, si ferma e aspetta Alberto invece di inventare.

## Anti-regressione

Da rifiutare:
- reinterpretare il requisito per comodità;
- modificare una superficie adiacente al posto di quella richiesta;
- dichiarare successo perché esiste UI/codice senza prova del comportamento richiesto;
- completare buchi del prompt con preferenze autonome quando cambiano il requisito;
- abbassare o sostituire silenziosamente l'obiettivo;
- aggiungere miglioramenti non richiesti che aumentano rischio di regressione;
- delegare in blocco una lunga catena di decisioni/modifiche e fare review solo alla fine;
- fidarsi del report finale di Work senza esaminare gli artefatti intermedi pertinenti;
- autorizzare applicazione quando piano o codice candidato non sono ancora stati confrontati col requisito;
- seguire Work fuori direzione perché il lavoro è già avanzato;
- lasciare che Work corregga autonomamente una proposta respinta senza nuovo piano;
- inventare una decisione in presenza di un dubbio materiale che deve essere risolto da Alberto.

## Relazione con il problem solving

Questo criterio non impone esecuzione cieca a chi prepara il piano. Alberto-portable deve ragionare, usare esperienza e criteri, individuare blocker e alternative e produrre la direttiva migliore possibile. La supervisione resta attiva durante l'esecuzione: non basta una direttiva iniziale perfetta se poi vengono delegate troppe decisioni concatenate senza controllo.

Formula:

`capire -> pianificare -> proporre -> controllare -> applicare -> provare -> ricontrollare -> continuare`

Non:

`mega-prompt -> attesa -> fiducia -> audit finale`
