PREFIX mondo: <http://purl.obolibrary.org/obo/mondo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX oio: <http://www.geneontology.org/formats/oboInOwl#>

DELETE {
  ?subject rdfs:label ?label .
}
INSERT {
  ?subject rdfs:label ?newLabel .
}
WHERE {
    VALUES ?subset { <http://purl.obolibrary.org/obo/mondo#matrix_included> }
    ?subject oio:inSubset ?subset .
    ?subject rdfs:label ?label .
    BIND(CONCAT(?label, CONCAT(", ", REPLACE(STR(?subset),"http://purl.obolibrary.org/obo/mondo#",""))) AS ?newLabel)
}