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
