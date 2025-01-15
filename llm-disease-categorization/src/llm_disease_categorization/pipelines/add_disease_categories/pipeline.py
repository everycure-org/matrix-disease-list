"""
This is a boilerplate pipeline 'add_disease_categories'
generated using Kedro 0.19.10
"""

from kedro.pipeline import Pipeline, pipeline, node
from . import nodes


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=nodes.add_disease_categories,
            inputs = [
                "disease_list",
                "params:disease_categories_txgnn_modified",
                "params:categorization_prompt"
            ],
            outputs = "disease_list_with_txgnn_tags",
            name = "add-txgnn-tags"
        ),
        node(
            func=nodes.add_disease_categories,
            inputs = [
                "disease_list_with_txgnn_tags",
                "params:disease_categories_medical_specialization",
                "params:categorization_prompt"
            ],
            outputs = "disease_list_with_medical_specialty_tags",
            name = "add-medical-specialty-tags"
        ),
        node(
            func=nodes.add_disease_categories,
            inputs = [
                "disease_list_with_medical_specialty_tags",
                "params:disease_categories_anatomical",
                "params:categorization_prompt"
            ],
            outputs = "disease_list_with_anatomical_tags",
            name = "add-tags-anatomical"
        ),
        node(
            func=nodes.return_final_categories,
            inputs=[
                "disease_list_with_anatomical_tags",
                "params:disease_categories_txgnn_modified",
                "params:disease_categories_anatomical",
                "params:disease_categories_medical_specialization"
            ],
            outputs="disease_categories",
            name = "return-final-disease-categories"
        )

    ])
