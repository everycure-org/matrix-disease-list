import pandas as pd
import getpass
pd.options.mode.chained_assignment = None
import difflib as dl
import re
import requests
from io import StringIO
from typing import List
from tqdm import tqdm
import json
import os
from typing import List, Dict, Optional, Any
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from functools import cache

import pickle
import functools

testing = False
limit = 100

def file_cache(cache_file="cache.pkl"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    cache = pickle.load(f)
            else:
                cache = {}

            key = (args, tuple(kwargs.items()))  # Create a hashable key from args and kwargs

            if key in cache:
                return cache[key]

            result = func(*args, **kwargs)
            cache[key] = result

            with open(cache_file, "wb") as f:
                pickle.dump(cache, f)

            return result

        return wrapper
    return decorator


def add_disease_categories(list_in:pd.DataFrame, params:str, base_prompt:dict, old_list: pd.DataFrame, rebuild_cache: bool) -> pd.DataFrame:

    category_tag = params['name']
    category_list = params['categories']


    cache = {}
    if not rebuild_cache:
        for idx, row in old_list.iterrows():
            cache[row['category_class']]=row[category_tag]

    categories_col = []
    disease_list = str(category_list)
    #print(disease_list)
    for idx, row in tqdm(list_in.iterrows(), total=len(list_in), desc="adding disease categories"):
        prompt = f"{base_prompt} {row['label'].upper()}. CATEGORY LIST: {disease_list}. If multiple items, do not include \'other\'. Use no quotation marks or \' symbols and delimit with vertical pipe | only when there are multiple entries."
        #print(prompt)
        success = False
        attempts=0
        #print(prompt)
        if row['category_class'] in cache:
            categories_col.append(cache[row['category_class']])
        else:
            while not success:
                try:
                    response = query_ollama(prompt)['response']
                    categories_col.append(response)
                    success = True
                except Exception as e:
                    print(e)
                    attempts+=1
                if attempts > 5:
                    success = True
                    categories_col.append("error") 
    list_in[category_tag]=categories_col
    return list_in

@file_cache()
def query_ollama(
    prompt: str,
    #model: str = "hf.co/bartowski/Llama-3.3-70B-Instruct-GGUF:IQ2_S",
    model: str = "llama3.1",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    url: str = "http://localhost:11434"
    ) -> Dict[str, Any]:
    """
    Send a prompt to a locally running Ollama model and return its response.
    
    Args:
        prompt (str): The main prompt/question to send to the model
        model (str): Name of the model to use (default is Llama-3.3-70B)
        system_prompt (str, optional): System prompt to set context/behavior
        temperature (float): Controls randomness (0.0 to 1.0)
        max_tokens (int, optional): Maximum number of tokens to generate
        top_p (float, optional): Nucleus sampling parameter
        top_k (int, optional): Top-k sampling parameter
        url (str): Base URL for the Ollama API
        
    Returns:
        Dict[str, Any]: Response from the model containing generated text and metadata
        
    Raises:
        requests.exceptions.RequestException: If API request fails
        json.JSONDecodeError: If response parsing fails
    """
    
    # Construct request payload
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    # Add optional parameters if provided
    if system_prompt:
        payload["system"] = system_prompt
    if max_tokens:
        payload["options"]["num_predict"] = max_tokens
    if top_p:
        payload["options"]["top_p"] = top_p
    if top_k:
        payload["options"]["top_k"] = top_k

    try:
        # Send POST request to Ollama API
        response = requests.post(
            f"{url.rstrip('/')}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to communicate with Ollama API: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Ollama API response: {str(e)}")


def return_final_categories(inList: pd.DataFrame) -> pd.DataFrame:
    inList.drop(['label', 'definition', 'synonyms', 'subsets', 'crossreferences'], axis=1, inplace=True)
    return inList


#################################################################
#### Additional EC Categories ##################################
###############################################################


def generate_tag(
    disease_list: List,
    id_list: List,
    model, 
    definitions: str = None, 
    synonyms: str = None, 
    raw_prompt: str = None,
    old_list: pd.DataFrame = None, 
    rebuild_cache: bool = None, 
    category_tag: str = None
) -> List:
    """Temporary function to generate tags based on provided prompts and params through OpenAI API call.

    This function is temporary and will be removed once we have tags embedded in the disease list.

    Args:
        disease_list: list- list of disease for which tags should be generated.
        definitions: str - (optional) definition of the disease, needed for prompts requiring multiple inputs.
        synonyms: str - (optional) synonyms of the disease, needed for prompts requiring multiple inputs.
        prompt: str - prompt for the tag generation
        llm_model: str - name of the llm model to use for tag generation
    Returns
        List of tags generated by the API call.
    """

    
    # Initialize the output parser
    output_parser = CommaSeparatedListOutputParser()

    cache = {}
    if not rebuild_cache:
        for idx, row in old_list.iterrows():
            cache[row['category_class']]=row[category_tag]

    # Generate tags
    tag_list = []
    for i, disease in tqdm(enumerate(disease_list), total=len(disease_list), desc="adding tags..."):
        id = id_list[i]
        if id in cache:
            print(f"cache hit for {id}")
            tag_list.append(cache[id])
        else:
            print("no cache hit")
            if not testing or i < limit:
                if (definitions is None) | (synonyms is None):
                    prompt = ChatPromptTemplate.from_messages(
                        [SystemMessage(content=raw_prompt), HumanMessage(content=disease)]
                    )
                    formatted_prompt = prompt.format_messages(disease=disease)
                else:
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            SystemMessage(
                                content=raw_prompt.format(disease=disease, synonym=synonyms[i], definition=definitions[i])
                            )
                        ]
                    )
                    formatted_prompt = prompt.format_messages(disease=disease, synonym=synonyms[i], definition=definitions[i])
                response = model.invoke(formatted_prompt)
                tags = output_parser.parse(response.content)
                tag_list.append(", ".join(tags).lower())
            else:
                tag_list.append("over limit")
    return tag_list

def enrich_disease_list(disease_list: List, params: Dict) -> pd.DataFrame:
    """function to enrich disease list with llm-generated tags.

    Args:
        disease_list: pd.DataFrame - merged disease_list with disease names column that will be used for tag generation
        params: Dict - parameters dictionary specifying tag names, column names, and model params
    Returns
        pd.DataFrame with x new tag columns (where x corresponds to number of tags specified in params)
    """
    for input_type in ["single_input", "multiple_input"]:
        input_params = params[input_type]
        for tag, tag_params in input_params.items():
            # Check if tag is already in disease list
            if tag in disease_list.columns:
                continue
            print(f"Applying tag: '{tag}' to disease list")
            input_col = tag_params["input_params"]["input_col"]
            output_col = tag_params["input_params"]["output_col"]
            raw_prompt = tag_params["input_params"]["prompt"]
            chat_model = ChatOpenAI(model=tag_params["model_params"]['model'])
            # Check whether the tag needs a single or multiple inputs
            if input_type == "single_input":
                disease_list[output_col] = generate_tag(
                    disease_list=disease_list[input_col], raw_prompt=raw_prompt, model=chat_model
                )
            else:
                definition_col = tag_params["input_params"]["definition"]
                synonym_col = tag_params["input_params"]["synonyms"]
                disease_list[output_col] = generate_tag(
                    disease_list=disease_list[input_col],
                    definitions=disease_list[definition_col],
                    synonyms=disease_list[synonym_col],
                    raw_prompt=raw_prompt,
                    model=chat_model
                )
    return disease_list


def enrich_disease_list_single_tag(
    disease_list: pd.DataFrame,
    tag_name: str,
    tag_params: Dict,
    single_input: bool,
    prev_list: pd.DataFrame,
    rebuild_cache: bool
) -> pd.DataFrame:
    """Function to enrich disease list with a single llm-generated tag.

    Args:
        disease_list: pd.DataFrame - disease list with disease names column for tag generation
        tag_name: str - name of the tag to be generated
        tag_params: Dict - parameters dictionary for the specific tag
        input_type: str - either "single_input" or "multiple_input"
    Returns:
        pd.DataFrame with the new tag column added
    """
    # Check if tag is already in disease list
    if tag_name in disease_list.columns:
        return disease_list

    print(f"Applying tag: '{tag_name}' to disease list")
    
    input_col = tag_params["input_params"]["input_col"]
    output_col = tag_params["input_params"]["output_col"]
    raw_prompt = tag_params["input_params"]["prompt"]
    chat_model = ChatOpenAI(model=tag_params["model_params"]['model'])

    # Generate tag based on input type
    if single_input:
        disease_list[output_col] = generate_tag(
            disease_list=disease_list[input_col],
            id_list = disease_list['category_class'],
            raw_prompt=raw_prompt,
            model=chat_model,
            old_list = prev_list,
            rebuild_cache = rebuild_cache,
            category_tag=output_col
        )
    else:  # multiple_input
        definition_col = tag_params["input_params"]["definition"]
        synonym_col = tag_params["input_params"]["synonyms"]
        disease_list[output_col] = generate_tag(
            disease_list=disease_list[input_col],
            id_list = disease_list['category_class'],
            definitions=disease_list[definition_col],
            synonyms=disease_list[synonym_col],
            raw_prompt=raw_prompt,
            model=chat_model,
            old_list = prev_list,
            rebuild_cache = rebuild_cache,
            category_tag=output_col
        )

    return disease_list