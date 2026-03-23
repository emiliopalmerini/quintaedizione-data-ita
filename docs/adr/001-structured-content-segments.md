# ADR-001: Structured Content Segments

**Status:** Accepted
**Date:** 2026-03-23

## Context

All description and free-text fields in our SRD data are plain markdown strings. When a monster's trait references spells (e.g., `*comunione*, *resurrezione*`), or a monster's stat block lists damage resistances (e.g., `"ai Danni radiosi, da fuoco"`), this information is trapped in unstructured text. Consumers cannot programmatically link to the referenced entities.

We want to enrich text fields so that entity references are structured while the surrounding text is preserved for display.

## Decision

Replace plain `string` description fields with an array of **segments**. Each segment is either plain text or a typed entity reference.

### Segment Types

```go
type Segment struct {
    Type string `json:"type"`          // "text" or a reference type
    Text string `json:"text"`          // display text (always present)
    ID   string `json:"id,omitempty"`  // entity ID (only for references)
}
```

Reference types:

| Type             | Refers to                          | Example ID              |
|------------------|------------------------------------|-------------------------|
| `spell`          | Spell entity                       | `comunione`             |
| `damage_type`    | Tipo di danno                      | `fuoco`                 |
| `condition`      | Condizione                         | `avvelenato`            |
| `creature_type`  | Tipo di creatura                   | `celestiale`            |
| `ability`        | Caratteristica (STR, DEX, etc.)    | `forza`                 |
| `skill`          | Competenza                         | `percezione`            |
| `equipment`      | Equipaggiamento/arma               | `spada-lunga`           |
| `rule`           | Regola                             | `attacco-opportunita`   |

### JSON Format

Before:
```json
{
  "name": "Incantesimi innati",
  "description": "Il deva può lanciare i seguenti incantesimi: comunione, rianimare morti"
}
```

After:
```json
{
  "name": "Incantesimi innati",
  "description": [
    {"type": "text", "text": "Il deva può lanciare i seguenti incantesimi: "},
    {"type": "spell", "id": "comunione", "text": "comunione"},
    {"type": "text", "text": ", "},
    {"type": "spell", "id": "rianimare-morti", "text": "rianimare morti"}
  ]
}
```

### Scope: Affected Fields

| Entity      | Fields                                                                                  |
|-------------|-----------------------------------------------------------------------------------------|
| Monster     | Traits[].description, Actions[].description, BonusActions[].description, Reactions[].description, LegendaryActions[].description, Resistances, DamageImmunities, ConditionImmunities |
| Spell       | Description, AtHigherLevels                                                             |
| Class       | Description, Features[].description, Subclasses[].description, Subclasses[].features[].description |
| Feat        | Benefit, Prerequisite                                                                   |
| MagicItem   | Description                                                                             |
| Equipment   | Description                                                                             |
| Background  | Description                                                                             |
| Species     | Description, Traits[].description                                                       |
| Rule        | Content                                                                                 |
| Glossary    | Definition                                                                              |

### Go Type: `Content`

Named type `Content = []Segment` replaces `string` in description fields.

Helpers:
- `Content.PlainText() string` — concatenates all `.Text` fields for search/display

## Implementation Plan

1. **Go types**: Define `Segment` and `Content` in `srd/` with marshal/unmarshal and `PlainText()`
2. **Migrate structs**: Change affected fields from `string` to `Content`
3. **Fix consumers**: Update Store, search indexing, and filters to use `PlainText()` where needed
4. **Python parsers**: Update `scripts/parse_srd/` to emit `[]Segment` JSON
5. **Regenerate JSON**: Re-run parsers to produce structured data

Steps 1-3 first (Go library). Steps 4-5 after (parser changes). No backward compatibility with plain string JSON — this is a breaking change.

## Consequences

- **Pro**: Consumers can programmatically resolve entity references
- **Pro**: `PlainText()` helper for consumers that don't need structure
- **Con**: JSON more verbose (mitigated by embedding + generation)
- **Con**: Python parsers need updating (one-time effort)
- **Con**: Breaking API change for Go consumers on description fields (mitigated by `Content` helpers)
