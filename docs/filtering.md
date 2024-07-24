## Default filters for Disease List

Here we outline and motivate the various filters we apply to construct the _diagnosable, clinically actionable diseases_.
As described in our [workflow specification](workflow.md), these filters serve as _heuristics_ and are gradually overwritten by community and internal expert feedback.

_List of current heurstics_:

- [ICD 10 CM Filter](#icd10)

<a id="icd10"></a>

### ICD 10 CM Filter

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

##### Limitations

- Mondo mappings to ICD10CM are currently incomplete