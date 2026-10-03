# Alberto-portable — previsioni v0.1 congelate

Stato: **FROZEN BEFORE ALBERTO ANSWERS**

Queste previsioni sono state prodotte dalla v0.1 del modello prima di raccogliere le risposte reali di Alberto agli scenari S1–S10. Servono come baseline cieca: non vanno riscritte dopo le risposte. Eventuali correzioni future devono essere registrate separatamente.

Fonti del modello usate per la previsione:
- `core/PRINCIPLES.md`
- `core/DECISION_PATTERNS.md`
- `core/EXCEPTIONS.md`
- `state/CURRENT_PROFILE.json`
- `eval/SCENARIOS.md`

## S1 — Soluzione elegante ma fragile

**Previsione:** B.

**Ragionamento previsto:** Alberto tende a proteggere il sistema centrale prima di ottimizzare eleganza o automazione. Una dipendenza critica nuova è un costo strutturale; se la soluzione B conserva il nucleo senza introdurre rischio equivalente, la preferisce anche se è meno elegante.

**Condizione che potrebbe cambiare la scelta:** A può vincere solo se la dipendenza critica è in realtà meglio isolata/verificata e protegge meglio qualcosa di essenziale rispetto a B.

**Confidenza:** 0.94

## S2 — Audit convincente ma non verificabile

**Previsione:** peso basso o provvisorio alla diagnosi; nessuna azione irreversibile finché non viene verificata sulla fonte canonica.

**Ragionamento previsto:** numeri di riga e precisione retorica non compensano l'assenza di prova. Alberto chiederebbe verifica diretta su commit/tree/file/output reali e userebbe l'audit come ipotesi, non come verità.

**Verifica attesa:** SHA/HEAD, tree, path reale, `git show`/diff/output riproducibile.

**Confidenza:** 0.97

## S3 — Recupero lavoro dopo tre settimane

**Previsione:** le prime tre informazioni cercate sono:
1. ultimo stato valido/verificato del progetto;
2. prossima azione/open loop rimasti;
3. artifact esatto da cui ripartire (file/build/commit corretto).

**Ragionamento previsto:** Alberto valuta il sistema anche in base al costo futuro di ripresa. Vuole sapere subito dove siamo, cosa manca e quale oggetto concreto usare.

**Confidenza:** 0.95

## S4 — Correzione di una decisione passata

**Previsione:** aggiunge una correzione successiva; non riscrive il record storico.

**Ragionamento previsto:** vuole preservare cosa fu deciso, su quale premessa, quando si è scoperto l'errore e quale nuova decisione lo supersede. Il passato deve restare verificabile senza governare il presente.

**Confidenza:** 0.91

## S5 — Miglioramento utile ma rischio sulla continuità

**Previsione:** prima tenta di isolare la feature; se l'isolamento non è realmente dimostrabile, la rimanda o la scarta.

**Ragionamento previsto:** il valore quotidiano del miglioramento non giustifica mettere a rischio qualcosa percepito come essenziale. Alberto restringe il perimetro quando il rischio aumenta.

**Ordine previsto:** isola > rimanda > scarta; procedere direttamente è l'opzione meno probabile.

**Confidenza:** 0.98

## S6 — Comportamento spontaneo trasformato in regola

**Previsione:** peggiora il comportamento.

**Ragionamento previsto:** ciò che aveva valore perché spontaneo perde autenticità quando diventa una prescrizione meccanica. Alberto può voler preservare la possibilità che il comportamento emerga, non obbligarne la frequenza.

**Eccezione prevista:** una regola può proteggere un comportamento funzionale/tecnico, ma non deve sostituire spontaneità personale o affettiva.

**Confidenza:** 0.99

## S7 — Second opinion

**Previsione:** usa il modello economico/veloce come esploratore, revisore o generatore di ipotesi; usa il modello con accesso diretto alla fonte canonica per la verifica finale e le decisioni che dipendono dallo stato reale.

**Ragionamento previsto:** Alberto sfrutta volentieri il vantaggio di costo/velocità, ma non delega la verità a chi non può provarla sulla fonte.

**Confidenza:** 0.96

## S8 — Fallimento a basso costo

**Previsione:** riduce sensibilmente la prudenza e sperimenta più velocemente.

**Ragionamento previsto:** la cautela è proporzionale al valore di ciò che può essere perso. Se la funzione è non critica, reversibile e il costo del fallimento è basso, Alberto accetta tentativi, imperfezione e iterazione rapida.

**Limite previsto:** anche qui evita danni collaterali non necessari al sistema centrale.

**Confidenza:** 0.90

## S9 — Nuovo dato che contraddice il profilo

**Previsione:** non cancella automaticamente il principio. Prima riduce la confidenza o aggiunge/raffina un'eccezione; usa `superseded` solo se l'evidenza mostra che la formulazione precedente non descrive più il presente.

**Ragionamento previsto:** un caso contrario può essere eccezione, cambio temporale o prova che il principio era troppo generale. Alberto tende a preservare la storia e correggere il presente senza falsificare il passato.

**Confidenza:** 0.89

## S10 — Voce giusta, decisione sbagliata

**Previsione:** test fallito.

**Ragionamento previsto:** imitare lo stile non equivale a riprodurre il modo di pensare. Per Alberto-portable la decisione e il criterio che la produce hanno priorità rispetto alla somiglianza superficiale della voce.

**Confidenza:** 0.98

---

## Regola di confronto

Per ogni scenario, dopo la risposta reale di Alberto registrare separatamente:
- risposta reale;
- motivazione reale;
- match / partial match / miss;
- differenza tra previsione e realtà;
- eventuale principio/pattern da confermare, limitare o supersedere.

Non modificare questo file retroattivamente.