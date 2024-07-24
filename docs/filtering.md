## Filters for Disease List

Here we outline and motivate the various filters we apply to construct the "druggable disease list". 

### Leaf Filter

#### Heuristic

1. If a disease has no ontological children, it is, by default, included in the list

#### Background

"Leaf diseases", ie the most specific disease terms in the ontology, most often represent disease subtypes. For genetic diseases, these represents diseases caused by variation in a specific gene. 

### Orphanet Subtype Filter

#### Heuristic

1. If a disease term in Mondo has a 'ordo_subtype_of_a_disorder' subset annotation, it is, by default, included in the list

#### Background

Orphanet organized their rare disorders as "group of disorders", "disorders", and "subtype of disorders". They define "subtype of disorders" as sub-forms of a disease based on distinct presentation, etiology, or histological aspect. [REF]
The Mondo disease terms representing diseases considered as "subtype of disorders" in Orphanet are annotated with the 'ordo_subtype_of_a_disorder' subset.
These diseases are most often the most specific disease terms (most often "lead diseases").

### Orphanet Disorder Filter

#### Heuristic

1. If a disease term in Mondo has a 'ordo_disorder' subset annotation, it is, by default, included in the list

#### Background

Orphanet organized their rare disorders as "group of disorders", "disorders", and "subtype of disorders". They define "disorders" as entities including diseases, syndromes, anomalies and particular clinical situations. "Disorders" are clinically homogeneous entities described in at least two independent individuals, confirming that the clinical signs are not associated by fortuity. [REF]
Orphanet conciders this level of classification as "diagnosable" disorder. 
These diseases are most often the ontological parents of "disease subtypes"


### OMIM Filter

#### Heuristic

1. If a disease has an exact match to an OMIM identifier (ie disease entry), it is, by default, included in the list

#### Background

The Online Mendelian Inheritance in Man (OMIM, https://www.omim.org/) catalogs human genes and genetic disorders and traits. All OMIM genetic disorders are represented in Mondo as a Mondo term with an "equivalent" (ie exact) cross-reference to OMIM.
We concider OMIM diseases/disorders as diagnosable (since they are reported in the database)

### ICD10 CM Filter

#### Heuristic

1. If a disease has an exact match to an ICD 10 category code, it is, by default, included in the list
1. If a disease has an exact match to an ICD 10 chapter or chapter header code, it is, by default, excluded from the list

#### Background

There are a few different types of ICD-10 codes that can be roughly identified by their structure:

1. Chapter codes (or block codes), for example `A00-B99` (Certain infectious and parasitic diseases). These codes can be recognised by containing a dash (`-`) character.
1. Chapter headers (or chapter titles), for example `A00` (Cholera). These can be identified by neither containing a dash, nor a period (`.`) character.
1. Category codes (or subcategory codes), for example: `A01.1` (Paratyphoid fever A). These can be recognized by containing a period (`.`) character.

Usually, we can assume the following:

1. The codes with dashes (chapter codes) represent broad categories of diseases.
1. The codes with periods (category/subcategory codes) represent more specific diagnoses.
1. The codes without dashes or periods (chapter headers) are usually the top-level categories within each chapter.

In clinical and coding contexts, people often refer to the codes with periods as the "billable codes" or "billable ICD-10 codes" because these are typically the ones used for specific diagnoses in medical billing and record-keeping. Codes without a period (chapter headers) are generally not billable, and Codes with dashes (chapter codes/block codes) are never billable.

However, it's important to note that not all codes with periods are billable. Some may require additional digits for specificity. The exact rules can vary slightly depending on the specific implementation of ICD-10 (such as ICD-10-CM in the United States), but generally, the most specific codes (usually those with periods) are the billable ones.

### OMIMPS Filter

#### Heuristic

1. If a disease has an exact match to an OMIMPS identifier, it is, by default, excluded from the list

#### Background

OMIM Phenotypic Series (OMIMPS) group diseases based on similar phenotypes. 
OMIMPS most often refers to the general disease when the OMIM terms are gene-specific subtypes of the disease. For example, the OMIM-PS ["Usher syndrome"](https://www.omim.org/phenotypicSeries/PS276900) includes all subtypes of Usher syndrome.
Sometimes, the OMIMPS group terms based on phenotype similarities. (for example: ["Intellectual developmental disorder, X-linked syndromic"](https://www.omim.org/phenotypicSeries/PS309510))
By nature, Mondo terms representing OMIMPS entry are not actual diseases but group of diseases.

### OMIMPS descendant Filter

#### Heuristic

1. If a disease is a subclass of a disease that has an exact match to an OMIMPS identifier, it is, by default, included in the list

#### Background

Since OMiMPS group diseases, we determined that ontological children of OMIMPS should be diseases that we would want to include. These would include terms corresponding to OMIM terms, and possibly other disease terms

### Grouping subset Filter

#### Heuristic

1. If a disease term in Mondo has a 'ordo_group_of_disorders' subset annotation, it is, by default, excluded in the list
1. If a disease term in Mondo has a 'disease_grouping' subset annotation, it is, by default, excluded in the list
1. If a disease term in Mondo has a 'harrisons_view' subset annotation, it is, by default, excluded in the list
1. If a disease term in Mondo has a 'rare_grouping' subset annotation, it is, by default, excluded from the list

#### Background

By nature, Mondo terms in the following subsets are not actual diseases but group of diseases. 
- _'ordo_group_of_disorders' subset_
Orphanet organized their rare disorders as "group of disorders", "disorders", and "subtype of disorders". They define "group of disorders" as a collection of disease/clinical entities sharing a given characteristic. [REF]
- _'disease_grouping' subset_
Terms in this subset have been manually curated and determined to be a grouping term.
- _'harrisons_view' subset_
Mondo's high-level classification was created based on the Harrison’s Principle of Internal Medicine textbook. Terms representing this high-level classification are annotated with the 'harrisons_view' subset
- _'rare_grouping' subset_
The ontological parent of rare diseases (see Mondo rare disease subset [here](https://mondo.readthedocs.io/en/latest/editors-guide/rare-disease-subset/))

### Grouping Subset Ancestor Filter

#### Heuristic

1. If a disease is an ontological parent of a disease that is a grouping term (as defined in the "Grouping Subset Filter" section), it is, by default, excluded from the list

#### Background

Ontologically, a parent of a grouping class would itself be a grouping class 

### Leaf Direct Parent Filter

#### Heuristic

1. This filter indicates if a disease is a direct parent of a leaf term
1. This filter is for information purposes and is not used to include/exclude terms from the list.

#### Background

This filter exists for information purposes. We think that the majority of the "leaf direct parent" would also be in the "orphanet disorder" subset and in the "OMIM" subset, and therefore whould be included in the list

### Subtype Subset Descendant Filter

#### Heuristic

1. This filter indicates if a disease is an ontological child of a "subtype of disorders" term
1. This filter is for information purposes and is not used to include/exclude terms from the list.

#### Background

This filter exists for information purposes. We think that the majority of the "orphanet subtype of disorder" would be leaf terms as they are specific. However, if there is a term that is an ontological child of an "orphanet subtype of disorder", it might need to be be included in the list .
