package srd

// Equipment represents a D&D 5e equipment item.
type Equipment struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Category    string            `json:"category"`
	Subcategory string            `json:"subcategory"`
	Properties  map[string]string `json:"properties"`
	Description string            `json:"description"`
	Source      string            `json:"-"`
}

func (e Equipment) SearchID() string        { return e.ID }
func (e Equipment) SearchTitle() string      { return e.Name }
func (e Equipment) SearchKeywords() []string { return []string{e.Category, e.Subcategory} }
