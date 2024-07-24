

all: matrix-disease-list.tsv

mondo.owl:
	wget "http://purl.obolibrary.org/obo/mondo.owl" -O $@
.PRECIOUS: mondo.owl

matrix-disease-list-unfiltered.tsv: mondo.owl sparql/matrix-disease-list-filters.sparql
	robot query -i $< -f tsv --query sparql/matrix-disease-list-filters.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]MONDO_/MONDO:/g' $@
	sed -i 's/http:[/][/]purl[.]obolibrary[.]org[/]obo[/]mondo#/mondo:/g' $@
	sed -i 's/>//g' $@
.PRECIOUS: matrix-disease-list-unfiltered.tsv

matrix-disease-list.tsv: matrix-disease-list-unfiltered.tsv scripts/matrix-disease-list.py
	python scripts/matrix-disease-list.py create-matrix-disease-list -i $< -o $@ -f f_leaf -v TRUE

