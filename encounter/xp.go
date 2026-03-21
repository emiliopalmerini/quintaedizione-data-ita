package encounter

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"strconv"
)

// MultiplierRange defines an encounter multiplier for a max monster count.
type MultiplierRange struct {
	MaxMonsters int     `json:"max_monsters"`
	Multiplier  float64 `json:"multiplier"`
}

// XPTables holds all XP data loaded from JSON.
type XPTables struct {
	XP2024      map[int]map[string]int
	Thresholds  map[int]map[string]int
	Multipliers []MultiplierRange
}

// LoadXPTables loads XP tables from a filesystem containing xp_2024.json and xp_2014.json.
func LoadXPTables(fsys fs.FS) (*XPTables, error) {
	tables := &XPTables{}

	// Load 2024 XP data
	data2024, err := fs.ReadFile(fsys, "xp_2024.json")
	if err != nil {
		return nil, fmt.Errorf("read xp_2024.json: %w", err)
	}
	var raw2024 map[string]map[string]int
	if err := json.Unmarshal(data2024, &raw2024); err != nil {
		return nil, fmt.Errorf("parse xp_2024.json: %w", err)
	}
	tables.XP2024 = make(map[int]map[string]int, len(raw2024))
	for k, v := range raw2024 {
		level, err := strconv.Atoi(k)
		if err != nil {
			return nil, fmt.Errorf("invalid level key %q: %w", k, err)
		}
		tables.XP2024[level] = v
	}

	// Load 2014 XP data
	data2014, err := fs.ReadFile(fsys, "xp_2014.json")
	if err != nil {
		return nil, fmt.Errorf("read xp_2014.json: %w", err)
	}
	var raw2014 struct {
		Thresholds  map[string]map[string]int `json:"thresholds"`
		Multipliers []MultiplierRange         `json:"multipliers"`
	}
	if err := json.Unmarshal(data2014, &raw2014); err != nil {
		return nil, fmt.Errorf("parse xp_2014.json: %w", err)
	}
	tables.Thresholds = make(map[int]map[string]int, len(raw2014.Thresholds))
	for k, v := range raw2014.Thresholds {
		level, err := strconv.Atoi(k)
		if err != nil {
			return nil, fmt.Errorf("invalid level key %q: %w", k, err)
		}
		tables.Thresholds[level] = v
	}
	tables.Multipliers = raw2014.Multipliers

	return tables, nil
}

// GetXPFor2024 returns the XP for a level and difficulty in the 2024 ruleset.
func (t *XPTables) GetXPFor2024(level int, difficulty Difficulty) (int, error) {
	levelData, ok := t.XP2024[level]
	if !ok {
		return 0, fmt.Errorf("unsupported level: %d", level)
	}
	xp, ok := levelData[difficulty.String()]
	if !ok {
		return 0, fmt.Errorf("unsupported difficulty: %s", difficulty)
	}
	return xp, nil
}

// GetThresholdFor2014 returns the XP threshold for a level and difficulty in the 2014 ruleset.
func (t *XPTables) GetThresholdFor2014(level int, difficulty Difficulty) (int, error) {
	levelData, ok := t.Thresholds[level]
	if !ok {
		return 0, fmt.Errorf("unsupported level: %d", level)
	}
	threshold, ok := levelData[difficulty.String()]
	if !ok {
		return 0, fmt.Errorf("unsupported difficulty: %s", difficulty)
	}
	return threshold, nil
}

// GetMultiplierFor2014 returns the encounter multiplier for the given number of monsters.
func (t *XPTables) GetMultiplierFor2014(numMonsters int) (float64, error) {
	if numMonsters < 1 {
		return 0, fmt.Errorf("number of monsters must be at least 1")
	}
	for _, r := range t.Multipliers {
		if numMonsters <= r.MaxMonsters {
			return r.Multiplier, nil
		}
	}
	if len(t.Multipliers) > 0 {
		return t.Multipliers[len(t.Multipliers)-1].Multiplier, nil
	}
	return 1.0, nil
}
