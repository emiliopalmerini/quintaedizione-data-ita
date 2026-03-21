# quintaedizione-data-ita

Modulo Go condiviso che fornisce i dati del Systems Reference Document (SRD) di D&D 5a Edizione in italiano, come struct Go tipizzate con JSON embeddato.

## Prerequisiti

- Go 1.25.2

## Comandi

| Comando        | Descrizione                      |
|----------------|----------------------------------|
| `make test`    | Formatta, vet, esegue i test     |
| `make format`  | Formatta il codice Go            |
| `make vet`     | Esegue go vet                    |

## Come funziona

```
PDF SRD → Parser Python → JSON → Go module (embed.FS) → Store in-memory
```

I file JSON in `data/` vengono embeddati nel binario a compile time. Nessun database esterno: tutto vive in memoria. I consumatori importano il modulo e accedono ai dati tramite lo Store centrale.

**Contenuti**: incantesimi, mostri, animali, classi, background, equipaggiamenti, oggetti magici, armi, armature, strumenti, cavalcature e veicoli, servizi, talenti, regole, mappe, generatori di tabelle casuali, tabelle XP per incontri.

## Struttura del progetto

```
data/
  srd/           JSON SRD embeddato (srd-5e, srd-5.5e)
  mappe/         JSON galleria mappe
  generatori/    JSON generatori casuali
  encounter/     JSON tabelle XP incontri
srd/             Struct tipizzate (Spell, Monster, Class, etc.)
encounter/       Calcolatore incontri (Party, calcolo XP)
maps/            Entità galleria mappe (Mappa)
generators/      Tipi tabelle casuali (Table, Column, Item)
store/           Store centrale (Load, accessor tipizzati, ricerca)
search/          Servizio di ricerca fuzzy
filters/         Definizioni filtri e predicate builder
scripts/         Script di generazione dati e parser
```

## Formato dati

- Tutte le struct espongono dati grezzi con tag JSON
- I campi di contenuto contengono markdown grezzo (nessun rendering HTML)
- I consumatori sono responsabili del rendering markdown nel formato preferito

## Licenza

- **Codice**: [BSD 3-Clause](LICENSE)
- **Contenuto SRD**: [Creative Commons Attribution 4.0 (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/) di Wizards of the Coast
