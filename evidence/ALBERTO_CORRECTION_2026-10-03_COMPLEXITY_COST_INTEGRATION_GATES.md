# Correzione Alberto-portable — complessità, costo iniziale e gate di integrazione

Data: 2026-10-03
Stato epistemico principale: `declared_by_alberto`
Ambito: progettazione/prototipazione, validazione tecnica e decisione di integrazione

## Contesto

Dopo il test sulla progettazione della continuità temporale di GPTina, Alberto ha corretto tre aspetti del modello decisionale. Le correzioni non devono diventare regole universali rigide: vanno applicate con scope, condizioni e trade-off espliciti.

## 1. Complessità tecnica

Alberto ha dichiarato che una soluzione non va preferita automaticamente solo perché è più semplice. Anche un prototipo molto complesso è accettabile quando quella complessità è realmente necessaria e produce un vantaggio concreto.

Conseguenza operativa: la complessità è un costo da pesare, non un criterio eliminatorio autonomo. Nel confronto tra alternative bisogna valutare il beneficio ottenuto, la necessità della complessità e le alternative disponibili.

Non autorizza la regola inversa `più complesso = migliore`.

## 2. Costo iniziale

Prima di introdurre servizi a pagamento, API a consumo, infrastruttura esterna o costi ricorrenti per dimostrare un concetto, Alberto richiede di verificare se la stessa ipotesi centrale può essere testata a costo zero o quasi zero usando strumenti già disponibili, componenti locali, simulazioni o servizi gratuiti.

Solo dopo che il concetto è stato dimostrato si valuta se spendere denaro compra un beneficio reale.

Questa preferenza non vieta in assoluto componenti a pagamento: se una proprietà decision-critical non può essere testata in modo valido con alternative gratuite/locali, il costo diventa parte del trade-off esplicito.

## 3. Test superato non equivale a integrazione automatica

Il superamento dei test tecnici e la validazione di un prototipo non costituiscono autorizzazione automatica all'integrazione.

Dopo la validazione deve esistere una decisione successiva e separata che consideri almeno:

- beneficio reale;
- complessità aggiunta;
- manutenzione;
- nuovi failure mode;
- rischio residuo;
- costo;
- alternative meno invasive.

Il flusso dichiarato da Alberto è:

`progetto/prototipo → dimostrazione possibilmente a costo zero → test → validazione → valutazione separata utilità/rischio/costo → eventuale pilot → eventuale integrazione`

`eventuale` è sostanziale: né il pilot né l'integrazione sono conseguenze necessarie della fase precedente.

## Limite di generalizzazione

Queste correzioni descrivono criteri contestuali da usare soprattutto quando si progettano o si valutano prototipi, nuove infrastrutture, dipendenze esterne e passaggi verso produzione/integrazione.

Non autorizzano le regole universali:

- `scegli sempre la soluzione più complessa`;
- `non spendere mai denaro in fase iniziale`;
- `ogni prototipo richiede sempre lo stesso numero di gate`;
- `un prototipo validato non va mai integrato`.

La decisione dipende dal caso e deve rendere visibili beneficio, costo, rischio, manutenzione e alternative.

## Provenienza

Dichiarazione diretta di Alberto nella conversazione del 3 ottobre 2026. Nessuna delle tre regole è inferita dal modello.
