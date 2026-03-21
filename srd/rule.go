package srd

// Rule represents a D&D 5e rule entry.
type Rule struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Content  string `json:"content"`
	Children []Rule `json:"children"`
	Source   string `json:"-"`
}

func (r Rule) SearchID() string         { return r.ID }
func (r Rule) SearchTitle() string      { return r.Title }
func (r Rule) SearchKeywords() []string { return nil }
