package srd

// ClassFeature represents a class feature gained at a specific level.
type ClassFeature struct {
	Name        string  `json:"name"`
	Level       int     `json:"level"`
	Description Content `json:"description"`
}

// Subclass represents a class specialization.
type Subclass struct {
	Name        string         `json:"name"`
	Description Content        `json:"description"`
	Features    []ClassFeature `json:"features"`
}

// Class represents a D&D 5e character class.
type Class struct {
	ID            string         `json:"id"`
	Name          string         `json:"name"`
	HitDie        string         `json:"hit_die"`
	Proficiencies string         `json:"proficiencies"`
	Description   Content        `json:"description"`
	Features      []ClassFeature `json:"features"`
	Subclasses    []Subclass     `json:"subclasses"`
	SpellList     []string       `json:"spell_list"`
	Source        string         `json:"-"`
}

func (c Class) SearchID() string         { return c.ID }
func (c Class) SearchTitle() string      { return c.Name }
func (c Class) SearchKeywords() []string { return nil }
