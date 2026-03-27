//go:build quality

package store

import (
	"fmt"
	"regexp"
	"strings"
	"testing"

	"github.com/emiliopalmerini/quintaedizione-data-ita/srd"
)

// qualityIssue tracks a data quality problem for reporting.
type qualityIssue struct {
	collection string
	entity     string
	field      string
	message    string
}

func (q qualityIssue) String() string {
	return fmt.Sprintf("[%s] %s.%s: %s", q.collection, q.entity, q.field, q.message)
}

// qualityReport collects issues and reports them at the end.
type qualityReport struct {
	issues []qualityIssue
}

func (r *qualityReport) add(collection, entity, field, message string) {
	r.issues = append(r.issues, qualityIssue{collection, entity, field, message})
}

func (r *qualityReport) report(t *testing.T) {
	t.Helper()
	for _, issue := range r.issues {
		t.Errorf("%s", issue)
	}
	if len(r.issues) > 0 {
		t.Logf("total quality issues: %d", len(r.issues))
	}
}

// --- Content checks ---

var (
	doubleSpaceRe    = regexp.MustCompile(`  +`)
	orphanMarkdownRe = regexp.MustCompile(`(?:^|[\s(])_?\*\*_?$|^_?\*\*_?(?:[\s)]|$)`)
	trailingSpaceRe  = regexp.MustCompile(`\s+$`)
	leadingSpaceRe   = regexp.MustCompile(`^\s+`)
)

func checkContent(r *qualityReport, collection, entity, field string, content srd.Content) {
	for i, seg := range content {
		prefix := fmt.Sprintf("segment[%d]", i)

		if seg.Type == "" {
			r.add(collection, entity, field, prefix+": empty type")
		}

		if seg.Type != "text" && seg.ID == "" {
			r.add(collection, entity, field, prefix+fmt.Sprintf(": ref segment type=%q has no ID", seg.Type))
		}

		if seg.Text == "" && seg.Type == "text" {
			r.add(collection, entity, field, prefix+": empty text segment")
		}

		if doubleSpaceRe.MatchString(seg.Text) {
			r.add(collection, entity, field, prefix+": double spaces in "+truncate(seg.Text, 60))
		}

		if orphanMarkdownRe.MatchString(seg.Text) {
			r.add(collection, entity, field, prefix+": orphan markdown in "+truncate(seg.Text, 60))
		}

		if seg.Type == "text" {
			if i == 0 && leadingSpaceRe.MatchString(seg.Text) && strings.TrimSpace(seg.Text) != "" {
				r.add(collection, entity, field, prefix+": leading whitespace")
			}
			if i == len(content)-1 && trailingSpaceRe.MatchString(seg.Text) {
				r.add(collection, entity, field, prefix+": trailing whitespace")
			}
		}
	}
}

// checkContentRefs validates that entity references in Content point to existing entities.
func checkContentRefs(r *qualityReport, s *Store, collection, entity, field string, content srd.Content) {
	for _, seg := range content {
		switch seg.Type {
		case "text":
			continue
		case "spell":
			if _, err := s.Spell(seg.ID); err != nil {
				r.add(collection, entity, field, fmt.Sprintf("broken spell ref: %q", seg.ID))
			}
		case "condition":
			if _, err := s.GlossaryEntry(seg.ID); err != nil {
				r.add(collection, entity, field, fmt.Sprintf("broken condition ref: %q", seg.ID))
			}
		}
	}
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return fmt.Sprintf("%q", s)
	}
	return fmt.Sprintf("%q...", s[:n])
}

// --- Required field checks ---

func requireNonEmpty(r *qualityReport, collection, entity, field, value string) {
	if strings.TrimSpace(value) == "" {
		r.add(collection, entity, field, "empty required field")
	}
}

func requireNonEmptyContent(r *qualityReport, collection, entity, field string, content srd.Content) {
	if len(content) == 0 {
		r.add(collection, entity, field, "empty required content")
		return
	}
	if strings.TrimSpace(content.PlainText()) == "" {
		r.add(collection, entity, field, "content has no visible text")
	}
}

// --- Duplicate checks ---

type sourceID struct {
	id, source string
}

// checkDuplicateIDs reports IDs that appear more than once within the same source edition.
func checkDuplicateIDs(r *qualityReport, collection string, entries []sourceID) {
	// Count per (source, id) pair
	type key struct{ source, id string }
	seen := make(map[key]int, len(entries))
	for _, e := range entries {
		seen[key{e.source, e.id}]++
	}
	for k, count := range seen {
		if count > 1 {
			r.add(collection, k.id, "id", fmt.Sprintf("duplicate ID in %s (%d occurrences)", k.source, count))
		}
	}
}

// --- Self-reference check for spells ---

func checkSpellSelfRef(r *qualityReport, spellID string, content srd.Content) {
	for _, seg := range content {
		if seg.Type == "spell" && seg.ID == spellID {
			r.add("incantesimi", spellID, "description", "spell references itself")
			return
		}
	}
}

// --- Main test ---

func TestDataQuality(t *testing.T) {
	s, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}

	r := &qualityReport{}

	t.Run("spells", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, spell := range s.Spells() {
			ids = append(ids, sourceID{spell.ID, spell.Source})
			requireNonEmpty(sr, "incantesimi", spell.ID, "id", spell.ID)
			requireNonEmpty(sr, "incantesimi", spell.ID, "name", spell.Name)
			requireNonEmpty(sr, "incantesimi", spell.ID, "school", spell.School)
			requireNonEmpty(sr, "incantesimi", spell.ID, "casting_time", spell.CastingTime)
			requireNonEmpty(sr, "incantesimi", spell.ID, "range", spell.Range)
			requireNonEmpty(sr, "incantesimi", spell.ID, "duration", spell.Duration)
			requireNonEmptyContent(sr, "incantesimi", spell.ID, "description", spell.Description)
			checkContent(sr, "incantesimi", spell.ID, "description", spell.Description)
			checkContent(sr, "incantesimi", spell.ID, "at_higher_levels", spell.AtHigherLevels)
			checkContentRefs(sr, s, "incantesimi", spell.ID, "description", spell.Description)
			checkSpellSelfRef(sr, spell.ID, spell.Description)
		}
		checkDuplicateIDs(sr, "incantesimi", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("monsters", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, m := range s.Monsters() {
			ids = append(ids, sourceID{m.ID, m.SourceEdition})
			requireNonEmpty(sr, "mostri", m.ID, "id", m.ID)
			requireNonEmpty(sr, "mostri", m.ID, "name", m.Name)
			requireNonEmpty(sr, "mostri", m.ID, "type", m.Type)
			requireNonEmpty(sr, "mostri", m.ID, "size", m.Size)
			requireNonEmpty(sr, "mostri", m.ID, "cr", m.CR)
			requireNonEmpty(sr, "mostri", m.ID, "ac", m.AC)
			requireNonEmpty(sr, "mostri", m.ID, "hp", m.HP)

			// Check all content fields
			checkContent(sr, "mostri", m.ID, "resistances", m.Resistances)
			checkContent(sr, "mostri", m.ID, "damage_immunities", m.DamageImmunities)
			checkContent(sr, "mostri", m.ID, "condition_immunities", m.ConditionImmunities)

			// Check features
			for _, feat := range m.Traits {
				requireNonEmpty(sr, "mostri", m.ID, "traits.name", feat.Name)
				checkContent(sr, "mostri", m.ID, "traits."+feat.Name, feat.Description)
				checkContentRefs(sr, s, "mostri", m.ID, "traits."+feat.Name, feat.Description)
			}
			for _, feat := range m.Actions {
				requireNonEmpty(sr, "mostri", m.ID, "actions.name", feat.Name)
				checkContent(sr, "mostri", m.ID, "actions."+feat.Name, feat.Description)
				checkContentRefs(sr, s, "mostri", m.ID, "actions."+feat.Name, feat.Description)
			}
			for _, feat := range m.BonusActions {
				checkContent(sr, "mostri", m.ID, "bonus_actions."+feat.Name, feat.Description)
				checkContentRefs(sr, s, "mostri", m.ID, "bonus_actions."+feat.Name, feat.Description)
			}
			for _, feat := range m.Reactions {
				checkContent(sr, "mostri", m.ID, "reactions."+feat.Name, feat.Description)
				checkContentRefs(sr, s, "mostri", m.ID, "reactions."+feat.Name, feat.Description)
			}
			for _, feat := range m.LegendaryActions {
				checkContent(sr, "mostri", m.ID, "legendary_actions."+feat.Name, feat.Description)
				checkContentRefs(sr, s, "mostri", m.ID, "legendary_actions."+feat.Name, feat.Description)
			}
		}
		checkDuplicateIDs(sr, "mostri", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("classes", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, c := range s.Classes() {
			ids = append(ids, sourceID{c.ID, c.Source})
			requireNonEmpty(sr, "classi", c.ID, "id", c.ID)
			requireNonEmpty(sr, "classi", c.ID, "name", c.Name)
			requireNonEmpty(sr, "classi", c.ID, "hit_die", c.HitDie)
			requireNonEmptyContent(sr, "classi", c.ID, "description", c.Description)
			checkContent(sr, "classi", c.ID, "description", c.Description)

			for _, feat := range c.Features {
				requireNonEmpty(sr, "classi", c.ID, "features.name", feat.Name)
				checkContent(sr, "classi", c.ID, "features."+feat.Name, feat.Description)
			}
			for _, sub := range c.Subclasses {
				requireNonEmpty(sr, "classi", c.ID, "subclasses.name", sub.Name)
				checkContent(sr, "classi", c.ID, "subclasses."+sub.Name, sub.Description)
				for _, feat := range sub.Features {
					checkContent(sr, "classi", c.ID, "subclasses."+sub.Name+"."+feat.Name, feat.Description)
				}
			}
		}
		checkDuplicateIDs(sr, "classi", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("backgrounds", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, b := range s.Backgrounds() {
			ids = append(ids, sourceID{b.ID, b.Source})
			requireNonEmpty(sr, "backgrounds", b.ID, "id", b.ID)
			requireNonEmpty(sr, "backgrounds", b.ID, "name", b.Name)
			requireNonEmptyContent(sr, "backgrounds", b.ID, "description", b.Description)
			checkContent(sr, "backgrounds", b.ID, "description", b.Description)
		}
		checkDuplicateIDs(sr, "backgrounds", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("equipment", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, e := range s.Equipment() {
			ids = append(ids, sourceID{e.ID, e.Source})
			requireNonEmpty(sr, "equipaggiamenti", e.ID, "id", e.ID)
			requireNonEmpty(sr, "equipaggiamenti", e.ID, "name", e.Name)
			requireNonEmpty(sr, "equipaggiamenti", e.ID, "category", e.Category)
			checkContent(sr, "equipaggiamenti", e.ID, "description", e.Description)
		}
		checkDuplicateIDs(sr, "equipaggiamenti", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("magic_items", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, mi := range s.MagicItems() {
			ids = append(ids, sourceID{mi.ID, mi.Source})
			requireNonEmpty(sr, "oggetti_magici", mi.ID, "id", mi.ID)
			requireNonEmpty(sr, "oggetti_magici", mi.ID, "name", mi.Name)
			requireNonEmpty(sr, "oggetti_magici", mi.ID, "type", mi.Type)
			requireNonEmpty(sr, "oggetti_magici", mi.ID, "rarity", mi.Rarity)
			requireNonEmptyContent(sr, "oggetti_magici", mi.ID, "description", mi.Description)
			checkContent(sr, "oggetti_magici", mi.ID, "description", mi.Description)
			checkContentRefs(sr, s, "oggetti_magici", mi.ID, "description", mi.Description)
		}
		checkDuplicateIDs(sr, "oggetti_magici", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("feats", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, f := range s.Feats() {
			ids = append(ids, sourceID{f.ID, f.Source})
			requireNonEmpty(sr, "talenti", f.ID, "id", f.ID)
			requireNonEmpty(sr, "talenti", f.ID, "name", f.Name)
			requireNonEmptyContent(sr, "talenti", f.ID, "benefit", f.Benefit)
			checkContent(sr, "talenti", f.ID, "benefit", f.Benefit)
			checkContent(sr, "talenti", f.ID, "prerequisite", f.Prerequisite)
		}
		checkDuplicateIDs(sr, "talenti", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("rules", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		var checkRules func(rules []srd.Rule, parentSource string)
		checkRules = func(rules []srd.Rule, parentSource string) {
			for _, rule := range rules {
				source := rule.Source
				if source == "" {
					source = parentSource
				}
				ids = append(ids, sourceID{rule.ID, source})
				requireNonEmpty(sr, "regole", rule.ID, "id", rule.ID)
				requireNonEmpty(sr, "regole", rule.ID, "title", rule.Title)
				checkContent(sr, "regole", rule.ID, "content", rule.Content)
				checkRules(rule.Children, source)
			}
		}
		checkRules(s.Rules(), "")
		checkDuplicateIDs(sr, "regole", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("species", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, sp := range s.Species() {
			ids = append(ids, sourceID{sp.ID, sp.Source})
			requireNonEmpty(sr, "specie", sp.ID, "id", sp.ID)
			requireNonEmpty(sr, "specie", sp.ID, "name", sp.Name)
			checkContent(sr, "specie", sp.ID, "description", sp.Description)
			for _, trait := range sp.Traits {
				requireNonEmpty(sr, "specie", sp.ID, "traits.name", trait.Name)
				checkContent(sr, "specie", sp.ID, "traits."+trait.Name, trait.Description)
			}
		}
		checkDuplicateIDs(sr, "specie", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("glossary", func(t *testing.T) {
		sr := &qualityReport{}
		var ids []sourceID
		for _, g := range s.Glossary() {
			ids = append(ids, sourceID{g.ID, g.Source})
			requireNonEmpty(sr, "glossario", g.ID, "id", g.ID)
			requireNonEmpty(sr, "glossario", g.ID, "term", g.Term)
			requireNonEmptyContent(sr, "glossario", g.ID, "definition", g.Definition)
			checkContent(sr, "glossario", g.ID, "definition", g.Definition)
		}
		checkDuplicateIDs(sr, "glossario", ids)
		r.issues = append(r.issues, sr.issues...)
		sr.report(t)
	})

	t.Run("summary", func(t *testing.T) {
		if len(r.issues) > 0 {
			t.Logf("=== DATA QUALITY SUMMARY: %d issues found ===", len(r.issues))

			// Group by collection
			byCollection := map[string]int{}
			byType := map[string]int{}
			for _, issue := range r.issues {
				byCollection[issue.collection]++
				// Categorize by type of issue
				switch {
				case strings.Contains(issue.message, "double spaces"):
					byType["double_spaces"]++
				case strings.Contains(issue.message, "orphan markdown"):
					byType["orphan_markdown"]++
				case strings.Contains(issue.message, "empty required"):
					byType["missing_fields"]++
				case strings.Contains(issue.message, "duplicate ID"):
					byType["duplicate_ids"]++
				case strings.Contains(issue.message, "broken"):
					byType["broken_refs"]++
				case strings.Contains(issue.message, "self-ref") || strings.Contains(issue.message, "references itself"):
					byType["self_refs"]++
				case strings.Contains(issue.message, "whitespace"):
					byType["whitespace"]++
				default:
					byType["other"]++
				}
			}

			t.Log("By collection:")
			for col, count := range byCollection {
				t.Logf("  %-20s %d", col, count)
			}
			t.Log("By issue type:")
			for typ, count := range byType {
				t.Logf("  %-20s %d", typ, count)
			}
		}
	})
}
