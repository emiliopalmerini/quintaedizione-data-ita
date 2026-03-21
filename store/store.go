package store

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"sort"
	"strings"

	datasrd "github.com/emiliopalmerini/quintaedizione-data-ita/data/srd"
	"github.com/emiliopalmerini/quintaedizione-data-ita/search"
	"github.com/emiliopalmerini/quintaedizione-data-ita/srd"
)

// Store is a read-only in-memory store for all SRD data.
type Store struct {
	spells       []srd.Spell
	spellIndex   map[string]int
	monsters     []srd.Monster
	monsterIndex map[string]int
	classes      []srd.Class
	classIndex   map[string]int
	backgrounds  []srd.Background
	bgIndex      map[string]int
	equipment    []srd.Equipment
	equipIndex   map[string]int
	magicItems   []srd.MagicItem
	miIndex      map[string]int
	feats        []srd.Feat
	featIndex    map[string]int
	rules        []srd.Rule
	ruleIndex    map[string]int
	glossary     []srd.GlossaryEntry
	glossIndex   map[string]int
	species      []srd.Species
	speciesIndex map[string]int
	sources      []srd.Source
	searchSvc    *search.Service
}

// Load creates a Store from the embedded JSON data.
func Load() (*Store, error) {
	return LoadFrom(datasrd.Files)
}

// LoadFrom creates a Store from a custom filesystem (useful for testing).
func LoadFrom(fsys fs.FS) (*Store, error) {
	s := &Store{}

	entries, err := fs.ReadDir(fsys, ".")
	if err != nil {
		return nil, fmt.Errorf("read data directory: %w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		src, err := loadSource(fsys, entry.Name())
		if err != nil {
			continue
		}
		s.sources = append(s.sources, src)

		if err := s.loadSourceData(fsys, entry.Name(), src.ShortName); err != nil {
			return nil, fmt.Errorf("source %s: %w", src.ID, err)
		}
	}

	if len(s.sources) == 0 {
		return nil, fmt.Errorf("no sources found")
	}

	s.buildIndexes()
	s.buildSearch()
	return s, nil
}

func loadSource(fsys fs.FS, dir string) (srd.Source, error) {
	data, err := fs.ReadFile(fsys, dir+"/source.json")
	if err != nil {
		return srd.Source{}, err
	}
	var src srd.Source
	if err := json.Unmarshal(data, &src); err != nil {
		return srd.Source{}, err
	}
	if src.ID == "" {
		return srd.Source{}, fmt.Errorf("source.json missing id")
	}
	return src, nil
}

func (s *Store) loadSourceData(fsys fs.FS, dir, shortName string) error {
	readJSON := func(filename string, v any) error {
		data, err := fs.ReadFile(fsys, dir+"/"+filename)
		if err != nil {
			return err
		}
		return json.Unmarshal(data, v)
	}

	// Spells
	var spells []srd.Spell
	if err := readJSON("spells.json", &spells); err == nil {
		for i := range spells {
			spells[i].Source = shortName
		}
		s.spells = append(s.spells, spells...)
	}

	// Monsters
	var monsters []srd.Monster
	if err := readJSON("monsters.json", &monsters); err == nil {
		for i := range monsters {
			monsters[i].SourceEdition = shortName
		}
		s.monsters = append(s.monsters, monsters...)
	}

	// Classes
	var classes []srd.Class
	if err := readJSON("classes.json", &classes); err == nil {
		for i := range classes {
			classes[i].Source = shortName
		}
		s.classes = append(s.classes, classes...)
	}

	// Backgrounds
	var backgrounds []srd.Background
	if err := readJSON("backgrounds.json", &backgrounds); err == nil {
		for i := range backgrounds {
			backgrounds[i].Source = shortName
		}
		s.backgrounds = append(s.backgrounds, backgrounds...)
	}

	// Equipment
	var equipment []srd.Equipment
	if err := readJSON("equipment.json", &equipment); err == nil {
		for i := range equipment {
			equipment[i].Source = shortName
		}
		s.equipment = append(s.equipment, equipment...)
	}

	// Magic Items
	var magicItems []srd.MagicItem
	if err := readJSON("magic_items.json", &magicItems); err == nil {
		for i := range magicItems {
			magicItems[i].Source = shortName
		}
		s.magicItems = append(s.magicItems, magicItems...)
	}

	// Feats
	var feats []srd.Feat
	if err := readJSON("feats.json", &feats); err == nil {
		for i := range feats {
			feats[i].Source = shortName
		}
		s.feats = append(s.feats, feats...)
	}

	// Rules
	s.loadRules(fsys, dir, shortName)

	// Glossary
	var glossary []srd.GlossaryEntry
	if err := readJSON("glossary.json", &glossary); err == nil {
		for i := range glossary {
			glossary[i].Source = shortName
		}
		s.glossary = append(s.glossary, glossary...)
	}

	// Species
	var species []srd.Species
	if err := readJSON("species.json", &species); err == nil {
		for i := range species {
			species[i].Source = shortName
		}
		s.species = append(s.species, species...)
	}

	return nil
}

func (s *Store) loadRules(fsys fs.FS, dir, shortName string) {
	entries, err := fs.ReadDir(fsys, dir)
	if err != nil {
		return
	}

	for _, e := range entries {
		name := e.Name()
		if !strings.HasPrefix(name, "rules_") || !strings.HasSuffix(name, ".json") {
			continue
		}

		data, err := fs.ReadFile(fsys, dir+"/"+name)
		if err != nil {
			continue
		}

		var rules []srd.Rule
		if err := json.Unmarshal(data, &rules); err != nil {
			continue
		}

		for i := range rules {
			rules[i].Source = shortName
		}
		s.rules = append(s.rules, rules...)
	}
}

func (s *Store) buildIndexes() {
	// Sort all slices by name/title first
	sort.Slice(s.spells, func(i, j int) bool { return s.spells[i].Name < s.spells[j].Name })
	sort.Slice(s.monsters, func(i, j int) bool { return s.monsters[i].Name < s.monsters[j].Name })
	sort.Slice(s.classes, func(i, j int) bool { return s.classes[i].Name < s.classes[j].Name })
	sort.Slice(s.backgrounds, func(i, j int) bool { return s.backgrounds[i].Name < s.backgrounds[j].Name })
	sort.Slice(s.equipment, func(i, j int) bool { return s.equipment[i].Name < s.equipment[j].Name })
	sort.Slice(s.magicItems, func(i, j int) bool { return s.magicItems[i].Name < s.magicItems[j].Name })
	sort.Slice(s.feats, func(i, j int) bool { return s.feats[i].Name < s.feats[j].Name })
	sort.Slice(s.rules, func(i, j int) bool { return s.rules[i].Title < s.rules[j].Title })
	sort.Slice(s.glossary, func(i, j int) bool { return s.glossary[i].Term < s.glossary[j].Term })
	sort.Slice(s.species, func(i, j int) bool { return s.species[i].Name < s.species[j].Name })

	// Build indexes after sorting
	s.spellIndex = buildIndex(s.spells, func(v srd.Spell) string { return v.ID })
	s.monsterIndex = buildIndex(s.monsters, func(v srd.Monster) string { return v.ID })
	s.classIndex = buildIndex(s.classes, func(v srd.Class) string { return v.ID })
	s.bgIndex = buildIndex(s.backgrounds, func(v srd.Background) string { return v.ID })
	s.equipIndex = buildIndex(s.equipment, func(v srd.Equipment) string { return v.ID })
	s.miIndex = buildIndex(s.magicItems, func(v srd.MagicItem) string { return v.ID })
	s.featIndex = buildIndex(s.feats, func(v srd.Feat) string { return v.ID })
	s.ruleIndex = buildIndex(s.rules, func(v srd.Rule) string { return v.ID })
	s.glossIndex = buildIndex(s.glossary, func(v srd.GlossaryEntry) string { return v.ID })
	s.speciesIndex = buildIndex(s.species, func(v srd.Species) string { return v.ID })
}

func buildIndex[T any](items []T, id func(T) string) map[string]int {
	idx := make(map[string]int, len(items))
	for i, item := range items {
		idx[id(item)] = i
	}
	return idx
}

// --- Typed accessors ---

func (s *Store) Spells() []srd.Spell           { return s.spells }
func (s *Store) Monsters() []srd.Monster        { return s.monsters }
func (s *Store) Classes() []srd.Class            { return s.classes }
func (s *Store) Backgrounds() []srd.Background   { return s.backgrounds }
func (s *Store) Equipment() []srd.Equipment      { return s.equipment }
func (s *Store) MagicItems() []srd.MagicItem     { return s.magicItems }
func (s *Store) Feats() []srd.Feat               { return s.feats }
func (s *Store) Rules() []srd.Rule               { return s.rules }
func (s *Store) Glossary() []srd.GlossaryEntry   { return s.glossary }
func (s *Store) Species() []srd.Species           { return s.species }
func (s *Store) Sources() []srd.Source             { return s.sources }

func (s *Store) Spell(id string) (srd.Spell, error) {
	return lookup(s.spells, s.spellIndex, id, "spell")
}

func (s *Store) Monster(id string) (srd.Monster, error) {
	return lookup(s.monsters, s.monsterIndex, id, "monster")
}

func (s *Store) Class(id string) (srd.Class, error) {
	return lookup(s.classes, s.classIndex, id, "class")
}

func (s *Store) Background(id string) (srd.Background, error) {
	return lookup(s.backgrounds, s.bgIndex, id, "background")
}

func (s *Store) EquipmentItem(id string) (srd.Equipment, error) {
	return lookup(s.equipment, s.equipIndex, id, "equipment")
}

func (s *Store) MagicItem(id string) (srd.MagicItem, error) {
	return lookup(s.magicItems, s.miIndex, id, "magic item")
}

func (s *Store) Feat(id string) (srd.Feat, error) {
	return lookup(s.feats, s.featIndex, id, "feat")
}

func (s *Store) Rule(id string) (srd.Rule, error) {
	return lookup(s.rules, s.ruleIndex, id, "rule")
}

func (s *Store) GlossaryEntry(id string) (srd.GlossaryEntry, error) {
	return lookup(s.glossary, s.glossIndex, id, "glossary entry")
}

func (s *Store) SpeciesEntry(id string) (srd.Species, error) {
	return lookup(s.species, s.speciesIndex, id, "species")
}

func lookup[T any](items []T, index map[string]int, id, kind string) (T, error) {
	i, ok := index[id]
	if !ok {
		var zero T
		return zero, fmt.Errorf("%s %q not found", kind, id)
	}
	return items[i], nil
}

// Collections returns the names of all loaded SRD collections.
func (s *Store) Collections() []string {
	return srd.AllCollections()
}

// Count returns the number of items in a collection.
func (s *Store) Count(collection string) int {
	switch srd.CollectionName(collection) {
	case srd.Incantesimi:
		return len(s.spells)
	case srd.Mostri:
		return len(s.monsters)
	case srd.Classi:
		return len(s.classes)
	case srd.Backgrounds:
		return len(s.backgrounds)
	case srd.Equipaggiamenti:
		return len(s.equipment)
	case srd.OggettiMagici:
		return len(s.magicItems)
	case srd.Talenti:
		return len(s.feats)
	case srd.Regole:
		return len(s.rules)
	case srd.Glossario:
		return len(s.glossary)
	case srd.Specie:
		return len(s.species)
	default:
		return 0
	}
}

// Search performs a fuzzy search across all collections.
func (s *Store) Search(query string, limitPerCollection int) []search.SearchResultSet {
	return s.searchSvc.Search(query, limitPerCollection)
}

func (s *Store) buildSearch() {
	items := make(map[string][]search.SearchableItem)

	addItems := func(collection string, searchables []srd.Searchable) {
		for _, item := range searchables {
			items[collection] = append(items[collection], search.SearchableItem{
				ID:         item.SearchID(),
				Collection: collection,
				Title:      item.SearchTitle(),
				Keywords:   item.SearchKeywords(),
			})
		}
	}

	addItems(srd.Incantesimi.String(), toSearchable(s.spells))
	addItems(srd.Mostri.String(), toSearchable(s.monsters))
	addItems(srd.Classi.String(), toSearchable(s.classes))
	addItems(srd.Backgrounds.String(), toSearchable(s.backgrounds))
	addItems(srd.Equipaggiamenti.String(), toSearchable(s.equipment))
	addItems(srd.OggettiMagici.String(), toSearchable(s.magicItems))
	addItems(srd.Talenti.String(), toSearchable(s.feats))
	addItems(srd.Regole.String(), toSearchable(s.rules))
	addItems(srd.Glossario.String(), toSearchable(s.glossary))
	addItems(srd.Specie.String(), toSearchable(s.species))

	s.searchSvc = search.NewService(items)
}

func toSearchable[T srd.Searchable](items []T) []srd.Searchable {
	result := make([]srd.Searchable, len(items))
	for i, item := range items {
		result[i] = item
	}
	return result
}
