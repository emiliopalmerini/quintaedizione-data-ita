# quintaedizione-data-ita

Shared Go module providing D&D 5e Italian SRD data as typed Go structs with embedded JSON.

## Build & Run

```bash
make test      # Format, vet, and run tests
make format    # Format Go code
make vet       # Run go vet
```

## Prerequisites

- Go 1.25.2

## Architecture

Central Store pattern with typed accessors. Data is embedded as JSON at compile time and loaded into an in-memory store at startup.

```
data/
  srd/           Embedded SRD JSON (srd-5e, srd-5.5e)
  mappe/         Embedded map gallery JSON
  generatori/    Embedded random generator JSON
  encounter/     Embedded encounter XP table JSON
srd/             Typed entity structs (Spell, Monster, Class, etc.)
encounter/       Encounter calculator (Party, XP calculation)
maps/            Map gallery entity (Mappa)
generators/      Random table types (Table, Column, Item)
store/           Central Store (Load, typed accessors, search)
search/          Fuzzy search service
filters/         Filter definitions and predicate builder
```

## Data Format

- All entity structs expose raw data with JSON tags
- Content fields contain raw markdown (no HTML rendering)
- Consumers are responsible for rendering markdown to their preferred format

## Testing

```bash
make test
go test -race ./...
go test -v ./store/...
```
