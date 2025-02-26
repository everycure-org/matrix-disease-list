from kedro.pipeline import Pipeline, pipeline, node
from . import nodes


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        

        node(
            func=nodes.add_disease_categories,
            inputs = [
                "disease_list",
                "params:disease_categories_txgnn_modified",
                "params:categorization_prompt",
                "prev_list",
                "params:rebuild_cache",
            ],
            outputs = "disease_list_with_txgnn_tags",
            name = "add-txgnn-tags"
        ),
        node(
            func=nodes.add_disease_categories,
            inputs = [
                "disease_list_with_txgnn_tags",
                "params:disease_categories_medical_specialization",
                "params:categorization_prompt",
                "prev_list",
                "params:rebuild_cache",
            ],
            outputs = "disease_list_with_medical_specialty_tags",
            name = "add-medical-specialty-tags"
        ),
        node(
            func=nodes.add_disease_categories,
            inputs = [
                "disease_list_with_medical_specialty_tags",
                "params:disease_categories_anatomical",
                "params:categorization_prompt",
                "prev_list",
                "params:rebuild_cache",
            ],
            outputs = "disease_list_with_anatomical_tags",
            name = "add-tags-anatomical"
        ),
        # node(
        #     func=nodes.enrich_disease_list,
        #     inputs=[
        #         "disease_list_with_anatomical_tags",
        #         "params:preprocessing.enrichment_tags",
        #     ],
        #     outputs="ec_enriched_disease_list",
        #     name="enrich_disease_list",
        # ),

        node(
            func=nodes.enrich_disease_list_single_tag,
            inputs = [
                "disease_list_with_anatomical_tags",
                "params:preprocessing.enrichment_tags.single_input.pathogen.input_params.output_col",
                "params:preprocessing.enrichment_tags.single_input.pathogen",
                "params:preprocessing.enrichment_tags.single_input.pathogen.single_input",
            ],
            outputs = "enriched_disease_list_pathogen",
            name="add-pathogen-tag"
        ),

        node(
            func=nodes.enrich_disease_list_single_tag,
            inputs = [
                "enriched_disease_list_pathogen",
                "params:preprocessing.enrichment_tags.single_input.cancer.input_params.output_col",
                "params:preprocessing.enrichment_tags.single_input.cancer",
                "params:preprocessing.enrichment_tags.single_input.cancer.single_input",
            ],
            outputs = "enriched_disease_list_cancer",
            name="add-cancer-tag"
        ),

        node(
            func=nodes.enrich_disease_list_single_tag,
            inputs = [
                "enriched_disease_list_cancer",
                "params:preprocessing.enrichment_tags.single_input.glucose_dysfunction.input_params.output_col",
                "params:preprocessing.enrichment_tags.single_input.glucose_dysfunction",
                "params:preprocessing.enrichment_tags.single_input.glucose_dysfunction.single_input",
            ],
            outputs = "enriched_disease_list_glucose_dysfunction",
            name="add-glucose_dysfunction-tag"
        ),

        node(
            func=nodes.enrich_disease_list_single_tag,
            inputs = [
                "enriched_disease_list_glucose_dysfunction",
                "params:preprocessing.enrichment_tags.single_input.existing_treatment.input_params.output_col",
                "params:preprocessing.enrichment_tags.single_input.existing_treatment",
                "params:preprocessing.enrichment_tags.single_input.existing_treatment.single_input",
            ],
            outputs = "enriched_disease_list_existing_treatment",
            name="add-existing_treatment-tag"
        ),

        node(
            func=nodes.enrich_disease_list_single_tag,
            inputs = [
                "enriched_disease_list_existing_treatment",
                "params:preprocessing.enrichment_tags.multiple_input.quality_life_years_lost.input_params.output_col",
                "params:preprocessing.enrichment_tags.multiple_input.quality_life_years_lost",
                "params:preprocessing.enrichment_tags.multiple_input.quality_life_years_lost.single_input",
            ],
            outputs = "enriched_disease_list_qoly",
            name="add-qoly-tag"
        ),

        
        node(
            func=nodes.return_final_categories,
            inputs=[
                "enriched_disease_list_qoly",
            ],
            outputs="disease_categories",
            name = "return-final-disease-categories"
        ),


    ])
