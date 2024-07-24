###Generating OBO Semantic Engineer course content and deploying website
#
# These are standard options to make Make sane:
# <http://clarkgrubb.com/makefile-style-guide#toc2>

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:


#################################
#### MATRIX Disease List ########
#################################

all: matrix-disease-list.tsv

mondo.owl:
	wget "http://purl.obolibrary.org/obo/mondo.owl" -O $@
.PRECIOUS: mondo.owl

mondo-metadata.tsv: mondo.owl sparql/ontology-metadata.sparql
	robot query -i $< -f tsv --query sparql/ontology-metadata.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<//g' $@
	sed -i 's/>//g' $@
.PRECIOUS: mondo-metadata.tsv

matrix-disease-list-unfiltered.tsv: mondo.owl sparql/matrix-disease-list-filters.sparql
	robot query -i $< -f tsv --query sparql/matrix-disease-list-filters.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]MONDO_/MONDO:/g' $@
	sed -i 's/http:[/][/]purl[.]obolibrary[.]org[/]obo[/]mondo#/mondo:/g' $@
	sed -i 's/>//g' $@
.PRECIOUS: matrix-disease-list-unfiltered.tsv

matrix-disease-list.tsv: matrix-disease-list-unfiltered.tsv scripts/matrix-disease-list.py
	pip install -r requirements.txt
	python scripts/matrix-disease-list.py create-matrix-disease-list -i $< \
		-o matrix-disease-list.tsv \
		-e matrix-excluded-diseases-list.tsv \
		-x matrix-disease-list.xlsx

#################################
#### Release system #############
#################################

ASSETS=matrix-disease-list.tsv \
	matrix-disease-list-unfiltered.tsv \
	matrix-disease-list.xlsx \
	matrix-excluded-diseases-list.tsv \
	mondo-metadata.tsv

gh_release:
	@test $(VERSION)
	ls -alt $(ASSETS)
	gh release create $(VERSION) --notes "TBD." --title "$(VERSION)" --draft $(ASSETS)

#################################
#### Documentation ##############
#################################

.PHONY: deploy_site
deploy_site:
	mkdocs gh-deploy --config-file mkdocs.yml

build_site:
	mkdocs build --config-file mkdocs.yml

