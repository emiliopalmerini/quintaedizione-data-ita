package encounter

import (
	"errors"
	"fmt"
	"strings"
)

// Ruleset represents the D&D ruleset version.
type Ruleset string

const (
	Ruleset2024 Ruleset = "2024"
	Ruleset2014 Ruleset = "2014"
)

// NewRuleset creates and validates a new Ruleset.
func NewRuleset(value string) (Ruleset, error) {
	switch strings.ToLower(value) {
	case "2024":
		return Ruleset2024, nil
	case "2014":
		return Ruleset2014, nil
	default:
		return "", errors.New("invalid ruleset: must be '2024' or '2014'")
	}
}

func (r Ruleset) String() string { return string(r) }
func (r Ruleset) IsValid() bool  { return r == Ruleset2024 || r == Ruleset2014 }

// Difficulty represents encounter difficulty.
type Difficulty string

const (
	DifficultyLow      Difficulty = "Low"
	DifficultyModerate Difficulty = "Moderate"
	DifficultyHigh     Difficulty = "High"
	DifficultyEasy     Difficulty = "Facile"
	DifficultyMedium   Difficulty = "Media"
	DifficultyHard     Difficulty = "Difficile"
	DifficultyDeadly   Difficulty = "Letale"
)

// NewDifficulty creates and validates a new Difficulty for the given ruleset.
func NewDifficulty(value string, ruleset Ruleset) (Difficulty, error) {
	d := Difficulty(value)
	switch ruleset {
	case Ruleset2024:
		if !d.IsValidFor2024() {
			return "", errors.New("invalid difficulty for 2024 ruleset")
		}
	case Ruleset2014:
		if !d.IsValidFor2014() {
			return "", errors.New("invalid difficulty for 2014 ruleset")
		}
	default:
		return "", errors.New("invalid ruleset")
	}
	return d, nil
}

func (d Difficulty) String() string { return string(d) }

func (d Difficulty) IsValidFor2024() bool {
	return d == DifficultyLow || d == DifficultyModerate || d == DifficultyHigh
}

func (d Difficulty) IsValidFor2014() bool {
	return d == DifficultyEasy || d == DifficultyMedium || d == DifficultyHard || d == DifficultyDeadly
}

// Character represents a single party member.
type Character struct {
	Level int
}

// NewCharacter creates a new character with the given level (1-20).
func NewCharacter(level int) (Character, error) {
	if level < 1 || level > 20 {
		return Character{}, errors.New("character level must be between 1 and 20")
	}
	return Character{Level: level}, nil
}

// Party represents a group of characters.
type Party struct {
	Characters []Character
}

// NewParty creates a new party with the given character levels.
func NewParty(levels []int) (Party, error) {
	if len(levels) == 0 {
		return Party{}, errors.New("party must have at least one character")
	}
	chars := make([]Character, 0, len(levels))
	for _, level := range levels {
		c, err := NewCharacter(level)
		if err != nil {
			return Party{}, fmt.Errorf("invalid character level %d: %w", level, err)
		}
		chars = append(chars, c)
	}
	return Party{Characters: chars}, nil
}

func (p Party) Size() int { return len(p.Characters) }

func (p Party) Levels() []int {
	levels := make([]int, len(p.Characters))
	for i, c := range p.Characters {
		levels[i] = c.Level
	}
	return levels
}

func (p Party) AverageLevel() float64 {
	if len(p.Characters) == 0 {
		return 0
	}
	total := 0
	for _, c := range p.Characters {
		total += c.Level
	}
	return float64(total) / float64(len(p.Characters))
}

// Encounter represents a D&D encounter with XP calculation.
type Encounter struct {
	ID          string
	Party       Party
	Ruleset     Ruleset
	Difficulty  Difficulty
	TotalXP     int
	NumMonsters int
}

// XPCalculationResult represents the result of XP calculation.
type XPCalculationResult struct {
	Ruleset                  Ruleset
	TotalXP                  int
	CalculatedDifficulty2014 Difficulty
	PartySize                int
	CharacterLevels          []int
}

// NewEncounter creates a new encounter.
func NewEncounter(id string, party Party, ruleset Ruleset, difficulty Difficulty) *Encounter {
	return &Encounter{
		ID:         id,
		Party:      party,
		Ruleset:    ruleset,
		Difficulty: difficulty,
	}
}

// ToResult converts the encounter to an XPCalculationResult.
func (e *Encounter) ToResult() XPCalculationResult {
	return XPCalculationResult{
		Ruleset:         e.Ruleset,
		TotalXP:         e.TotalXP,
		PartySize:       e.Party.Size(),
		CharacterLevels: e.Party.Levels(),
	}
}
