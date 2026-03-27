// fix-orphan-markdown strips orphan bold/italic markers (_**, **_, **)
// that appear at the start or end of JSON string values as artifacts
// of PDF parsing. It does NOT touch valid inline formatting like _**Header.**_
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// Trailing orphan: _** or ** at end of string, optionally preceded by whitespace
var trailingOrphan = regexp.MustCompile(`\s*_?\*\*_?\s*$`)

// Leading orphan: **_ or ** at start of string, optionally followed by whitespace
var leadingOrphan = regexp.MustCompile(`^\s*_?\*\*_?\s*`)

// Inline bold-italic like _**Header.**_ — indicates the text has real formatting
var inlineBoldItalic = regexp.MustCompile(`_\*\*[^*]+\*\*_`)

var totalFixes int

func fixOrphanMarkdown(v any) any {
	switch val := v.(type) {
	case string:
		return fixString(val)
	case []any:
		for i, elem := range val {
			val[i] = fixOrphanMarkdown(elem)
		}
		return val
	case map[string]any:
		for k, elem := range val {
			val[k] = fixOrphanMarkdown(elem)
		}
		return val
	default:
		return v
	}
}

func fixString(s string) string {
	original := s

	// Strip trailing orphan markers like " _**" or " **"
	// But only if it's truly orphan (not part of inline formatting)
	if trailingOrphan.MatchString(s) {
		candidate := trailingOrphan.ReplaceAllString(s, "")
		// Only apply if we didn't destroy valid inline formatting
		// A trailing _** is orphan if there's no matching closing **_ after it
		// Since it's at the end, there can't be a closing marker → it's orphan
		if candidate != "" {
			s = candidate
		}
	}

	// Strip leading orphan markers like "**_ " or "** "
	if leadingOrphan.MatchString(s) {
		// Check that this isn't part of inline formatting like **_word_**
		prefix := leadingOrphan.FindString(s)
		rest := s[len(prefix):]
		// If the rest doesn't start with a bold-italic block, it's orphan
		if !strings.HasPrefix(rest, "*") && !inlineBoldItalic.MatchString(prefix+rest[:min(len(rest), 30)]) {
			s = rest
		}
	}

	if s != original {
		totalFixes++
	}
	return s
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
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

	before := totalFixes
	fixed := fixOrphanMarkdown(parsed)
	fixes := totalFixes - before

	out, err := json.MarshalIndent(fixed, "", "  ")
	if err != nil {
		return 0, fmt.Errorf("marshal %s: %w", path, err)
	}
	out = append(out, '\n')

	if string(out) == string(data) {
		return 0, nil
	}

	if err := os.WriteFile(path, out, 0644); err != nil {
		return 0, err
	}

	return fixes, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "usage: %s <dir>...\n", os.Args[0])
		os.Exit(1)
	}

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
				totalFiles++
			}
			return nil
		})
		if err != nil {
			fmt.Fprintf(os.Stderr, "walk error: %s\n", err)
			os.Exit(1)
		}
	}

	fmt.Printf("\nfixed %d orphan markdown occurrences in %d files\n", totalFixes, totalFiles)
}
