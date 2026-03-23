package srd

// MagicItem represents a D&D 5e magic item.
type MagicItem struct {
	ID                string `json:"id"`
	Name              string `json:"name"`
	Type              string `json:"type"`
	Rarity            string `json:"rarity"`
	Attunement        bool   `json:"attunement"`
	AttunementDetails string `json:"attunement_details"`
	Description       Content `json:"description"`
	Source            string `json:"-"`
}

func (m MagicItem) SearchID() string         { return m.ID }
func (m MagicItem) SearchTitle() string      { return m.Name }
func (m MagicItem) SearchKeywords() []string { return []string{m.Type, m.Rarity} }

func (m MagicItem) FilterValue(field string) any {
	switch field {
	case "rarita":
		return m.Rarity
	case "tipo":
		return m.Type
	default:
		return nil
	}
}
