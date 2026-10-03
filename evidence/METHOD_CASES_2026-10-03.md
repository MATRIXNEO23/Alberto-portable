# Metodo / audit — casi osservati 2026-10-03

Questa fonte documenta due osservazioni operative distinte sullo stesso modello/metodo durante l'audit di `MATRIXNEO23/scodinzolina-conntinuity`.

## Caso M-2026-10-03-01 — audit repo, evidenza confabulata

Metodo: Qwen/coder
Task type: `repo_audit`
Role: `audit`

Osservazione:
- ha prodotto una diagnosi architetturale concettualmente plausibile;
- ha citato simboli, funzioni e numeri di riga che non esistevano nel tree canonico;
- dopo clone fresco e verifica contro `origin/main`, ha riconosciuto che il precedente audit era errato;
- failure mode rilevante: `citation_hallucination`.

Esito verificato: `wrong` per le citazioni puntuali del primo audit.

## Caso M-2026-10-03-02 — audit repo dopo riallineamento

Metodo: Qwen/coder
Task type: `repo_audit`
Role: `audit`

Condizioni aggiuntive:
- clone fresco dalla repository canonica;
- HEAD e origin/main verificati identici;
- obbligo di prova tramite tree reale;
- divieto di completare buchi a intuito.

Osservazione:
- ha corretto il finding precedente;
- ha distinto ciò che esisteva realmente da ciò che era stato confabulato;
- ha prodotto un audit utile per restringere la progettazione successiva.

Esito verificato: `correct` sotto vincoli di provenance più forti.

## Lezione

Non derivare una reputazione globale "Qwen buono/cattivo". L'evidenza mostra invece che il comportamento cambia con il protocollo operativo: per audit repo la verificabilità sul tree canonico e l'obbligo di provenance sono condizioni decisive. Questa evidenza va usata per routing contestuale e definizione del ruolo, non per una graduatoria assoluta.