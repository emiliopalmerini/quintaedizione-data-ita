// fix-double-spaces collapses runs of multiple spaces into a single space
// inside all JSON string values. It preserves JSON structure and formatting.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
)

var multiSpace = regexp.MustCompile(`  +`)

func fixStrings(v any) any {
	switch val := v.(type) {
	case string:
		return multiSpace.ReplaceAllString(val, " ")
	case []any:
		for i, elem := range val {
			val[i] = fixStrings(elem)
		}
		return val
	case map[string]any:
		for k, elem := range val {
			val[k] = fixStrings(elem)
		}
		return val
	default:
		return v
	}
}

func processFile(path string) (int, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}

	var parsed any
	if err := json.Unmarshal(data, &parsed); err != nil {
		return 0, fmt.Errorf("parse %s: %w", path, err)
	}

	fixed := fixStrings(parsed)

	out, err := json.MarshalIndent(fixed, "", "  ")
	if err != nil {
		return 0, fmt.Errorf("marshal %s: %w", path, err)
	}
	out = append(out, '\n')

	// Only write if changed
	if string(out) == string(data) {
		return 0, nil
	}

	// Count fixes (difference in multi-space matches)
	oldCount := len(multiSpace.FindAllString(string(data), -1))

	if err := os.WriteFile(path, out, 0644); err != nil {
		return 0, err
	}

	return oldCount, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "usage: %s <dir>...\n", os.Args[0])
		os.Exit(1)
	}

	totalFixes := 0
	totalFiles := 0

	for _, dir := range os.Args[1:] {
		err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if info.IsDir() || filepath.Ext(path) != ".json" {
				return nil
			}

			fixes, err := processFile(path)
			if err != nil {
				fmt.Fprintf(os.Stderr, "error: %s\n", err)
				return nil
			}
			if fixes > 0 {
				fmt.Printf("  %s: %d fixes\n", path, fixes)
				totalFixes += fixes
				totalFiles++
			}
			return nil
		})
		if err != nil {
			fmt.Fprintf(os.Stderr, "walk error: %s\n", err)
			os.Exit(1)
		}
	}

	fmt.Printf("\nfixed %d double-space occurrences in %d files\n", totalFixes, totalFiles)
}
