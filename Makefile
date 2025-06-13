###Makefile for the MATRIX Disease List
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

ONTBASE=                    http://purl.obolibrary.org/obo/mondo
TODAY ?=                    $(shell date +%Y-%m-%d)
VERSION=                    $(TODAY)

ROBOT=robot

ANNOTATE_ONTOLOGY_VERSION = annotate -V $(ONTBASE)/releases/$(VERSION)/$@ --annotation owl:versionInfo $(VERSION)
ANNOTATE_CONVERT_FILE = annotate --ontology-iri $(ONTBASE)/$@ $(ANNOTATE_ONTOLOGY_VERSION) convert -f ofn --output $@.tmp.owl && mv $@.tmp.owl $@

#################################
#### MATRIX Disease List ########
#################################

ASSETS=matrix-disease-list.tsv \
	matrix-disease-list-unfiltered.tsv \
	matrix-disease-list-unfiltered-processed.tsv \
	matrix-disease-list.xlsx \
	matrix-excluded-diseases-list.tsv \
	matrix-disease-groupings.tsv \
	mondo-metadata.tsv \
	mondo-with-filter-designations.owl

all: $(ASSETS)

MONDO_OWL_URL=http://purl.obolibrary.org/obo/mondo.owl
#MONDO_OWL_URL=https://github.com/monarch-initiative/mondo/releases/download/v2024-11-05/mondo.owl

# The current release of the Mondo disease ontology
tmp/mondo.owl:
	wget "$(MONDO_OWL_URL)" -O $@
.PRECIOUS: tmp/mondo.owl

%.db: %.owl
	@rm -f $*.db
	@rm -f .template.db
	@rm -f .template.db.tmp
	@rm -f $*-relation-graph.tsv.gz
	RUST_BACKTRACE=full semsql make $*.db
	@rm -f .template.db
	@rm -f .template.db.tmp
	@rm -f $*-relation-graph.tsv.gz
	@test -f $*.db || (echo "Error: File not found!" && exit 1)

.PRECIOUS: %.db

# A list of all billable ICD10 CM codes
tmp/icd10-cm-codes.xlsx:
	wget https://www.cms.gov/files/document/valid-icd-10-list.xlsx -O $@

tmp/mondo.sssom.tsv:
	wget http://purl.obolibrary.org/obo/mondo/mappings/mondo.sssom.tsv -O $@

tmp/icd10-cm-billable.template.tsv: tmp/icd10-cm-codes.xlsx tmp/mondo.sssom.tsv
	python scripts/matrix-disease-list.py create-billable-icd10-template -i $< \
		-i $< \
		-m tmp/mondo.sssom.tsv \
		-o $@

tmp/llm-based-disease-groupings.template.tsv: llm-disease-categorization/data/03_primary/disease_categories.tsv
	python scripts/matrix-disease-list.py format-llm-disease-categorization -i llm-disease-categorization/data/03_primary/disease_categories.tsv -o $@ -c "https://orcid.org/0000-0002-4299-3501"

tmp/mondo-labels.tsv: tmp/mondo.owl
	$(ROBOT) export -i tmp/mondo.owl -f tsv --header "ID|LABEL" --export $@

tmp/subtypes.robot.tsv: tmp/mondo-labels.tsv tmp/mondo.db
	python scripts/matrix-disease-list.py create-template-with-high-granularity-subtypes \
		-l tmp/mondo-labels.tsv \
		-a sqlite:tmp/mondo.db \
		-t 0 \
		-r $@ \
		-g tmp/grouping-counts.tsv \
		-s tmp/subtype-counts.tsv \
		-o tmp/all-subtype-matches.tsv

# The MONDO ontology with the manually curated subsets added
tmp/mondo-with-manually-curated-subsets.owl: tmp/mondo.owl \
	src/included-diseases.robot.tsv \
	src/excluded-diseases.robot.tsv \
	tmp/icd10-cm-billable.template.tsv \
	tmp/subtypes.robot.tsv \
	tmp/llm-based-disease-groupings.template.tsv
	$(ROBOT) template -i tmp/mondo.owl --merge-after \
			--template src/excluded-diseases.robot.tsv \
			--template src/included-diseases.robot.tsv \
			--template src/grouping-diseases.robot.tsv \
			--template tmp/icd10-cm-billable.template.tsv \
			--template tmp/llm-based-disease-groupings.template.tsv \
			--template tmp/subtypes.robot.tsv \
		query --update sparql/inject-mondo-top-grouping.ru \
		query --update sparql/inject-susceptibility-subset.ru \
		query --update sparql/inject-subset-declaration.ru \
		query --update sparql/downfill-disease-groupings.ru \
		query --update sparql/disease-groupings-other.ru \
		query --update sparql/inject-subset-declaration.ru \
	 $(ANNOTATE_CONVERT_FILE)
.PRECIOUS: mondo-with-filter-designations.owl

# A metadata file for the MONDO ontology to know which version was used for creating the disease list
mondo-metadata.tsv: tmp/mondo.owl sparql/ontology-metadata.sparql
	$(ROBOT) query -i $< -f tsv --query sparql/ontology-metadata.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<//g' $@
	sed -i 's/>//g' $@
.PRECIOUS: mondo-metadata.tsv

# The unfiltered MATRIX disease list, including the filtering features
matrix-disease-list-unfiltered.tsv: tmp/mondo-with-manually-curated-subsets.owl sparql/matrix-disease-list-filters.sparql
	robot query -i $< -f tsv --query sparql/matrix-disease-list-filters.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]MONDO_/MONDO:/g' $@
	sed -i 's/http:[/][/]purl[.]obolibrary[.]org[/]obo[/]mondo#/mondo:/g' $@
	sed -i 's/>//g' $@
.PRECIOUS: matrix-disease-list-unfiltered.tsv

matrix-disease-list-metrics.tsv: tmp/mondo-with-manually-curated-subsets.owl sparql/matrix-disease-list-metrics.sparql
	robot query -i $< -f tsv --query sparql/matrix-disease-list-metrics.sparql $@
	sed -i 's/[?]//g' $@
	sed -i 's/<http:[/][/]purl[.]obolibrary[.]org[/]obo[/]MONDO_/MONDO:/g' $@
	sed -i 's/http:[/][/]purl[.]obolibrary[.]org[/]obo[/]mondo#/mondo:/g' $@
	sed -i 's/>//g' $@
.PRECIOUS: matrix-disease-list-metrics.tsv

# The final MATRIX disease list
matrix-disease-list.tsv: matrix-disease-list-unfiltered.tsv matrix-disease-list-metrics.tsv scripts/matrix-disease-list.py
	pip install -r requirements.txt --break-system-packages
	python scripts/matrix-disease-list.py create-matrix-disease-list -i matrix-disease-list-unfiltered.tsv \
		-m matrix-disease-list-metrics.tsv \
		--subtype-counts-tsv tmp/subtype-counts.tsv \
		-o matrix-disease-list.tsv \
		-e matrix-excluded-diseases-list.tsv \
		--output-included-diseases-template src/included-diseases.robot.tsv \
		--output-excluded-diseases-template src/excluded-diseases.robot.tsv \
		--output-included-diseases-new new-included-diseases-since-last-release.md \
		--output-excluded-diseases-new new-excluded-diseases-since-last-release.md \
		-l matrix-disease-list-unfiltered-processed.tsv \
		-x matrix-disease-list.xlsx \
		-g matrix-disease-groupings.tsv
.PRECIOUS: matrix-disease-list.tsv

# ROBOT template with the disease list designations added as subset declarations
tmp/matrix-list-designations.robot.tsv: matrix-disease-list-unfiltered-processed.tsv matrix-disease-list.tsv
	python scripts/matrix-disease-list.py create-template-from-matrix-disease-list -i $< -o $@
.PRECIOUS: tmp/matrix-list-designations.robot.tsv

# This version of Mondo can help reviewers browsing the hierarchy with the filter designations clearly marked in the disease labels
mondo-with-filter-designations.owl: tmp/mondo-with-manually-curated-subsets.owl tmp/matrix-list-designations.robot.tsv sparql/update-labels-with-list-designation.ru
	$(ROBOT) template -i $< --merge-after --template tmp/matrix-list-designations.robot.tsv \
		query --update sparql/update-labels-with-list-designation.ru \
	 $(ANNOTATE_CONVERT_FILE)
.PRECIOUS: mondo-with-filter-designations.owl

#################################
#### Release system #############
#################################

# Running a GitHub release with the `gh` client.
gh_release:
	@test $(VERSION)
	ls -alt $(ASSETS)
	gh release create $(VERSION) --notes "TBD." --title "$(VERSION)" --draft $(ASSETS)


tmp/grounding.tsv: tmp/mondo.owl tmp/disease-labels.tsv
	runoak -i sqlite:obo:mondo annotate --text-file tmp/disease-labels.tsv -W -O tsv -o $@


#################################
#### Help #######################
#################################


.PHONY: help
help:
	@echo "$$data"

define data
Usage: sh odk.sh make [command]

----------------------------------------
	Command reference
----------------------------------------

Core commands:
* all:	Build all release assets
* help:			Print ODK Usage information
* deploy_site:	Updates the documentation pages on GitHub.
* gh_release: Runs a GitHub release for the current version of the disease list.

Tricks:
* Add -B to the end of your command to force re-running it even if nothing has changed

endef
export data

