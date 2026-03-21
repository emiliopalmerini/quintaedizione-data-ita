package srd

// Spell represents a D&D 5e spell.
type Spell struct {
	ID             string   `json:"id"`
	Name           string   `json:"name"`
	Level          int      `json:"level"`
	School         string   `json:"school"`
	Classes        []string `json:"classes"`
	CastingTime    string   `json:"casting_time"`
	Range          string   `json:"range"`
	Components     string   `json:"components"`
	Duration       string   `json:"duration"`
	Description    string   `json:"description"`
	AtHigherLevels string   `json:"at_higher_levels"`
	Ritual         bool     `json:"ritual"`
	Source         string   `json:"-"`
}

func (s Spell) SearchID() string       { return s.ID }
func (s Spell) SearchTitle() string     { return s.Name }
func (s Spell) SearchKeywords() []string { return s.Classes }
