import click
import pandas as pd
import logging


def matrix_filter_final_columns(df_disease_list):
    """
    Filter a DataFrame by a specific column and value.
    
    Parameters
    ----------
    df_disease_list : pandas.DataFrame
        The disease list with columns that are used for filtering.
    
    Returns
    -------
    pandas.DataFrame
        The disease list with only the relevant columns.
    """
    return df_disease_list[['category_class', 'label', 'definition', 'synonyms', 'subsets', 'crossreferences']]
                                              

def matrix_disease_filter(df_disease_list_unfiltered):
    """
    Filter a DataFrame by a specific column and value.
    
    Parameters
    ----------
    df_disease_list_unfiltered : pandas.DataFrame
        The disease list, unfiltered, but with columns that are used for filtering.
    
    Returns
    -------
    pandas.DataFrame, pandas.DataFrame
        A tuple of two DataFrames: the first one contains the included diseases, and the second one contains the excluded diseases.
    """
    filter_column = 'official_matrix_filter'
    
    # By default, no disease is included
    df_disease_list_unfiltered[filter_column] = False
    
    # QC: Check for conflicts where both f_matrix_manually_included and f_matrix_manually_excluded are True
    conflicts = df_disease_list_unfiltered[
        df_disease_list_unfiltered['f_matrix_manually_included'] & df_disease_list_unfiltered['f_matrix_manually_excluded']
    ]

    if not conflicts.empty:
        # Format the conflicts nicely
        conflict_str = conflicts.to_string(index=False)
        raise ValueError(f"Conflicts found: The following entries are marked as both manually included and manually excluded:\n{conflict_str}")
    
    # First, we add all manually curated classes to the list
    df_disease_list_unfiltered[filter_column] |= df_disease_list_unfiltered['f_matrix_manually_included'] == True
    
    # Next, we add all leaf classes
    df_disease_list_unfiltered[filter_column] |= df_disease_list_unfiltered['f_leaf'] == True

    # Now, we add all the immediate parents of leaf classes that are mapped to OMIM, ICD, or Orphanet
    df_disease_list_unfiltered[filter_column] |= (
        (df_disease_list_unfiltered['f_leaf_direct_parent'] == True) & 
        (
            (df_disease_list_unfiltered['f_omim'] == True) | 
            (df_disease_list_unfiltered['f_omimps_descendant'] == True) | 
            (df_disease_list_unfiltered['f_icd_category'] == True) |
            (df_disease_list_unfiltered['f_orphanet_disorder'] == True) |
            (df_disease_list_unfiltered['f_orphanet_subtype'] == True)
        )
    )
    
    # Next, we add all diseases corresponding to ICD 10 billable codes
    df_disease_list_unfiltered[filter_column] |= df_disease_list_unfiltered['f_icd_category'] == True
    
    # Next, we add all diseases corresponding to Orphanet disorders
    df_disease_list_unfiltered[filter_column] |= df_disease_list_unfiltered['f_orphanet_disorder'] == True
    
    # Next, we add all diseases corresponding to ClinGen curated conditions
    df_disease_list_unfiltered[filter_column] |= df_disease_list_unfiltered['f_clingen'] == True
    
    # Next, we add all diseases corresponding to OMIM curated diseases
    df_disease_list_unfiltered[filter_column] |= df_disease_list_unfiltered['f_omim'] == True
    
    # Next we remove all susceptibilities, mondo subtypes, and diseases with and/or or with/without
    # UPDATE 13.02.2025: We will for now _not_ remove these, but provide filter columns for them instead
    #df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_mondo_subtype'] == True, filter_column] = False
    #df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_susceptibility'] == True, filter_column] = False
    #df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_andor'] == True, filter_column] = False
    #df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_withorwithout'] == True, filter_column] = False
    
    ## Remove all hereditary diseases without classification. This is imo a dangerous default, but
    ## @jxneli reviewed all 849 cases from the February 2025 release and found that all were indeed
    ## "irrelevant" for drug repurposing, https://github.com/everycure-org/matrix-disease-list/issues/50
    df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_unclassified_hereditary'] == True, filter_column] = False
    
    ## Remove all diseases that are candidates for obsoletion
    ## https://github.com/everycure-org/matrix-disease-list/issues/48
    df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_obsoletion_candidate'] == True, filter_column] = False
    
    ## Remove all paraphilic disorders
    ## https://github.com/everycure-org/matrix-disease-list/issues/42
    df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_paraphilic'] == True, filter_column] = False
    
    
    # Remove disease that were manually excluded
    df_disease_list_unfiltered.loc[df_disease_list_unfiltered['f_matrix_manually_excluded'] == True, filter_column] = False
    
    # Split the DataFrame into two parts: included and excluded diseases
    df_included_diseases = df_disease_list_unfiltered[df_disease_list_unfiltered[filter_column] == True]
    df_excluded_diseases = df_disease_list_unfiltered[df_disease_list_unfiltered[filter_column] == False]

    return df_included_diseases, df_excluded_diseases, df_disease_list_unfiltered 

@click.group()
def cli():
    """A command-line tool to perform various operations."""
    pass

@cli.command()
def help():
    """List available commands and their parameters."""
    commands = {
        'create-matrix-disease-list': 'Load a disease list in TSV format, filter it, and write the output to a new TSV file.'
    }
    for command, description in commands.items():
        click.echo(f"{command}: {description}")


@cli.command()
@click.option('--input-xlsx', '-i', required=True, type=click.Path(exists=True), help='Path to the input Excel file.')
@click.option('--mondo-tsv', '-m', required=True, type=click.Path(exists=True), help='Path to the mondo SSSOM TSV file.')
@click.option('--output-tsv', '-o', required=True, type=click.Path(), help='Path to the output TSV file.')
def create_billable_icd10_template(input_xlsx, mondo_tsv, output_tsv):
    """
    Reads the first sheet of the input XLSX file, modifies ICD-10 codes, filters rows based on matches
    in mondo.sssom.tsv, and writes the result to an output TSV file.
    """
    # Load the first sheet of the Excel file into a pandas DataFrame
    df = pd.read_excel(input_xlsx, sheet_name=0)
    
    # Transform ICD-10 codes in the first column
    df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: f"ICD10CM:{x[:3]}.{x[3:]}" if pd.notna(x) and len(x) > 3 else x)
    
    # Load the mondo SSSOM TSV file
    mondo_df = pd.read_csv(mondo_tsv, comment="#", sep='\t')
    
    # Extract exactMatch ICD10CM codes
    icd10_codes = mondo_df.loc[mondo_df['predicate_id'] == 'skos:exactMatch', 'object_id'].unique()
    
    # Filter the DataFrame for rows with ICD-10 codes present in mondo SSSOM
    icd10_codes_billable = df[df.iloc[:, 0].isin(icd10_codes)]["CODE"].unique()
    
    rows = []
    
    for icd10_code in icd10_codes_billable:
        row_to_add = mondo_df[(mondo_df['predicate_id'] == 'skos:exactMatch') & (mondo_df['object_id'] == icd10_code)][['subject_id', 'object_id']]
        row_to_add['SUBSET']="http://purl.obolibrary.org/obo/mondo#icd10_billable"
        row_to_add['ID']=row_to_add['subject_id']
        row_to_add['ICD10CM_CODE']=row_to_add['object_id']
        rows.append(row_to_add[['ID', 'SUBSET','ICD10CM_CODE']])
    
    robot_template_header = pd.DataFrame({
        'ID': ['ID'],
        'SUBSET': ['AI oboInOwl:inSubset'],
        'ICD10CM_CODE': [""]
        })
    
    df_icd10billable_subsets = pd.concat(rows)
    df_icd10billable_subsets = pd.concat([robot_template_header, df_icd10billable_subsets]).reset_index(drop=True)

    # Write the filtered DataFrame to a TSV file
    df_icd10billable_subsets.to_csv(output_tsv, sep='\t', index=False)

def extract_groupings(subsets, groupings):
    """Extract groupings for list of subsets."""
    result = {grouping: [] for grouping in groupings}
    
    if subsets:
        for subset in subsets.split(";"):
            for grouping in groupings:
                if grouping in subset:
                    # Extract the specific part after the grouping
                    subset_tag = subset.replace("mondo:","").replace(grouping,"").replace(" ","").strip("_")
                    if subset_tag != "member":
                        result[grouping].append(subset_tag)
    return {key: "|".join(values) if values else "" for key, values in result.items()}


@cli.command()
@click.option('--input-file', '-i', required=True, type=click.Path(exists=True), help="Input TSV file")
@click.option('--output-included-diseases', '-o', required=True, type=click.Path(), help="Included disease list as TSV file")
@click.option('--output-included-diseases-template', required=True, type=click.Path(), help="Included disease list template for manual curation as TSV file")
@click.option('--output-excluded-diseases-template', required=True, type=click.Path(), help="Excluded disease list template for manual curation as TSV file")
@click.option('--output-included-diseases-new', required=True, type=click.Path(), help="Included disease list update since last release as TSV file")
@click.option('--output-excluded-diseases-new', required=True, type=click.Path(), help="Excluded disease list update since last release as TSV file")
@click.option('--output-excluded-diseases', '-e', required=False, type=click.Path(), help="Excluded disease list as TSV file")
@click.option('--output-unfiltered-diseases-processed', '-l', required=False, type=click.Path(), help="Unfiltered disease list with added filter columns as TSV file")
@click.option('--output-xlsx', '-x', required=False, type=click.Path(), help="Excluded disease list as TSV file")
@click.option('--output-disease-groupings', '-g', required=False, type=click.Path(), help="A table with Mondo disease groupings")
def create_matrix_disease_list(input_file, output_included_diseases, output_included_diseases_template, output_excluded_diseases_template, output_included_diseases_new, output_excluded_diseases_new, output_excluded_diseases, output_unfiltered_diseases_processed, output_xlsx, output_disease_groupings):
    """
    Load a TSV file, filter it by a specific column and value, and write the result to a new TSV file.
    """
    # Load the TSV file
    df = pd.read_csv(input_file, sep='\t')
    
    # Filter the DataFrame
    df_included_diseases, df_excluded_diseases, df_matrix_disease_filter_modified = matrix_disease_filter(df)
    df_included_diseases = matrix_filter_final_columns(df_included_diseases)
    df_excluded_diseases = matrix_filter_final_columns(df_excluded_diseases)
    
    # Before we write the list to a final file, we make load the old list to figure out which diseases are new.
    df_old_included_disease = pd.read_csv(output_included_diseases, sep='\t') 
    df_included_diseases_template = pd.read_csv(output_included_diseases_template, sep='\t')
    df_new_included_diseases_compared_to_release = df_included_diseases[~df_included_diseases['category_class'].isin(df_old_included_disease['category_class'])]
    df_new_included_diseases = df_new_included_diseases_compared_to_release[~df_new_included_diseases_compared_to_release['category_class'].isin(df_included_diseases_template['ID'])]
    df_new_included_diseases = df_new_included_diseases[['category_class', 'label']]
    df_new_included_diseases.columns = ['ID', 'LABEL']
    df_new_included_diseases['SUBSET'] = ''
    df_new_included_diseases['CONTRIBUTOR'] = ''
    df_new_included_diseases['COMMENT'] = ''
    df_included_diseases_template = pd.concat([df_included_diseases_template, df_new_included_diseases])
    df_included_diseases_template.to_csv(output_included_diseases_template, sep='\t', index=False)
    
    if output_included_diseases_new:
        # Write markdown output for updates
        df_new_included_diseases_compared_to_release[['category_class','label']].to_markdown(output_included_diseases_new, index=False)
    
    # Same with newly excluded diseases
    df_old_excluded_disease = pd.read_csv(output_excluded_diseases, sep='\t') 
    df_excluded_diseases_template = pd.read_csv(output_excluded_diseases_template, sep='\t')
    df_new_excluded_diseases_compared_to_release = df_excluded_diseases[~df_excluded_diseases['category_class'].isin(df_old_excluded_disease['category_class'])]
    df_new_excluded_diseases = df_new_excluded_diseases_compared_to_release[~df_new_excluded_diseases_compared_to_release['category_class'].isin(df_excluded_diseases_template['ID'])]
    df_new_excluded_diseases = df_new_excluded_diseases[['category_class', 'label']]
    df_new_excluded_diseases.columns = ['ID', 'LABEL']
    df_new_excluded_diseases['SUBSET'] = ''
    df_new_excluded_diseases['CONTRIBUTOR'] = ''
    df_new_excluded_diseases['COMMENT'] = ''
    # Filter out IDs that are already in df_excluded_diseases_template this is necessary of this code
    # is run before the official disease list is updated.
    df_new_excluded_diseases = df_new_excluded_diseases[~df_new_excluded_diseases['ID'].isin(df_excluded_diseases_template['ID'])]
    df_excluded_diseases_template = pd.concat([df_excluded_diseases_template, df_new_excluded_diseases])
    df_excluded_diseases_template.to_csv(output_excluded_diseases_template, sep='\t', index=False)
    
    if output_excluded_diseases_new:
        # Write markdown output for updates
        df_new_excluded_diseases_compared_to_release[['category_class','label']].to_markdown(output_excluded_diseases_new, index=False)

    
    # Write the final disease list to the output file
    df_included_diseases.to_csv(output_included_diseases, sep='\t', index=False)
    click.echo(f"Filtered disease list written to {output_included_diseases}")
    
    if output_excluded_diseases:
        df_excluded_diseases.to_csv(output_excluded_diseases, sep='\t', index=False)
        click.echo(f"Excluded diseases written to {output_excluded_diseases}")
    
    if output_unfiltered_diseases_processed:
        df_matrix_disease_filter_modified.to_csv(output_unfiltered_diseases_processed, sep='\t', index=False)
        click.echo(f"Unfiltered diseases written to {output_unfiltered_diseases_processed}")

    if output_disease_groupings:
        curated_disease_groupings = ["harrisons_view", "matrix_txgnn_grouping", "mondo_top_grouping"]
        llm_disease_groupings = [ "matrix_llm__medical_specialization",	"matrix_llm__txgnn", "matrix_llm__anatomical", "matrix_llm__is_pathogen_caused", "matrix_llm__is_cancer", "matrix_llm__is_glucose_dysfunction", "matrix_llm__tag_existing_treatment", "matrix_llm__tag_qaly_lost"]
        disease_groupings = curated_disease_groupings + llm_disease_groupings
        df_disease_groupings = df_matrix_disease_filter_modified[["category_class", "label", "subsets"]]
        
        # Apply the function to extract groupings
        df_disease_groupings_extracted = df_disease_groupings["subsets"].apply(
            lambda x: extract_groupings(x, disease_groupings)
        ).apply(pd.Series)

        # Combine with the original DataFrame
        df_disease_groupings_pivot = pd.concat(
            [df_disease_groupings[["category_class", "label"]], df_disease_groupings_extracted], axis=1
        )
        df_disease_groupings_pivot.sort_values(by="category_class", inplace=True)
        df_disease_groupings_pivot.to_csv(output_disease_groupings, sep='\t', index=False)
        click.echo(f"Disease groupinhs written to {output_disease_groupings}")

    
    if output_xlsx:
        with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
            df_included_diseases.to_excel(writer, sheet_name='Matrix Disease List', index=False)
            df_excluded_diseases.to_excel(writer, sheet_name='Excluded Diseases', index=False)
            df_matrix_disease_filter_modified.to_excel(writer, sheet_name='Unfiltered disease list', index=False)
            df.to_excel(writer, sheet_name='Unfiltered Diseases', index=False)
        click.echo(f"All tables are compiled together as an Excel spreadsheet in {output_xlsx}")

@cli.command()
@click.option('-i', '--input', 'input_file', required=True, type=click.Path(exists=True), help='MATRIX disease list in TSV format')
@click.option('-o', '--output', 'output_file', required=True, type=click.Path(), help='Output TSV file to write ROBOT template')
def create_template_from_matrix_disease_list(input_file, output_file):
    """
    Create a template from the matrix disease list.
    """
    # Load the input TSV file
    df_input = pd.read_csv(input_file, sep='\t')
    
    robot_template_header = pd.DataFrame({
        'category_class': ['ID'],
        'subset': ['AI oboInOwl:inSubset']
        })

    # Select only the 'category_class' column from df_input
    df_template = df_input[['category_class']]
    
    df_template['subset'] = df_input['official_matrix_filter'].apply(
        lambda x: 'http://purl.obolibrary.org/obo/mondo#matrix_included' if x else 'http://purl.obolibrary.org/obo/mondo#matrix_excluded'
    )

    df_template = pd.concat([robot_template_header, df_template]).reset_index(drop=True)

    df_template.to_csv(output_file, sep='\t', index=False)
    
    click.echo(f"Template created and written to {output_file}") 


@cli.command()
@click.option(
    '-i', '--input-file', required=True, type=click.Path(exists=True), help='Path to the input TSV file.'
)
@click.option(
    '-o', '--output-file', required=True, type=click.Path(), help='Path to save the reformatted TSV file.'
)
@click.option(
    '-c', '--contributor', multiple=True, help='Contributor ORCIDs. Can specify multiple values.'
)
@click.option(
    '-r', '--repair-invalid-values', default=True, help='Replaces whitespace in values with underscores.'
)
def format_llm_disease_categorization(input_file, output_file, contributor, repair_invalid_values, log_count=20):
    """
    Reformat a TSV file to include LABEL, SUBSET, CONTRIBUTOR, and COMMENT columns.
    """
    import re
    log_count = 0
    df = pd.read_csv(input_file, sep='\t', dtype=str)
    contributors = '|'.join(contributor)

    reformatted_rows = []

    for _, row in df.iterrows():
        id_ = row['category_class']

        # Process all columns after the first one as subsets
        for column_name in df.columns[1:]:
            col = column_name.lower()
            subset_prefix = f'obo:mondo#matrix_llm__{col}'
            subset_prefix_member = f'obo:mondo#matrix_llm__{col}_member'
            if isinstance(row[column_name], str):
                specific_subsets = row[column_name].strip().split('|')
            
            valid_values = [v.strip().lower() for v in specific_subsets if re.match(r'^\w+$', v.strip())]
            invalid_values = [v.strip() for v in specific_subsets if not re.match(r'^\w+$', v.strip())]
            if repair_invalid_values:
                valid_values += [re.sub(r"\W", "_", v.strip().lower()) for v in invalid_values]
            for value in invalid_values:
                if log_count < log_count:
                    logging.warning(f"Invalid value '{value}' found in column '{col}' for ID '{id_}'. Only showing only {log_count} warnings for brevity.")
                    log_count += 1
            prefixed_subsets_specific = [f"{subset_prefix}_{subset.strip()}" for subset in valid_values]
            all_subsets_list = [subset_prefix_member] + prefixed_subsets_specific
            all_subsets = '|'.join(all_subsets_list)
            
            reformatted_rows.append({
                'ID': id_,
                'SUBSET': all_subsets,
                'CONTRIBUTOR': contributors
                })
                

    reformatted_df = pd.DataFrame(reformatted_rows)
    
    robot_template_header = pd.DataFrame({
        'ID': ['ID'],
        'SUBSET': ['AI oboInOwl:inSubset SPLIT=|'],
        'CONTRIBUTOR': ['>AI dc:contributor SPLIT=|'],
        })
    
    output_df = pd.concat([robot_template_header, reformatted_df]).reset_index(drop=True)
    output_df.sort_values(by='ID', inplace=True)
    output_df.to_csv(output_file, sep='\t', index=False)

def match_patterns_efficiently(df, label_column, patterns):
    import re
    label_match = []
    label_pattern = []

    for _, row in df.iterrows():
        label = row[label_column]
        match_found = False

        for key, pattern in patterns.items():
            match = re.match(pattern, label)
            
            if match:
                match = match.group(1)
            else:
                match = None
            
            if match:
                label_match.append(match)
                label_pattern.append(key)
                match_found = True
                break  # Exit pattern loop on first match

        if not match_found:
            label_match.append(None)
            label_pattern.append(None)

    # Add the results to the DataFrame
    df["label_match"] = label_match
    df["label_pattern"] = label_pattern
    return df

@cli.command()
@click.option(
    '-l', '--labels', required=True, type=click.Path(exists=True), help='Path to a TSV with Mondo labels.'
)
@click.option(
    '-o', '--output-all-matches', required=True, type=click.Path(), help='Path to save the full output TSV file.'
)
@click.option(
    '-r', '--output-template', required=True, type=click.Path(), help='Path to save the template.'
)
@click.option(
    '-g', '--output-grouping-counts', required=False, type=click.Path(), help='Path to save grouping counts.'
)
@click.option(
    '-t', '--threshold-subtype-count', required=True, type=int, help='Path to save the template.'
)
def create_template_with_high_granularity_subtypes(labels, output_all_matches, output_template, output_grouping_counts, threshold_subtype_count=10):
    """
    Reformat a TSV file;
    """

    # Load the data
    df_labels = pd.read_csv(labels, sep="\t")
    df_labels = df_labels.dropna(subset=['LABEL'])
    df_labels = df_labels[df_labels['ID'].str.startswith('MONDO:')]
    df_labels = df_labels[["ID", "LABEL"]]
    df_labels.columns = ["category_class", "label"]

    # Define patterns
    patterns = {
        "x_type_ad": "(.*)[ ]type[ ][A-Z0-9]+$",
        "x_group_a": "(.*)[ ]group [A-Z]+$",
        "x_d": "(.*)[ ][0-9]+[0-9A-Za-z]*$",
        "x_d_ca": "(.*)[ ][0-9]+[0-9A-Za-z]*[,][ ][/A-Za-z0-9-_, ()]+$",
        "x_td_a": "(.*)[ ]type[ ][0-9]+[ ][/A-Za-z0-9-_, ()]+$",
        "x_d_a": "(.*)[ ][0-9]+[0-9A-Za-z]*[ ][/A-Za-z0-9-_, ()]+$",
        "x_da_a": "(.*)[ ][0-9]+[a-z]*[ ][/A-Za-z0-9-_, ()]+$",
        "x_dp": "(.*)[ ][0-9]+p$",
        "x_a": "(.*)[ ][A-Z]+$",
        "x_a_type": "(.*)[,][ ][A-Za-z0-9-_]+[ ]type$",
        "x_type_I": "(.*)[ ]type[ ](X{0,3})(IX|IV|V?I{0,3})+$",
        "x_I": "(.*)[ ](X{0,3})(IX|IV|V?I{0,3})+$",
    }

    df_disease_list_matched = match_patterns_efficiently(df_labels, "label", patterns)

    df_disease_list_matched_subset = df_disease_list_matched[["category_class", "label", "label_match", "label_pattern"]]
    df_disease_list_matched_subset.sort_values(by="label_match", inplace=True)
    
    # This step is to check if an extracted label_match is a valid label in the original disease list
    df_disease_list_matched_subset_with_matched_label_ids = pd.merge(df_disease_list_matched_subset, df_labels[['label','category_class']], left_on="label_match", right_on="label", how="left")
    
    if output_all_matches:
        df_disease_list_matched_subset_with_matched_label_ids.to_csv(output_all_matches, sep="\t", index=False)
    
    # Count the number of subtypes for each disease
    grouped_data = df_disease_list_matched_subset_with_matched_label_ids.groupby(["category_class_y", "label_y"]).size()
    grouped_df = grouped_data.reset_index(name="count")
    if output_grouping_counts:
        grouped_df.to_csv(output_grouping_counts, sep="\t", index=False)
    
    # Filter the DataFrame to only include subtypes with a count greater than the threshold
    top_grouped_df = grouped_df[grouped_df["count"] > threshold_subtype_count]
    
    # Get the subset of the DataFrame that matches the top groupings
    top_subset_df = df_disease_list_matched_subset_with_matched_label_ids[df_disease_list_matched_subset_with_matched_label_ids['category_class_y'].notna() & df_disease_list_matched_subset_with_matched_label_ids['category_class_y'].isin(top_grouped_df['category_class_y'])]

    # Display the final filtered DataFrame
    final_subset_df = top_subset_df[["category_class_x", "label_x"]].drop_duplicates().sort_values(by="category_class_x")
    final_subset_df['subset'] = "http://purl.obolibrary.org/obo/mondo#mondo_subtype"
    final_subset_df['contributor'] = "https://orcid.org/0000-0002-7356-1779"
    final_subset_df.columns=["ID", "LABEL", "SUBSET", "CONTRIBUTOR"]
    
    robot_template_header = pd.DataFrame({
        'ID': ['ID'],
        'LABEL': [''],
        'SUBSET': ['AI oboInOwl:inSubset SPLIT=|'],
        'CONTRIBUTOR': ['>AI dc:contributor SPLIT=|'],
        })
    
    output_df = pd.concat([robot_template_header, final_subset_df]).reset_index(drop=True)
    output_df.sort_values(by='ID', inplace=True)
    
    output_df.to_csv(output_template, sep="\t", index=False)


if __name__ == '__main__':
    cli()
