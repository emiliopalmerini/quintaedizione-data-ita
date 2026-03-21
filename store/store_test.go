package store

import (
	"testing"

	"github.com/emiliopalmerini/quintaedizione-data-ita/srd"
)

func TestLoad(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	// Verify sources were loaded
	if len(s.Sources()) == 0 {
		t.Fatal("expected at least one source")
	}

	// Verify all collections have data
	collections := map[string]int{
		"incantesimi":     len(s.Spells()),
		"mostri":          len(s.Monsters()),
		"classi":          len(s.Classes()),
		"backgrounds":     len(s.Backgrounds()),
		"equipaggiamenti": len(s.Equipment()),
		"oggetti_magici":  len(s.MagicItems()),
		"talenti":         len(s.Feats()),
		"regole":          len(s.Rules()),
		"glossario":       len(s.Glossary()),
		"specie":          len(s.Species()),
	}

	for name, count := range collections {
		if count == 0 {
			t.Errorf("collection %q has no items", name)
		}
		if s.Count(name) != count {
			t.Errorf("Count(%q) = %d, want %d", name, s.Count(name), count)
		}
	}
}

func TestSpellLookup(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	// Spells should be sorted by name
	spells := s.Spells()
	for i := 1; i < len(spells); i++ {
		if spells[i].Name < spells[i-1].Name {
			t.Errorf("spells not sorted: %q before %q", spells[i-1].Name, spells[i].Name)
			break
		}
	}

	// Lookup by ID should work
	if len(spells) > 0 {
		first := spells[0]
		got, err := s.Spell(first.ID)
		if err != nil {
			t.Fatalf("Spell(%q) error: %v", first.ID, err)
		}
		if got.Name != first.Name {
			t.Errorf("Spell(%q).Name = %q, want %q", first.ID, got.Name, first.Name)
		}
	}

	// Lookup unknown ID should error
	_, err = s.Spell("nonexistent-spell-xyz")
	if err == nil {
		t.Error("expected error for unknown spell ID")
	}
}

func TestMonsterLookup(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	monsters := s.Monsters()
	if len(monsters) > 0 {
		first := monsters[0]
		got, err := s.Monster(first.ID)
		if err != nil {
			t.Fatalf("Monster(%q) error: %v", first.ID, err)
		}
		if got.Name != first.Name {
			t.Errorf("Monster(%q).Name = %q, want %q", first.ID, got.Name, first.Name)
		}
	}
}

func TestCollections(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	collections := s.Collections()
	if len(collections) != len(srd.Registry) {
		t.Errorf("Collections() returned %d, want %d", len(collections), len(srd.Registry))
	}

	// Should be sorted
	for i := 1; i < len(collections); i++ {
		if collections[i] < collections[i-1] {
			t.Errorf("collections not sorted: %q before %q", collections[i-1], collections[i])
			break
		}
	}
}

func TestSearch(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	results := s.Search("fuoco", 5)
	if len(results) == 0 {
		t.Fatal("expected search results for 'fuoco'")
	}

	// Verify results have scores
	for _, set := range results {
		for _, r := range set.Results {
			if r.Score <= 0 {
				t.Errorf("result %q has non-positive score %d", r.Title, r.Score)
			}
		}
	}

	// Empty query returns nil
	empty := s.Search("", 5)
	if empty != nil {
		t.Error("expected nil for empty query")
	}
}

func TestMappe(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	mappe := s.Mappe()
	if len(mappe) == 0 {
		t.Fatal("expected maps to be loaded")
	}

	// Lookup by slug
	first := mappe[0]
	got, err := s.Mappa(first.Slug)
	if err != nil {
		t.Fatalf("Mappa(%q) error: %v", first.Slug, err)
	}
	if got.Nome != first.Nome {
		t.Errorf("Mappa(%q).Nome = %q, want %q", first.Slug, got.Nome, first.Nome)
	}

	// Tags
	tags := s.MappeTags()
	if len(tags) == 0 {
		t.Error("expected map tags")
	}
}

func TestGenerators(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	tables := s.GeneratorTables()
	if len(tables) == 0 {
		t.Fatal("expected generator tables to be loaded")
	}

	// Lookup by ID
	first := tables[0]
	got, err := s.GeneratorTable(first.ID)
	if err != nil {
		t.Fatalf("GeneratorTable(%q) error: %v", first.ID, err)
	}
	if got.Name != first.Name {
		t.Errorf("GeneratorTable(%q).Name = %q, want %q", first.ID, got.Name, first.Name)
	}
}

func TestXPTables(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	xp := s.XPTables()
	if xp == nil {
		t.Fatal("expected XP tables to be loaded")
	}

	// Test 2024 XP
	val, err := xp.GetXPFor2024(5, "High")
	if err != nil {
		t.Fatalf("GetXPFor2024(5, High) error: %v", err)
	}
	if val != 1100 {
		t.Errorf("GetXPFor2024(5, High) = %d, want 1100", val)
	}

	// Test 2014 threshold
	threshold, err := xp.GetThresholdFor2014(1, "Facile")
	if err != nil {
		t.Fatalf("GetThresholdFor2014(1, Facile) error: %v", err)
	}
	if threshold != 25 {
		t.Errorf("GetThresholdFor2014(1, Facile) = %d, want 25", threshold)
	}

	// Test multiplier
	mult, err := xp.GetMultiplierFor2014(2)
	if err != nil {
		t.Fatalf("GetMultiplierFor2014(2) error: %v", err)
	}
	if mult != 1.5 {
		t.Errorf("GetMultiplierFor2014(2) = %f, want 1.5", mult)
	}
}

func TestSearchable(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	// Verify Searchable interface is implemented
	spells := s.Spells()
	if len(spells) > 0 {
		var searchable srd.Searchable = spells[0]
		if searchable.SearchID() == "" {
			t.Error("SearchID() returned empty string")
		}
		if searchable.SearchTitle() == "" {
			t.Error("SearchTitle() returned empty string")
		}
	}
}
