package srd

import "sort"

// CollectionName identifies a collection of SRD entities.
type CollectionName string

const (
	Classi          CollectionName = "classi"
	Backgrounds     CollectionName = "backgrounds"
	Incantesimi     CollectionName = "incantesimi"
	Talenti         CollectionName = "talenti"
	Equipaggiamenti CollectionName = "equipaggiamenti"
	Servizi         CollectionName = "servizi"
	Regole          CollectionName = "regole"
	OggettiMagici   CollectionName = "oggetti_magici"
	Mostri          CollectionName = "mostri"
	Glossario       CollectionName = "glossario"
	Specie          CollectionName = "specie"
)

// CollectionInfo describes a collection's metadata.
type CollectionInfo struct {
	Name        CollectionName
	Title       string
	Description string
}

// Registry maps collection names to their metadata.
var Registry = map[CollectionName]CollectionInfo{
	Classi:          {Name: Classi, Title: "Classi", Description: "Le classi dei personaggi giocanti con caratteristiche, privilegi e sottoclassi."},
	Backgrounds:     {Name: Backgrounds, Title: "Background", Description: "I background dei personaggi con abilità, talenti e tratti caratteristici."},
	Incantesimi:     {Name: Incantesimi, Title: "Incantesimi", Description: "Tutti gli incantesimi dal trucchetto al 9° livello con descrizione e componenti."},
	Talenti:         {Name: Talenti, Title: "Talenti", Description: "I talenti disponibili per personalizzare e potenziare il tuo personaggio."},
	Equipaggiamenti: {Name: Equipaggiamenti, Title: "Equipaggiamento", Description: "Armi, armature, strumenti e altro equipaggiamento per gli avventurieri."},
	Servizi:         {Name: Servizi, Title: "Servizi", Description: "Servizi, cavalcature, veicoli e spese di sostentamento."},
	Regole:          {Name: Regole, Title: "Regole", Description: "Le regole base del gioco: combattimento, esplorazione e interazione."},
	OggettiMagici:   {Name: OggettiMagici, Title: "Oggetti Magici", Description: "Oggetti magici di ogni rarità: armi, armature, pozioni e oggetti meravigliosi."},
	Mostri:          {Name: Mostri, Title: "Mostri", Description: "Il bestiario completo con statistiche, abilità e gradi sfida."},
	Glossario:       {Name: Glossario, Title: "Glossario", Description: "Definizioni dei termini chiave e delle regole di gioco."},
	Specie:          {Name: Specie, Title: "Specie", Description: "Le specie giocabili con tratti, abilità speciali e caratteristiche."},
}

func (c CollectionName) String() string { return string(c) }

// GetInfo returns collection metadata by name.
func GetInfo(name string) (CollectionInfo, bool) {
	info, exists := Registry[CollectionName(name)]
	return info, exists
}

// IsValidCollection returns true if the name is a known collection.
func IsValidCollection(name string) bool {
	_, exists := Registry[CollectionName(name)]
	return exists
}

// AllCollections returns all collection names in alphabetical order.
func AllCollections() []string {
	names := make([]string, 0, len(Registry))
	for name := range Registry {
		names = append(names, name.String())
	}
	sort.Strings(names)
	return names
}
