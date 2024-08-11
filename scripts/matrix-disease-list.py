import click
import pandas as pd


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
@click.option('--input-file', '-i', required=True, type=click.Path(exists=True), help="Input TSV file")
@click.option('--output-included-diseases', '-o', required=True, type=click.Path(), help="Included disease list as TSV file")
@click.option('--output-included-diseases-template', required=True, type=click.Path(), help="Included disease list template for manual curation as TSV file")
@click.option('--output-excluded-diseases-template', required=True, type=click.Path(), help="Excluded disease list template for manual curation as TSV file")
@click.option('--output-excluded-diseases', '-e', required=False, type=click.Path(), help="Excluded disease list as TSV file")
@click.option('--output-unfiltered-diseases-processed', '-l', required=False, type=click.Path(), help="Unfiltered disease list with added filter columns as TSV file")
@click.option('--output-xlsx', '-x', required=False, type=click.Path(), help="Excluded disease list as TSV file")
def create_matrix_disease_list(input_file, output_included_diseases, output_included_diseases_template, output_excluded_diseases_template, output_excluded_diseases, output_unfiltered_diseases_processed, output_xlsx):
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
    df_new_included_diseases = df_included_diseases[~df_included_diseases['category_class'].isin(df_old_included_disease['category_class'])]
    df_new_included_diseases = df_new_included_diseases[['category_class', 'label']]
    df_new_included_diseases.columns = ['ID', 'LABEL']
    df_new_included_diseases['SUBSET'] = ''
    df_new_included_diseases['CONTRIBUTOR'] = ''
    df_new_included_diseases['COMMENT'] = ''
    df_included_diseases_template = pd.concat([df_included_diseases_template, df_new_included_diseases])
    df_included_diseases_template.to_csv(output_included_diseases_template, sep='\t', index=False)
    
    # Same with newly excluded diseases
    df_old_excluded_disease = pd.read_csv(output_excluded_diseases, sep='\t') 
    df_excluded_diseases_template = pd.read_csv(output_excluded_diseases_template, sep='\t')
    df_new_excluded_diseases = df_excluded_diseases[~df_excluded_diseases['category_class'].isin(df_old_excluded_disease['category_class'])]
    df_new_excluded_diseases = df_new_excluded_diseases[['category_class', 'label']]
    df_new_excluded_diseases.columns = ['ID', 'LABEL']
    df_new_excluded_diseases['SUBSET'] = ''
    df_new_excluded_diseases['CONTRIBUTOR'] = ''
    df_new_excluded_diseases['COMMENT'] = ''
    df_excluded_diseases_template = pd.concat([df_excluded_diseases_template, df_new_excluded_diseases])
    df_excluded_diseases_template.to_csv(output_excluded_diseases_template, sep='\t', index=False)
    
    # Write the final disease list to the output file
    df_included_diseases.to_csv(output_included_diseases, sep='\t', index=False)
    click.echo(f"Filtered disease list written to {output_included_diseases}")
    
    if output_excluded_diseases:
        df_excluded_diseases.to_csv(output_excluded_diseases, sep='\t', index=False)
        click.echo(f"Excluded diseases written to {output_excluded_diseases}")
    
    if output_unfiltered_diseases_processed:
        df_matrix_disease_filter_modified.to_csv(output_unfiltered_diseases_processed, sep='\t', index=False)
        click.echo(f"Unfiltered diseases written to {output_unfiltered_diseases_processed}")
    
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
    df_template['subset'] = 'http://purl.obolibrary.org/obo/mondo#matrix_included'

    df_template = pd.concat([robot_template_header, df_template]).reset_index(drop=True)

    df_template.to_csv(output_file, sep='\t', index=False)
    
    click.echo(f"Template created and written to {output_file}") 

if __name__ == '__main__':
    cli()
