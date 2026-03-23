package srd

import (
	"encoding/json"
	"strings"
)

// Segment represents a piece of content: either plain text or a typed entity reference.
type Segment struct {
	Type string `json:"type"`
	Text string `json:"text"`
	ID   string `json:"id,omitempty"`
}

// Content is a sequence of segments representing rich text with entity references.
type Content []Segment

// PlainText concatenates all segment text into a single string.
func (c Content) PlainText() string {
	var b strings.Builder
	for _, s := range c {
		b.WriteString(s.Text)
	}
	return b.String()
}

// Refs returns only the non-text segments (entity references).
func (c Content) Refs() []Segment {
	var refs []Segment
	for _, s := range c {
		if s.Type != "text" {
			refs = append(refs, s)
		}
	}
	return refs
}

// UnmarshalJSON accepts both a JSON string (legacy) and a JSON array of segments.
func (c *Content) UnmarshalJSON(data []byte) error {
	// Try array of segments first
	var segments []Segment
	if err := json.Unmarshal(data, &segments); err == nil {
		*c = segments
		return nil
	}

	// Fall back to plain string
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return err
	}
	*c = Content{{Type: "text", Text: s}}
	return nil
}

// TextSegment creates a plain text segment.
func TextSegment(text string) Segment {
	return Segment{Type: "text", Text: text}
}

// RefSegment creates a typed entity reference segment.
func RefSegment(refType, id, text string) Segment {
	return Segment{Type: refType, Text: text, ID: id}
}
