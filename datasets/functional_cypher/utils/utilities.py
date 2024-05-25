"""Collection of basic Python helper functions"""

import json
from typing import Any, List, Dict, Callable
import pickle
import itertools
from itertools import product, combinations
import random
from collections import defaultdict

### File handlers ###

def write_json(an_object: List[Any], file_path: str ) -> None:
    """Writes a Python object to a json file."""
    with open(file_path, "w") as fp:
        json.dump(an_object, fp)


def read_json(file_path: str) -> Any:
    """Reads a json file to the Python object it contains."""
    with open(file_path, 'rb') as fp:
        data=json.load(fp)
        return data
    

def write_pkl(an_object: Any, file_path: str) -> None:
    """Writes a Python object to a pickle file."""
    with open(file_path, 'wb') as f:
        pickle.dump(an_object, f)


def read_pkl(an_object: Any, file_path: str) -> Any:
    """Reads a pickle file."""
    with open(file_path, 'rb') as f:
        an_object = pickle.load(f)
        return an_object
    

### Lists and dictionaries utilities ###

def extract_subdict(my_dict: Dict, 
                    keys_to_extract: List[str]
                    )-> Dict:
    """Extracts a subdictionary of a dictionary."""
    return {key: my_dict[key] for key in keys_to_extract if key in my_dict}

    
def filter_empty_dict_values(lst: List[Dict]
                             )-> List[Dict]:
    """Filter out dictionaries with empty list values."""
    return [d for d in lst if any(d.values())]
    
def filter_dicts_list(lst: List[Dict]
                             )-> List[Dict]:
    """Filter out dictionaries with at least one empty value."""
    return [d for d in lst if all(d.values())]


def filter_empty_sublists(lst: List
                          )->List:
    """Filters empty sublists from a list of lists."""
    return [sublist for sublist in lst if any(sublist)]


def flatten_list(nested_list: List[List]) -> List[str]:
    """Flattens a nested Python list."""
    flat_list = []
    for sublist in nested_list:
        flat_list.extend(sublist)
    return flat_list


### Helpers for building samples data ###

def build_node_sampler(nlist: List[List], 
                       prompter: Callable[..., Dict],
                       allow_repeats: bool
                       ) -> List[Dict]:
    """
    Build the samples for queries that involve one node label with attribute, values.

    Input:
    - nlist: [[label, property, value],...] extracted from parsed node instances
    - prompter: prompt builder function
    - allow_repeats: if repeated entries with the same label, property pair 
    but different values are to be included or not

    Output:
    - fine-tuning data
    """

    # Filter the node instances for node, property duplicates
    seen = set()
    filtered = [e for e in nlist if (e[0], e[1]) not in seen and not seen.add((e[0], e[1]))]

    sampler = []

    if allow_repeats:
        entries = nlist
    else:
        entries = filtered

    for entry in entries:
        temp_dict = prompter(entry[0], entry[1], entry[2])
        sampler.append(temp_dict)

    return sampler
    

def get_property_pairs(nlist_1: List[List],
                       nlist_2: List[List],
                       same_node: bool,
                       allow_repeats: bool
                       ) -> List[Dict]:
    """
    Builds queries samples that involve pairs of nodes with their properties
    and associated values.

    Input:
    - nlist_1: [[label_1, property_1, value_1],...] extracted from node instances
    - nlist_2: [[label_2, property_2, value_2],...] extracted from node instances
    - same_node: if label_1, label_2 can be the same or not
    - allow_repeats: if repeated entries with the same label, property pair 
    and different values are to be included or not

    Output:
    - [label_1, prop_1, val_1, label_2, prop_2, val_2] if distinct labels
    - [label_1, prop_1, val_1, prop_2, val_2] if the same label 
    """

    prod = list(product(nlist_1, nlist_2))

    if same_node:
        output = [e for e in prod if e[0][0] == e[1][0]]
    else:
        output = prod


    seen_pairs = set()
    filtered = [e for e in output if (e[0][0], e[0][1], e[1][0], e[1][1]) \
    not in seen_pairs and not \
    seen_pairs.add((e[0][0],e[0][1], e[1][0], e[1][1]))]

    if allow_repeats:
        output = output
    else:
        output = filtered

    return output
    

def build_nodes_property_pairs_sampler(nlist_1: List[List],
                                       nlist_2: List[List],
                                       prompter: Callable[..., Dict],
                                       same_node: bool,
                                       allow_repeats: bool,
                                       )-> List[Dict]:
    
    """
    Builds sampler for pairs of nodes, property, values with or without repeats.
    
    Input:
    - nlist_1: [[label_1, property_1, value_1],...] extracted from node instances
    - nlist_2: [[label_2, property_2, value_2],...] extracted from node instances
    - prompter: prompt builder function
    - same_node: if label_1, label_2 can be the same or not
    - allow_repeats: if repeated entries with the same label, property pair 
    but different values are to be included or not

    Output:
    - fine-tuning data

    """

    output = get_property_pairs(nlist_1, nlist_2,
                                same_node=same_node,
                                allow_repeats=allow_repeats)

    sampler = []

    for e in output:
        if same_node:
            temp_dict = prompter(e[0][0], e[0][1], e[0][2], e[1][1], e[1][2])
        else:
            temp_dict = prompter(e[0][0], e[0][1], e[0][2], e[1][0], e[1][1], e[1][2])

        sampler.append(temp_dict)

    return sampler
    
    
def build_nodes_pairs(nodes: List[str],
                      prompter: Callable[..., Dict],
                      allow_repeats: bool,
                      ) -> List[Dict]:
    """
    Builder for queries that involve two node labels.

    Input:
    - nodes: list of node labels
    - prompter: prompt builder function
    - allow_repeats: if repeated entries with the same label, property pair 
    but different values are to be included or not

    Output:
    - fine-tuning data
    """

    output = list(product(nodes, nodes))

    sampler = []

    for e in output:
        temp_dict = prompter(e[0], e[1])

        sampler.append(temp_dict)

    return sampler
    

def build_relationships_samples(rel_list: List[Any],
                                prompter: Callable[..., Dict],
                                allow_repeats: bool) -> List[Dict]:
    
    """
    Builds relationships based queries, with or without repeats.
    The start and end nodes properties can be selected using their datatypes.
    
    Input:
    - rel_list: [start_label, [{property: val}, ...], relationship_type, end_label, 
    [{property_: value},...] are extracted from relationship instances
    - prompter: prompt builder function
    - allow_repeats: if repeated entries with the same start node, relationship type, end node 
    are to be included or not

    Output:
    - fine-tuning data

    """
    
     # Filter the instances for node, property duplicates
    seen = set()
    filtered = [e for e in rel_list if (e[0], e[2], e[3]) not in seen and not seen.add((e[0], e[2], e[3]))]


    if allow_repeats:
        rel_list= rel_list
    else:
        rel_list = filtered

    sampler = []

    for e in rel_list:
        for k, v in e[1].items():
            for kk, vv in e[4].items():
                temp_dict = prompter(e[0], k, v, e[2], e[3], kk, vv)
                sampler.append(temp_dict)


    return sampler
    

def build_relationships_props_samples(rel_list: List[Any],
                                prompter: Callable[..., Dict],
                                allow_repeats: bool) -> List[Dict]:
    
    """
    Builds relationships with attributes based queries, with or without repeats.
    The start and end nodes properties as well as the relationship properties can be selected using their datatypes.
    
    Input:
    - rel_list: [start_label, {property: val, prop: val}, relationship_type , {property: val, property: val}, end_label, {property_: value, ...}] 
    are extracted from relationship instances
    - prompter: prompt builder function
    - allow_repeats: if repeated entries with the same start node, relationship type, end node are to be included or not

    Output:
    - list of dictionaries with keys: Prompt, Question, Schema, Cypher
    """
    
    # Filter the instances for node, property duplicates
    seen = set()
    filtered = [e for e in rel_list if (e[0], e[2], e[4]) not in seen and not seen.add((e[0], e[2], e[4]))]


    if allow_repeats:
        rel_list= rel_list
    else:
        rel_list = filtered

    sampler = []

    for e in rel_list:
        for k, v in e[1].items():
            for kk, vv in e[3].items():
                for kkk, vvv in e[5].items():
                    temp_dict = prompter(e[0], k, v, e[2], kk, vv, e[4], kkk, vvv)
                    sampler.append(temp_dict)

    return sampler

    

def collect_samples(sampler: List[Dict], 
                    sample_max: int) -> List[Dict]:
    
    """
    Function to select a specified number of samples of each type.
    
    Input:
    - sampler: list of dictionaries with keys: Prompt, Question, Schema, Cypher
    - sample_max: max number of samples of each type

    Output:
    - list of dictionaries with keys: Prompt, Question, Schema, Cypher
    """
    
    num_samples = len(sampler)

    # Ensure sample_max is not greater than the number of available samples
    if num_samples <= sample_max:
        return sampler

    # Only sample if there are more than M samples
    else:
        return random.sample(sampler, sample_max)
        



