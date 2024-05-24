"""Functions to extract information from structured_schema"""

from typing import Any, List, Dict, Union, Tuple
import re

from neo4j import time

# Import local modules
from utils.utilities import *

def retrieve_datatypes(jschema: Dict,
                            comp: str) -> List[str]:
    
    """Retrieves the set of datatypes present in the graph.
    INPUTS:
    - jschema - graph schema
    - comp - values node, rel to extract datatypes for the specified graph component
    OUTPUT:
    - list of possible datatypes for the specified graph component"""

    if comp=="node":
        all_node_types = []
        all_nodes = get_nodes_list(jschema)
        for label in all_nodes:
            node_info = jschema['node_props'][label]
            node_types = [el['datatype'] for el in node_info]
            all_node_types = all_node_types + node_types
        return list(set(all_node_types))
    
    elif comp=="rel":
        all_rel_types = set()
        all_rels = jschema["rel_props"]
        #rel_dtypes = set()
        for rel in all_rels.values():
            for prop in rel:
                rel_type = prop.get("datatype")
                if rel_type:
                    all_rel_types.add(rel_type)
        return list(all_rel_types)


#### NODES ####

def get_nodes_list(jschema: Dict
                   ) -> List[str]:
    """Returns the list of node labels in the graph."""
    return list(jschema['node_props'].keys())


def get_node_properties(jschema: Dict,
                        label: str,
                        datatypes: bool=False,
                        datatype: str=""
                        ) -> Any:
    """Function to extract a list of properties for a given node.
    Options to return the datatypes or a properties of specific datatype only."""
   
    node_info = jschema['node_props'][label]
    if datatypes:
        if len(datatype) > 1:
            props = [el['property'] for el in node_info if el['datatype'] == datatype]
        else:
            props = node_info
    else:
        props = [el['property'] for el in node_info]
    return props


def get_nodes_properties_of_datatype(jschema: Dict,
                                     nodes: List[str], 
                                     datatype: str=""
                                     ) -> List[Dict]:
    """Function to extract the properties of given datatype, for a list of nodes."""
    outputs = []
    for node in nodes:
        output = get_node_properties(jschema, node, datatypes=True, datatype=datatype)
        outputs.append({node: output})
        
    # Filter out the nodes that do not have any property of specified type
    return filter_empty_dict_values(outputs)


#### RELATIONSHIPS ####

def extract_relationships_list(jschema: Dict,
                               formatted: bool=False
                               )-> Any:
    """Extracts the list of relationships in one of the following formats:
    formatted=True - each relationship is a string: (:start)-[:type]->(:end)
    formatted=False - each relationship is a dictionary with keys: start, type, end.
    """
    if formatted:
        rels_list=[]
        for el in jschema['relationships']:
            formatted_rels = f"(:{el['start']})-[:{el['type']}]->(:{el['end']})" 
            rels_list.append(formatted_rels)
    else:
        rels_list = jschema['relationships']
    return rels_list  


def get_relationships_with_datatype(jschema: Dict,
                                    datatype: str,
                                    )->List[str]:
        """Returns a list of relationship types that have attributes with specified datatype."""
        sampler = get_relationships_properties_of_datatype(jschema, datatype)
        rels_string = [list(e.keys())[0] for e in sampler]
        return rels_string
        
def get_relationships_properties_of_datatype(jschema: Dict,
                                             datatype: str
                                             ) -> List[Any]:
    """Extracts relationships properties of specified datatype."""
    outputs = []
    for rel in list(jschema['rel_props'].keys()):
        props = jschema['rel_props'][rel]
        selected_props = [el['property'] for el in props if el['datatype'] == datatype]
        if len(selected_props) > 0:
            outputs.append({rel:selected_props})
    return outputs

#### SERIALIZE TEMPORAL DATA FOR SAVING ####

def neo4j_date_to_string(v: str
                         )-> str:
    """Convert neo4j.time.Date to ISO formatted string."""
    """Sample neo4j.time.Date(2023, 10, 25)'"""
    return f"{v.year}-{v.month:02d}-{v.day:02d}"


def neo4j_datetime_to_string(v: str
                             )-> str:
    """Convert neo4j.time.DateTime to ISO formatted string."""
    """Sample neo4j.time.DateTime(2023, 11, 10, 12, 23, 32, 0, tzinfo=<UTC>)"""
    return f"{v.year}-{v.month:02d}-{v.day:02d} T {v.hour:02d}:{v.minute:02d}:{v.second:02d} {v.tzinfo}"


def transform_temporals_in_dict(d: Dict
                                )-> Dict:
    """Transform neo4j.time objects in a dictionary to ISO formatted strings."""
    for key, value in d.items():
        if isinstance(value, time.Date):
            d[key] = neo4j_date_to_string(value)
        elif isinstance(value, time.DateTime):
            d[key] = neo4j_datetime_to_string(value)
    return d


def serialize_nodes_data(entries: List[Dict], 
                        )->List[Dict]:
    """Function to parse the Neo4j.time entries from extracted instances
    for a list of nodes."""
    
    for sublist in entries:
        for rec in sublist:
            rec['Instance']['properties'] = transform_temporals_in_dict( rec['Instance']['properties'])
    return entries


def serialize_relationships_data(entries: List[Dict], 
                                 )->List[Dict]:
    """Function to parse the Neo4j.time entries from extracted instances
    for a list of relationships."""

    for sublist in entries:
        for rec in sublist:
            t = list(rec.keys())
            rec[t[0]] = transform_temporals_in_dict(rec[t[0]])
            rec[t[1]] = transform_temporals_in_dict(rec[t[1]])
            rec[t[2]] = transform_temporals_in_dict(rec[t[2]])
    return entries


#### PARSED INSTANCES ###

def parse_node_instances_datatype(jschema: List[Dict],
                                  nodes_instances: List[Dict],
                                  nodes: List[str], 
                                  datatype: str,
                                  flatten: bool
                                  )->List[Any]:
    """Parse instances of nodes and properties with specified data type.
    Format [[label, property, value], ...]"""

    # Parse date and date_time in extracted instances
    sampler = serialize_nodes_data(nodes_instances)

    # Get the nodes and the properties of specifid datatype
    np_datatype = get_nodes_properties_of_datatype(jschema,nodes, datatype) 

    full_result = []

    for el in np_datatype:
        label = list(el.keys())[0]
        props_label = el[label] 

        result_label = []
        sampler_label = [e for e in sampler if e[0]['Instance']['Label']==label]

        for instance in sampler_label[0]:
            parsed_dict = extract_subdict(instance['Instance']['properties'], props_label) 
            parsed_instance = [[label, key, value] for key, value in parsed_dict.items() if key and value]
            if parsed_instance:
                full_result.append(parsed_instance)
    
    full_result = filter_empty_sublists(full_result)
                
    if flatten:
        return flatten_list(full_result)
    else:
        return full_result
    

def filter_relationships_instances(jschema: Dict,
                                   rels_instances: List[Dict],
                                   datatype_start: str,
                                   datatype_end: str
                                   )-> List[Dict]:
    """Parses a list of relationships. It extracts those properties for both source and target nodes that are of specified data types.
    """

    result = []

    for coll in rels_instances:
        for instance in coll:
            triple = list(instance.keys())
            
            label_start = triple[0][:-6]
            selected_props_start = get_node_properties(jschema, label_start, True, datatype_start)
            selected_start = extract_subdict(instance[triple[0]], selected_props_start)
            
            label_end = triple[2][:-4]
            selected_props_end =  get_node_properties(jschema, label_end, True, datatype_end)
            selected_end = extract_subdict(instance[triple[2]], selected_props_end)
            
            rel = triple[1]

            if selected_start and selected_end:
                result.append([label_start, selected_start, rel, label_end, selected_end])
    return result
    

def filter_relationships_with_props_instances(jschema: Dict,
                                   instances: List[Dict],
                                   datatype_start: str,
                                   datatype_rel: str,
                                   datatype_end: str
                                   )-> List[Dict]:
    """Parses a list of relationships. 
    It extracts those properties for source, relationship and target that are of specified data types.
    """
    
    result = []

    for coll in instances:
        for instance in coll:
            triple = list(instance.keys())
            
            # Remove the _start from the label 
            label_start = triple[0][:-6]
            # Retrieve node properties with specified datatype
            selected_props_start = get_node_properties(jschema, label_start, True, datatype_start)
            # Extract the corresponding subdictionary
            selected_start = extract_subdict(instance[triple[0]], selected_props_start)

            # Retrieve the relationship type
            rel = triple[1]
            # Extract all properties of given type for all relationships
            selected_props_rel = get_relationships_properties_of_datatype(jschema, datatype_rel)
            extracted = [d[rel] for d in selected_props_rel if rel in d]
            if len(extracted) > 0:
                selected_rel = extract_subdict(instance[triple[1]], extracted[0])
            else:
                continue
        
            # Remove _end from label
            label_end = triple[2][:-4]
            # Retrieve node properties with specifid datatype
            selected_props_end =  get_node_properties(jschema, label_end, True, datatype_end)
            # Extract the correspnding subdictionary
            selected_end = extract_subdict(instance[triple[2]], selected_props_end)

            if selected_start and selected_end and selected_rel:
                result.append([
                    label_start, selected_start, 
                    rel, selected_rel, 
                    label_end, selected_end
                    ])
    return result

    
def retrieve_instances_with_relationships_props(relationship_instances: List[Any]
                                                ) -> List[Any]:
    """Returns the instances where the relationship has attributes."""

    instances_with_rel_props = []

    for rel in relationship_instances:
        filtered_instances = filter_dicts_list(rel)
        instances_with_rel_props.append(filtered_instances)

    # Filter the empty sublist
    instances_with_rel_props = filter_empty_sublists(instances_with_rel_props)

    return instances_with_rel_props

#### EXTRACT LOCAL GRAPH INFO ####

def build_minimal_subschema(jschema: Dict,
                    nodes_info: List[Tuple[str, Dict[str, str]]],
                    relationships_info: List[Tuple[str, str, str, Dict[str, str]]],
                    include_node_props: bool=True,
                    include_rel_props: bool=False,
                    include_types: bool = False,
                    ) -> str:
    """
    Constructs a subschema description from given nodes and relationships, with an option to include data types for properties.

    Args:
    - nodes: A list of tuples, where each tuple represents a node label and a dictionary of the node's properties with their data types.
    - relationships: A list of tuples, each representing a relationship. The tuple contains the start node label, relationship type, end node label, and a dictionary of the relationship's properties with their data types.
    - include_types: A boolean indicating whether to include data types in the property descriptions.

    Returns:
    - A string describing the node labels, their properties (optionally with data types), and relationships with their properties (optionally with data types), formatted for easy reading and suitable for various uses including fine-tuning a language model for Cypher query generation.
    """

    def extract_specific_props(comp_props, comp_info):
        result = []

        # Iterate through comp_info to handle specified labels and properties
        for item in comp_info:
            label = item[0]
            prop = item[1] if len(item) > 1 else None

            # If no specific property is provided, just add the label
            if prop is None:
                result.append([label, {}])
            else:
                # Find and add the specified property if it exists
                found_prop = False
                for prop_details in comp_props.get(label, []):
                    if prop_details['property'] == prop:
                        result.append([label, {prop: prop_details['datatype']}])
                        found_prop = True
                        break  # Found the property, no need to keep searching
                if not found_prop:
                    # If the property is specified but not found, include the label without properties
                    result.append([label, {}])

        return result

    local_nodes = extract_specific_props(jschema["node_props"], nodes_info)
    local_relationships = extract_specific_props(jschema["rel_props"], relationships_info)

    rels_list = [item[0] for item in local_relationships]
    def extract_specific_relations(rel_list, rels):
        specific_rels=[]
        for rel in rels:
            specific_rel = [r for r in jschema["relationships"] if r["type"]==rel][0]
            specific_rels.append(specific_rel)

        return specific_rels

    relevant_relations = extract_specific_relations(jschema["relationships"], rels_list)

    # Helper function to format node properties
    def format_props(props: Dict[str, str],
                     ) -> str:
        if include_types:
            return ", ".join(f"{k}: {v}" for k, v in props.items())
        else:
            return ", ".join(f"{k}" for k in props.keys())


    # Building relationships
    relations= [f"{{'start': {e['start']}, 'type': {e['type']}, 'end': {e['end']} }}" for e in relevant_relations]
    # Building relationship descriptions

    # Combine all parts
    newline = "\n"

    if include_node_props:
        # Building node descriptions
        node_descriptions = [f"{label} {{{format_props(props)}}}" for label, props in local_nodes]
        
    else:
        node_descriptions = [label for label, _ in local_nodes]
        

    if include_rel_props:
        relationship_descriptions= [f"{label} {{{format_props(props)}}}" for label, props in local_relationships]

        subschema = f"""
        Relevant node labels and their properties {'(with datatypes)' if include_types else ''} are:\n{newline.join(node_descriptions)}\n
Relevant relationships are:\n{newline.join(relations)}\n

Relevant relationship properties {'(with datatypes)' if include_types else ''} are:\n{newline.join(relationship_descriptions)}\n
    """
    else:
        subschema = f"""
        Relevant node labels and their properties {'(with datatypes)' if include_types else ''} are:\n{newline.join(node_descriptions)}\n
Relevant relationships are:\n{newline.join(relations)}\n
  """

    return subschema.strip()



   

    




  

    
 
        
  

   

    

    



        
