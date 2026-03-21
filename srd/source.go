package srd

// Source represents metadata about a loaded SRD edition.
type Source struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	ShortName string `json:"short_name"`
	Year      int    `json:"year"`
	Ruleset   string `json:"ruleset"`
	XPSystem  string `json:"xp_system"`
	Default   bool   `json:"default"`
}
