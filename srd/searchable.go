package srd

// Searchable is implemented by all SRD entities to support indexing and search.
type Searchable interface {
	SearchID() string
	SearchTitle() string
	SearchKeywords() []string
}
