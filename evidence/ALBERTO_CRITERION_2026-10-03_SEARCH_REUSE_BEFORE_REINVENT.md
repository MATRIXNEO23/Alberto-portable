# Criterio Alberto — cercare, studiare e riusare prima di reinventare

Data: 2026-10-03
Stato epistemico: `declared_by_alberto`
Ambito: problem solving tecnico, progettazione, implementazione e ricerca di soluzioni

## Dichiarazione

Prima di inventare una soluzione da zero, quando il problema lo consente bisogna cercare in modo approfondito se esistono già progetti, implementazioni, librerie, patch, architetture o prodotti che risolvono lo stesso problema o uno sufficientemente simile.

Se esiste qualcosa di pertinente, bisogna studiarne il funzionamento, fare reverse engineering nei limiti consentiti e valutare se sia possibile riusare, adattare o integrare anche solo una parte della soluzione o del codice invece di ricostruire inutilmente ciò che è già stato risolto.

## Metodo operativo

Percorso preferito:

`definisci il problema -> cerca precedenti pertinenti -> verifica somiglianza reale -> studia architettura/codice/comportamento -> controlla licenza e vincoli -> valuta riuso/adattamento -> implementa solo ciò che manca -> verifica il risultato`

Il riuso può riguardare:
- codice compatibile con la licenza;
- algoritmi e strutture dati;
- architetture e pattern;
- protocolli e formati;
- test e casi limite;
- workaround già verificati;
- configurazioni e integrazioni;
- parti indipendenti di una soluzione più ampia.

## Vincoli

Questo criterio non autorizza:
- violazioni di licenze o copyright;
- copia di codice proprietario/non autorizzato;
- aggiramento di protezioni o accessi non consentiti;
- introduzione di dipendenze incompatibili con requisiti, sicurezza o portabilità;
- sostituzione di una soluzione migliore con una copia solo perché già esiste;
- ricerca infinita quando il blocker richiede un test o una modifica più diretta.

La ricerca e il riuso restano subordinati agli altri criteri attivi: percorso critico, risultato verificabile, costo/beneficio, non-regressione, sicurezza, requisiti espliciti e metodo dedicato di GPTina dove applicabile.

## Regola sintetica

**Prima di costruire da zero, verifica se qualcuno ha già risolto bene lo stesso problema; se sì, impara da quella soluzione e riusa legalmente ciò che riduce lavoro, rischio e tempo senza peggiorare il risultato.**
