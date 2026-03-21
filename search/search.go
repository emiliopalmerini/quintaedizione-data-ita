package search

import (
	"sort"
	"strings"

	"github.com/lithammer/fuzzysearch/fuzzy"
)

// SearchableItem represents an item that can be searched.
type SearchableItem struct {
	ID         string
	Collection string
	Title      string
	Keywords   []string
}

// SearchResult represents a single search match.
type SearchResult struct {
	ID         string
	Collection string
	Title      string
	Score      int
}

// SearchResultSet groups results by collection.
type SearchResultSet struct {
	Collection string
	Results    []SearchResult
	Total      int64
}

// Service provides fuzzy search across searchable items.
type Service struct {
	items map[string][]SearchableItem
}

// NewService creates a search service with the given items grouped by collection.
func NewService(items map[string][]SearchableItem) *Service {
	return &Service{items: items}
}

// Search performs a fuzzy search across all collections.
func (s *Service) Search(query string, limitPerCollection int) []SearchResultSet {
	if query == "" {
		return nil
	}

	query = strings.ToLower(strings.TrimSpace(query))

	var results []SearchResultSet
	for collection, items := range s.items {
		collResults, total := searchInCollection(items, query, limitPerCollection)
		if total == 0 {
			continue
		}
		results = append(results, SearchResultSet{
			Collection: collection,
			Results:    collResults,
			Total:      int64(total),
		})
	}

	sort.Slice(results, func(i, j int) bool {
		if len(results[i].Results) == 0 || len(results[j].Results) == 0 {
			return len(results[i].Results) > len(results[j].Results)
		}
		return results[i].Results[0].Score > results[j].Results[0].Score
	})

	return results
}

// SearchCollection performs a fuzzy search within a single collection.
func (s *Service) SearchCollection(collection, query string, limit int) []SearchResult {
	if query == "" {
		return nil
	}

	items, ok := s.items[collection]
	if !ok {
		return nil
	}

	query = strings.ToLower(strings.TrimSpace(query))
	results, _ := searchInCollection(items, query, limit)
	return results
}

func searchInCollection(items []SearchableItem, query string, limit int) ([]SearchResult, int) {
	type rankedItem struct {
		item  SearchableItem
		score int
	}

	var ranked []rankedItem

	for _, item := range items {
		title := strings.ToLower(item.Title)
		keywords := strings.ToLower(strings.Join(item.Keywords, " "))

		if strings.Contains(title, query) {
			ranked = append(ranked, rankedItem{item: item, score: 1000 + len(query)*10})
			continue
		}

		if keywords != "" && strings.Contains(keywords, query) {
			ranked = append(ranked, rankedItem{item: item, score: 500 + len(query)*5})
			continue
		}

		if len(query) >= 3 {
			matches := fuzzy.RankFind(query, []string{title})
			if len(matches) > 0 && matches[0].Distance <= len(query)/2 {
				ranked = append(ranked, rankedItem{item: item, score: 100 - matches[0].Distance})
				continue
			}

			if keywords != "" {
				keywordMatches := fuzzy.RankFind(query, []string{keywords})
				if len(keywordMatches) > 0 && keywordMatches[0].Distance <= len(query)/2 {
					ranked = append(ranked, rankedItem{item: item, score: 50 - keywordMatches[0].Distance})
				}
			}
		}
	}

	totalMatches := len(ranked)

	sort.Slice(ranked, func(i, j int) bool {
		return ranked[i].score > ranked[j].score
	})

	if limit > 0 && len(ranked) > limit {
		ranked = ranked[:limit]
	}

	results := make([]SearchResult, 0, len(ranked))
	for _, r := range ranked {
		results = append(results, SearchResult{
			ID:         r.item.ID,
			Collection: r.item.Collection,
			Title:      r.item.Title,
			Score:      r.score,
		})
	}

	return results, totalMatches
}
