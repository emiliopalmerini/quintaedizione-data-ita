package srd

// Feature represents a named ability or action with a description.
type Feature struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

// Monster represents a D&D 5e monster or creature.
type Monster struct {
	ID                  string            `json:"id"`
	Name                string            `json:"name"`
	Type                string            `json:"type"`
	Size                string            `json:"size"`
	Alignment           string            `json:"alignment"`
	CR                  string            `json:"cr"`
	CRDetail            string            `json:"cr_detail"`
	Source              string            `json:"source"`
	AC                  string            `json:"ac"`
	Initiative          string            `json:"initiative"`
	HP                  string            `json:"hp"`
	Speed               string            `json:"speed"`
	Skills              string            `json:"skills"`
	Resistances         string            `json:"resistances"`
	DamageImmunities    string            `json:"damage_immunities"`
	ConditionImmunities string            `json:"condition_immunities"`
	Senses              string            `json:"senses"`
	Languages           string            `json:"languages"`
	Equipment           string            `json:"equipment"`
	Traits              []Feature         `json:"traits"`
	Actions             []Feature         `json:"actions"`
	BonusActions        []Feature         `json:"bonus_actions"`
	Reactions           []Feature         `json:"reactions"`
	LegendaryActions    []Feature         `json:"legendary_actions"`
	Group               string            `json:"group"`
	AbilityScores       map[string]int    `json:"ability_scores"`
	AbilityMods         map[string]int    `json:"ability_mods"`
	SavingThrows        map[string]string `json:"saving_throws"`
	SourceEdition       string            `json:"-"`
}

func (m Monster) SearchID() string         { return m.ID }
func (m Monster) SearchTitle() string      { return m.Name }
func (m Monster) SearchKeywords() []string { return []string{m.Type, m.CR} }

func (m Monster) FilterValue(field string) any {
	switch field {
	case "tipo":
		return m.Type
	case "taglia":
		return m.Size
	case "allineamento":
		return m.Alignment
	case "grado_sfida":
		return m.CR
	default:
		return nil
	}
}
