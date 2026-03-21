package maps

// Mappa represents a map with Italian-translated metadata.
type Mappa struct {
	Slug                 string   `json:"slug"`
	Nome                 string   `json:"nome"`
	NomeOriginale        string   `json:"nome_originale"`
	Immagine             string   `json:"immagine"`
	Tag                  []string `json:"tag"`
	Descrizione          string   `json:"descrizione"`
	Autore               string   `json:"autore"`
	Licenza              string   `json:"licenza"`
	URLOriginale         string   `json:"url_originale"`
	URLImmagineOriginale string   `json:"url_immagine_originale"`
}

// SearchFilters holds filter criteria for map search.
type SearchFilters struct {
	Query  string
	Tags   []string
	Offset int
	Limit  int
}
