PREFIX mondo: <http://purl.obolibrary.org/obo/mondo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX oio: <http://www.geneontology.org/formats/oboInOwl#>

INSERT {
  ?subject oio:inSubset ?otherSubset .
}
WHERE {
  VALUES ?subset { 
    <http://purl.obolibrary.org/obo/mondo#matrix_txgnn_grouping>
    <http://purl.obolibrary.org/obo/mondo#harrisons_view>
    <http://purl.obolibrary.org/obo/mondo#mondo_top_grouping>
  }
  ?subject rdfs:subClassOf+ <http://purl.obolibrary.org/obo/MONDO_0700096> .
  
  # Bind ?memberSubset before checking filters
  BIND(IRI(CONCAT(STR(?subset), "_member")) AS ?memberSubset)
  BIND(IRI(CONCAT(STR(?subset), "_other")) AS ?otherSubset)

  # Ensure ?subject is not already inSubset for ?subset or ?memberSubset
  FILTER NOT EXISTS {
    ?subject oio:inSubset ?subset .
  }
  FILTER NOT EXISTS {
    ?subject oio:inSubset ?memberSubset .
  }
}
