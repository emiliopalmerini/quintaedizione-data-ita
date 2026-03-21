package srd

// Background represents a D&D 5e character background.
type Background struct {
	ID                 string `json:"id"`
	Name               string `json:"name"`
	AbilityScores      string `json:"ability_scores"`
	Feat               string `json:"feat"`
	SkillProficiencies string `json:"skill_proficiencies"`
	ToolProficiency    string `json:"tool_proficiency"`
	Equipment          string `json:"equipment"`
	Description        string `json:"description"`
	Source             string `json:"-"`
}

func (b Background) SearchID() string        { return b.ID }
func (b Background) SearchTitle() string      { return b.Name }
func (b Background) SearchKeywords() []string { return nil }
