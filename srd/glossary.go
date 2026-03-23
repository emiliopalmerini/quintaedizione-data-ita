package srd

// GlossaryEntry represents a D&D 5e glossary term.
type GlossaryEntry struct {
	ID         string   `json:"id"`
	Term       string   `json:"term"`
	Category   string   `json:"category"`
	Definition Content  `json:"definition"`
	SeeAlso    []string `json:"see_also"`
	Source     string   `json:"-"`
}

func (g GlossaryEntry) SearchID() string         { return g.ID }
func (g GlossaryEntry) SearchTitle() string      { return g.Term }
func (g GlossaryEntry) SearchKeywords() []string { return g.SeeAlso }

func (g GlossaryEntry) FilterValue(field string) any {
	switch field {
	case "categoria":
		return g.Category
	default:
		return nil
	}
}
