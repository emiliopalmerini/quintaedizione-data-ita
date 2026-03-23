package srd

// SpeciesTrait represents a racial/species trait.
type SpeciesTrait struct {
	Name        string  `json:"name"`
	Description Content `json:"description"`
}

// Species represents a D&D 5e playable species.
type Species struct {
	ID           string         `json:"id"`
	Name         string         `json:"name"`
	CreatureType string         `json:"creature_type"`
	Size         string         `json:"size"`
	Speed        string         `json:"speed"`
	Traits       []SpeciesTrait `json:"traits"`
	Description  Content        `json:"description"`
	Source       string         `json:"-"`
}

func (s Species) SearchID() string         { return s.ID }
func (s Species) SearchTitle() string      { return s.Name }
func (s Species) SearchKeywords() []string { return []string{s.CreatureType} }

func (s Species) FilterValue(field string) any {
	switch field {
	case "tipo_creatura":
		return s.CreatureType
	case "taglia":
		return s.Size
	default:
		return nil
	}
}
