package srd

import (
	"encoding/json"
	"testing"
)

func TestContentPlainText(t *testing.T) {
	tests := []struct {
		name    string
		content Content
		want    string
	}{
		{
			name:    "empty content",
			content: Content{},
			want:    "",
		},
		{
			name: "text only",
			content: Content{
				{Type: "text", Text: "Il deva può lanciare i seguenti incantesimi"},
			},
			want: "Il deva può lanciare i seguenti incantesimi",
		},
		{
			name: "mixed segments",
			content: Content{
				{Type: "text", Text: "Resistenze ai danni: "},
				{Type: "damage_type", Text: "fuoco", ID: "fuoco"},
				{Type: "text", Text: ", "},
				{Type: "damage_type", Text: "fulmine", ID: "fulmine"},
			},
			want: "Resistenze ai danni: fuoco, fulmine",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.content.PlainText()
			if got != tt.want {
				t.Errorf("PlainText() = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestContentRefs(t *testing.T) {
	content := Content{
		{Type: "text", Text: "Lancia "},
		{Type: "spell", Text: "comunione", ID: "comunione"},
		{Type: "text", Text: " e "},
		{Type: "spell", Text: "resurrezione", ID: "resurrezione"},
		{Type: "text", Text: ". Immune a "},
		{Type: "condition", Text: "avvelenato", ID: "avvelenato"},
	}

	refs := content.Refs()
	if len(refs) != 3 {
		t.Fatalf("Refs() returned %d segments, want 3", len(refs))
	}

	// Verify only non-text segments are returned
	for _, ref := range refs {
		if ref.Type == "text" {
			t.Errorf("Refs() should not include text segments, got %+v", ref)
		}
	}

	// Verify order preserved
	if refs[0].ID != "comunione" {
		t.Errorf("refs[0].ID = %q, want %q", refs[0].ID, "comunione")
	}
	if refs[1].ID != "resurrezione" {
		t.Errorf("refs[1].ID = %q, want %q", refs[1].ID, "resurrezione")
	}
	if refs[2].ID != "avvelenato" {
		t.Errorf("refs[2].ID = %q, want %q", refs[2].ID, "avvelenato")
	}
}

func TestContentRefsEmpty(t *testing.T) {
	content := Content{
		{Type: "text", Text: "solo testo"},
	}

	refs := content.Refs()
	if len(refs) != 0 {
		t.Errorf("Refs() returned %d segments, want 0", len(refs))
	}
}

func TestContentJSONMarshal(t *testing.T) {
	content := Content{
		{Type: "text", Text: "Lancia "},
		{Type: "spell", Text: "comunione", ID: "comunione"},
	}

	data, err := json.Marshal(content)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	var got Content
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatalf("Unmarshal error: %v", err)
	}

	if len(got) != 2 {
		t.Fatalf("roundtrip got %d segments, want 2", len(got))
	}
	if got[0].Type != "text" || got[0].Text != "Lancia " {
		t.Errorf("segment[0] = %+v, want text segment", got[0])
	}
	if got[1].Type != "spell" || got[1].ID != "comunione" {
		t.Errorf("segment[1] = %+v, want spell ref", got[1])
	}
}

func TestContentJSONOmitsIDForText(t *testing.T) {
	content := Content{
		{Type: "text", Text: "solo testo"},
	}

	data, err := json.Marshal(content)
	if err != nil {
		t.Fatalf("Marshal error: %v", err)
	}

	// ID should be omitted for text segments
	var raw []map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		t.Fatalf("Unmarshal raw error: %v", err)
	}

	if _, hasID := raw[0]["id"]; hasID {
		t.Error("text segment should not have 'id' field in JSON")
	}
}

func TestSegmentTextConstructor(t *testing.T) {
	s := TextSegment("hello world")
	if s.Type != "text" {
		t.Errorf("Type = %q, want %q", s.Type, "text")
	}
	if s.Text != "hello world" {
		t.Errorf("Text = %q, want %q", s.Text, "hello world")
	}
	if s.ID != "" {
		t.Errorf("ID = %q, want empty", s.ID)
	}
}

func TestSegmentRefConstructor(t *testing.T) {
	s := RefSegment("spell", "comunione", "comunione")
	if s.Type != "spell" {
		t.Errorf("Type = %q, want %q", s.Type, "spell")
	}
	if s.Text != "comunione" {
		t.Errorf("Text = %q, want %q", s.Text, "comunione")
	}
	if s.ID != "comunione" {
		t.Errorf("ID = %q, want %q", s.ID, "comunione")
	}
}

func TestContentUnmarshalFromString(t *testing.T) {
	raw := `"Il deva lancia comunione"`
	var c Content
	if err := json.Unmarshal([]byte(raw), &c); err != nil {
		t.Fatalf("Unmarshal string error: %v", err)
	}
	if len(c) != 1 {
		t.Fatalf("got %d segments, want 1", len(c))
	}
	if c[0].Type != "text" {
		t.Errorf("Type = %q, want %q", c[0].Type, "text")
	}
	if c[0].Text != "Il deva lancia comunione" {
		t.Errorf("Text = %q, want %q", c[0].Text, "Il deva lancia comunione")
	}
}

func TestFeatureWithContent(t *testing.T) {
	raw := `{
		"name": "Incantesimi innati",
		"description": [
			{"type": "text", "text": "Il deva lancia "},
			{"type": "spell", "id": "comunione", "text": "comunione"}
		]
	}`

	var f Feature
	if err := json.Unmarshal([]byte(raw), &f); err != nil {
		t.Fatalf("Unmarshal Feature error: %v", err)
	}

	if f.Name != "Incantesimi innati" {
		t.Errorf("Name = %q, want %q", f.Name, "Incantesimi innati")
	}
	if len(f.Description) != 2 {
		t.Fatalf("Description has %d segments, want 2", len(f.Description))
	}
	if f.Description.PlainText() != "Il deva lancia comunione" {
		t.Errorf("PlainText() = %q, want %q", f.Description.PlainText(), "Il deva lancia comunione")
	}
}
