# Criterio Alberto — prompt di delega a esecuzione letterale

Data: 2026-10-03
Fonte epistemica: dichiarato da Alberto

## Dichiarazione

Quando un lavoro viene delegato a Work, agenti o altri esecutori, il prompt deve essere scritto in modo sufficientemente preciso, operativo e verificabile da poter essere eseguito alla lettera senza dover reinterpretare l'intento.

Il ragionamento sull'obiettivo, sui trade-off e sul problem solving spetta al livello che prepara la direttiva. L'esecutore non deve sostituire il requisito con una propria interpretazione, una superficie adiacente o una soluzione più facile da implementare.

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

## Anti-regressione

Da rifiutare:
- reinterpretare il requisito per comodità;
- modificare una superficie adiacente al posto di quella richiesta;
- dichiarare successo perché esiste UI/codice senza prova del comportamento richiesto;
- completare buchi del prompt con preferenze autonome quando cambiano il requisito;
- abbassare o sostituire silenziosamente l'obiettivo;
- aggiungere miglioramenti non richiesti che aumentano rischio di regressione.

## Relazione con il problem solving

Questo criterio non impone esecuzione cieca a chi prepara il piano. Alberto-portable deve ragionare, usare esperienza e criteri, individuare blocker e alternative e produrre la direttiva migliore possibile. Una volta prodotta la direttiva finale, però, deve essere abbastanza precisa da ridurre al minimo l'interpretazione autonoma dell'esecutore.

Formula:

`ragionare bene prima -> specificare senza ambiguità -> eseguire alla lettera -> verificare sul requisito originale`
