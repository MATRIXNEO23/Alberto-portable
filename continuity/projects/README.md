# Project-partitioned continuity

Questo layer conserva il **filo operativo** dei progetti senza affidarlo alla memoria volatile dell'istanza.

## Struttura

```text
continuity/projects/<project_id>/
  LIVE_CONTEXT.json
  micro-checkpoints/YYYY/MM/DD/<checkpoint_id>.json
```

- I micro-checkpoint sono **immutabili**.
- `LIVE_CONTEXT.json` è solo un puntatore derivato all'ultimo checkpoint; non è una seconda fonte di verità.
- Ogni progetto vive nella propria directory.
- Il checkpoint conserva contesto operativo; la repository/fonte canonica resta la verità live.
- Se il progetto usa un recovery dedicato, come GPTina quando applicabile, non usare questo layer come sostituto.

## Quando creare un checkpoint

Crearlo a transizioni materiali, non a ogni messaggio:

- milestone verificata;
- correzione importante;
- handoff;
- cambio progetto;
- cambio istanza;
- interruzione di un lavoro lungo che dovrà essere ripreso.

## Contenuto minimo

Un checkpoint deve contenere:

- repository, branch e HEAD osservati;
- obiettivo corrente;
- lavoro completato;
- fatti verificati;
- fatti ancora non verificati;
- decisioni;
- correzioni;
- vincoli attivi;
- componenti toccati;
- open loop;
- prossima azione;
- rischi di regressione;
- provenance.

## Comandi

Scrittura:

```bash
python tools/project_continuity.py checkpoint \
  --project filum \
  --input checkpoint.json
```

Recovery:

```bash
python tools/project_continuity.py recover --project filum
```

Audit:

```bash
python tools/project_continuity.py audit --project filum
```

## Regola di recovery

```text
identifica project_id
-> recupera SOLO quel progetto
-> verifica stato live della fonte canonica
-> riconcilia eventuali differenze
-> continua dal punto verificato
```

Il checkpoint non autorizza mai a saltare la verifica live della repository quando il task dipende dallo stato corrente.
