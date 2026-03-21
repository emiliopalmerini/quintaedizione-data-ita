package filters

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/emiliopalmerini/quintaedizione-data-ita/srd"
)

// Filterable is implemented by entities that support field-based filtering.
type Filterable interface {
	FilterValue(field string) any
}

// DataType identifies the type of a filter field.
type DataType int

const (
	StringType DataType = iota
	NumberType
	BooleanType
	EnumType
)

// Operator defines how a filter value is matched.
type Operator int

const (
	ExactMatch Operator = iota
	RegexMatch
	RangeMatch
	InMatch
)

// Definition describes a single filter field.
type Definition struct {
	Name        string
	FieldPath   string
	DataType    DataType
	Operator    Operator
	Collections []srd.CollectionName
	EnumValues  []string
	Description string
}

// Value pairs a filter definition with a user-supplied value.
type Value struct {
	Definition Definition
	Val        string
}

// Set groups filter values for a collection.
type Set struct {
	Collection srd.CollectionName
	Filters    []Value
}

func NewSet(collection srd.CollectionName) *Set {
	return &Set{Collection: collection, Filters: make([]Value, 0)}
}

func (s *Set) Add(v Value)       { s.Filters = append(s.Filters, v) }
func (s *Set) HasFilters() bool  { return len(s.Filters) > 0 }

// Predicate tests whether a Filterable entity matches.
type Predicate func(Filterable) bool

// BuildPredicate converts a Set into a Predicate (all filters AND-ed).
func BuildPredicate(set *Set) (Predicate, error) {
	if !set.HasFilters() {
		return nil, nil
	}

	var predicates []Predicate
	for _, fv := range set.Filters {
		p, err := buildSingle(fv)
		if err != nil {
			return nil, fmt.Errorf("filter %s: %w", fv.Definition.Name, err)
		}
		if p != nil {
			predicates = append(predicates, p)
		}
	}

	if len(predicates) == 0 {
		return nil, nil
	}
	if len(predicates) == 1 {
		return predicates[0], nil
	}

	return func(f Filterable) bool {
		for _, p := range predicates {
			if !p(f) {
				return false
			}
		}
		return true
	}, nil
}

// CombinePredicates combines multiple predicates with AND logic.
func CombinePredicates(predicates ...Predicate) Predicate {
	var nonNil []Predicate
	for _, p := range predicates {
		if p != nil {
			nonNil = append(nonNil, p)
		}
	}
	if len(nonNil) == 0 {
		return nil
	}
	if len(nonNil) == 1 {
		return nonNil[0]
	}
	return func(f Filterable) bool {
		for _, p := range nonNil {
			if !p(f) {
				return false
			}
		}
		return true
	}
}

func buildSingle(fv Value) (Predicate, error) {
	if fv.Val == "" {
		return nil, nil
	}

	switch fv.Definition.Operator {
	case ExactMatch:
		return buildExact(fv.Definition.FieldPath, fv.Val, fv.Definition.DataType)
	case RegexMatch:
		return buildRegex(fv.Definition.FieldPath, fv.Val)
	case RangeMatch:
		return buildRange(fv.Definition.FieldPath, fv.Val)
	case InMatch:
		return buildIn(fv.Definition.FieldPath, fv.Val)
	default:
		return nil, fmt.Errorf("unsupported operator: %d", fv.Definition.Operator)
	}
}

func buildExact(field, value string, dt DataType) (Predicate, error) {
	converted, err := convertValue(value, dt)
	if err != nil {
		return nil, err
	}
	target := fmt.Sprintf("%v", converted)
	return func(f Filterable) bool {
		return fmt.Sprintf("%v", f.FilterValue(field)) == target
	}, nil
}

func buildRegex(field, value string) (Predicate, error) {
	parts := strings.Split(value, ",")
	var patterns []*regexp.Regexp
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		compiled, err := regexp.Compile("(?i)" + regexp.QuoteMeta(p))
		if err != nil {
			return nil, fmt.Errorf("invalid pattern: %w", err)
		}
		patterns = append(patterns, compiled)
	}
	if len(patterns) == 0 {
		return nil, nil
	}
	return func(f Filterable) bool {
		v := f.FilterValue(field)
		if v == nil {
			return false
		}
		s := fmt.Sprintf("%v", v)
		for _, p := range patterns {
			if p.MatchString(s) {
				return true
			}
		}
		return false
	}, nil
}

func buildRange(field, value string) (Predicate, error) {
	value = strings.TrimSpace(value)
	type numPred func(float64) bool
	var pred numPred

	if strings.HasPrefix(value, ">=") {
		n, err := strconv.ParseFloat(strings.TrimSpace(value[2:]), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid range: %s", value)
		}
		pred = func(v float64) bool { return v >= n }
	} else if strings.HasPrefix(value, "<=") {
		n, err := strconv.ParseFloat(strings.TrimSpace(value[2:]), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid range: %s", value)
		}
		pred = func(v float64) bool { return v <= n }
	} else if strings.HasPrefix(value, ">") {
		n, err := strconv.ParseFloat(strings.TrimSpace(value[1:]), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid range: %s", value)
		}
		pred = func(v float64) bool { return v > n }
	} else if strings.HasPrefix(value, "<") {
		n, err := strconv.ParseFloat(strings.TrimSpace(value[1:]), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid range: %s", value)
		}
		pred = func(v float64) bool { return v < n }
	} else if strings.Contains(value, "-") {
		parts := strings.SplitN(value, "-", 2)
		min, err := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid range min: %s", parts[0])
		}
		max, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid range max: %s", parts[1])
		}
		pred = func(v float64) bool { return v >= min && v <= max }
	} else {
		n, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return nil, fmt.Errorf("invalid number: %s", value)
		}
		pred = func(v float64) bool { return v == n }
	}

	return func(f Filterable) bool {
		v := f.FilterValue(field)
		if v == nil {
			return false
		}
		n, ok := toFloat64(v)
		if !ok {
			return false
		}
		return pred(n)
	}, nil
}

func buildIn(field, value string) (Predicate, error) {
	values := strings.Split(value, ",")
	trimmed := make([]string, 0, len(values))
	for _, v := range values {
		if t := strings.TrimSpace(v); t != "" {
			trimmed = append(trimmed, t)
		}
	}
	if len(trimmed) == 0 {
		return nil, nil
	}
	return func(f Filterable) bool {
		v := f.FilterValue(field)
		if v == nil {
			return false
		}
		s := fmt.Sprintf("%v", v)
		for _, t := range trimmed {
			if s == t {
				return true
			}
		}
		return false
	}, nil
}

func convertValue(value string, dt DataType) (any, error) {
	switch dt {
	case NumberType:
		return strconv.ParseFloat(value, 64)
	case BooleanType:
		return strconv.ParseBool(value)
	default:
		return value, nil
	}
}

func toFloat64(v any) (float64, bool) {
	switch n := v.(type) {
	case float64:
		return n, true
	case float32:
		return float64(n), true
	case int:
		return float64(n), true
	case int64:
		return float64(n), true
	case string:
		f, err := strconv.ParseFloat(n, 64)
		return f, err == nil
	default:
		return 0, false
	}
}
