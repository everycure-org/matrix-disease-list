import click
import pandas as pd

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
@click.option('--output-file', '-o', required=True, type=click.Path(), help="Output TSV file")
@click.option('--filter-column', '-f', required=True, type=str, help="Column to filter on")
@click.option('--filter-value', '-v', required=True, type=str, help="Value to filter by")
def create_matrix_disease_list(input_file, output_file, filter_column, filter_value):
    """
    Load a TSV file, filter it by a specific column and value, and write the result to a new TSV file.
    """
    # Load the TSV file
    df = pd.read_csv(input_file, sep='\t')
    
    # Filter the DataFrame
    filtered_df = df[df[filter_column] == filter_value]
    
    # Write the filtered DataFrame to a new TSV file
    filtered_df.to_csv(output_file, sep='\t', index=False)
    
    click.echo(f"Filtered data written to {output_file}")

if __name__ == '__main__':
    cli()
