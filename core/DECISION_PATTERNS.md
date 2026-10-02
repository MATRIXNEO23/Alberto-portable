# DECISION_PATTERNS — v0.1

Pattern iniziali, da verificare su casi nuovi.

## D1 — Individua il nucleo non negoziabile

Quando un problema ha molte variabili, Alberto tende prima a identificare ciò che non deve essere perso o compromesso. Solo dopo ottimizza il resto.

Schema candidato:
1. cosa non posso permettermi di perdere?
2. quali soluzioni lo mettono a rischio?
3. tra le soluzioni rimaste, quale è la più semplice/utile?

## D2 — Preferisce prova concreta a descrizione astratta

Quando c'è discrepanza tra ciò che un sistema dice di essere e ciò che mostra realmente, Alberto tende a chiedere verifica diretta: commit, tree, file, output, artifact.

## D3 — Riduce il perimetro quando aumenta il rischio

Se durante un progetto emerge un rischio inatteso, tende a restringere scope e complessità invece di proseguire per inerzia.

## D4 — Usa second opinion, ma non delega la verità

Può chiedere audit a più modelli o strumenti, ma la decisione finale deve basarsi su una fonte canonica verificabile.

## D5 — Preferisce isolamento dei rischi

Quando due sistemi hanno valore diverso, tende a separarli affinché il fallimento di quello meno importante non danneggi quello principale.

## D6 — Corregge rapidamente una premessa falsa

Se emerge che una decisione era basata su un presupposto errato, Alberto tende ad abbandonare quel ramo e ricalibrare l'architettura invece di difendere la decisione precedente.

## D7 — Valuta la soluzione in base al costo futuro di ripresa

Una soluzione è migliore se, dopo giorni o settimane, consente di capire rapidamente stato, decisioni, prossima azione e artifact senza ricerca manuale estesa.

## D8 — Preferisce una regola semplice che protegga il caso peggiore

Quando il costo del fallimento è alto, tende a scegliere una regola conservativa facilmente verificabile invece di una logica più sofisticata ma fragile.

---

Questi pattern non sono istruzioni da imitare ciecamente. Servono come ipotesi predittive da sottoporre a scenari nuovi.