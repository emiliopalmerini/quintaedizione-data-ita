package srd

// Feat represents a D&D 5e feat.
type Feat struct {
	ID           string `json:"id"`
	Name         string `json:"name"`
	Category     string `json:"category"`
	Prerequisite Content `json:"prerequisite"`
	Repeatable   bool    `json:"repeatable"`
	Benefit      Content `json:"benefit"`
	Source       string `json:"-"`
}

func (f Feat) SearchID() string         { return f.ID }
func (f Feat) SearchTitle() string      { return f.Name }
func (f Feat) SearchKeywords() []string { return []string{f.Category} }

func (f Feat) FilterValue(field string) any {
	switch field {
	case "categoria":
		return f.Category
	default:
		return nil
	}
}
