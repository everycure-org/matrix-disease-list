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
    return df_disease_list[['category_class', 'label', 'definition', 'synonyms', 'subsets', 'icd10_xrefs']]
                                              

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
    
    # First, we add all leaf classes
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
    
    # Split the DataFrame into two parts: included and excluded diseases
    df_included_diseases = df_disease_list_unfiltered[df_disease_list_unfiltered[filter_column] == True]
    df_excluded_diseases = df_disease_list_unfiltered[df_disease_list_unfiltered[filter_column] == False]

    return df_included_diseases, df_excluded_diseases 

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
@click.option('--output-excluded-diseases', '-e', required=False, type=click.Path(), help="Excluded disease list as TSV file")
@click.option('--output-xlsx', '-x', required=False, type=click.Path(), help="Excluded disease list as TSV file")
def create_matrix_disease_list(input_file, output_included_diseases, output_excluded_diseases, output_xlsx):
    """
    Load a TSV file, filter it by a specific column and value, and write the result to a new TSV file.
    """
    # Load the TSV file
    df = pd.read_csv(input_file, sep='\t')
    
    # Filter the DataFrame
    df_included_diseases, df_excluded_diseases = matrix_disease_filter(df)
    df_included_diseases = matrix_filter_final_columns(df_included_diseases)
    df_excluded_diseases = matrix_filter_final_columns(df_excluded_diseases)
    
    # Write the filtered DataFrame to a new TSV file
    df_included_diseases.to_csv(output_included_diseases, sep='\t', index=False)
    click.echo(f"Filtered disease list written to {output_included_diseases}")
    
    if output_excluded_diseases:
        df_excluded_diseases.to_csv(output_excluded_diseases, sep='\t', index=False)
        click.echo(f"Excluded diseases written to {output_excluded_diseases}")
    
    if output_xlsx:
        with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
            df_included_diseases.to_excel(writer, sheet_name='Matrix Disease List', index=False)
            df_excluded_diseases.to_excel(writer, sheet_name='Excluded Diseases', index=False)
            df.to_excel(writer, sheet_name='Unfiltered Diseases', index=False)
        click.echo(f"Excluded diseases written to {output_xlsx}")   

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
