
"""Functions to extract specific KG information and data using Cypher"""

from typing import Any, List, Iterable
import neo4j

# Import local modules
from utils.utilities import *
from utils.neo4j_conn import Neo4jGraph

#### Queries ####

node_properties_query = """
    CALL apoc.meta.data()
    YIELD label, other, elementType, type, property
    WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
    WITH label AS nodeLabels, collect({property:property, datatype:type}) AS properties
    RETURN {label: nodeLabels, properties: properties} AS output
    """
    
rel_query = """
    CALL apoc.meta.data()
    YIELD label, other, elementType, type, property
    WHERE type = "RELATIONSHIP" AND elementType = "node"
    UNWIND other AS other_node
    RETURN {start: label, type: property, end: toString(other_node)} AS output
    """

rel_properties_query = """
    CALL apoc.meta.data()
    YIELD label, other, elementType, type, property
    WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
    WITH label AS nodeLabels, collect({property:property, datatype:type}) AS properties
    RETURN {type: nodeLabels, properties: properties} AS output
    """

class Neo4jSchema(Neo4jGraph):
    """Neo4j wrapper for graph operations."""

    def __init__(
        self, 
        url: str, 
        username: str, 
        password: str, 
        database: str,
        ) -> None:
        """Create a Neo4j graph wrapper instance and extract schema information."""

        self.conn = Neo4jGraph(url, username, password, database)
        self.schema: str = ""
        self.structured_schema: Dict[str, Any] = {}

        try:
            self.build_schema()
        except neo4j.exceptions.ClientError:
            raise ValueError(
                "Could not use APOC procedures. "
                "Please ensure the APOC plugin is installed in Neo4j and that "
                "'apoc.meta.data()' is allowed in Neo4j configuration "
            )
    
    #### Schema Utilities ####

    @property
    def get_schema(self) -> str:
        """Returns the schema as a string."""
        return self.schema

    @property
    def get_structured_schema(self) -> Dict[str, Any]:
        """Returns the schema as a json object."""
        return self.structured_schema

    def build_schema(self) -> None:
        """Build KG schema as a string or as a json object."""

        node_properties = [el["output"] for el in self.conn.query(node_properties_query)]
        rel_properties = [el["output"] for el in self.conn.query(rel_properties_query)]
        relationships = [el["output"] for el in self.conn.query(rel_query)]
    
        self.structured_schema = {
            "node_props": {el["label"]: el["properties"] for el in node_properties},
            "rel_props": {el["type"]: el["properties"] for el in rel_properties},
            "relationships": relationships,
            }

        # Format node properties
        formatted_node_props = []
        for el in node_properties:
            props_str = ", ".join(
                #[f"{prop['property']}: {prop['datatype']}" for prop in el["properties"]]
                [f"{prop['property']}" for prop in el["properties"]]
            )
            formatted_node_props.append(f"{el['label']} {{{props_str}}}")

        # Format relationship properties
        formatted_rel_props = []
        for el in rel_properties:
            props_str = ", ".join(
                #[f"{prop['property']}: {prop['datatype']}" for prop in el["properties"]]
                [f"{prop['property']}" for prop in el["properties"]]
            )
            formatted_rel_props.append(f"{el['type']} {{{props_str}}}")

        # Format relationships
        formatted_rels = [
            f"(:{el['start']})-[:{el['type']}]->(:{el['end']})" for el in relationships
        ]
    
        self.schema = "\n".join(
            [
                "Node properties are the following:",
                ",".join(formatted_node_props),
                #"Relationship properties are the following:",
                #",".join(formatted_rel_props),
                "The relationships are the following:",
                ",".join(formatted_rels),
            ]
        )


    #### Instances Utilities ####
    
    def extract_node_instances(self, 
                            selected_labels: List[str], 
                            n: int) -> List[Any]:
        """
        Function to extract node instances: attributes & values."""
        extracted = []
        for label in selected_labels:
            query_nodes = f"""MATCH (p:{label}) 
                            WITH p LIMIT {n}
                            RETURN {{Label: '{label}', properties: properties(p)}} AS Instance
                            """
            
            data = self.conn.query(query_nodes)
            extracted.append(data)

        return extracted
    
        
    def extract_relationship_instances(self,
                                       rel: Dict,
                                       n: int,
                                       ) -> List[Any]:
        """
        Function to extract instances for a given relationship, written as a triple.
        The data includes properties for both nodes and relationship (if any).
        """
        extracted = []
        query_rels = f"""MATCH (a:{rel['start']})-[r:{rel['type']}]->(b:{rel['end']}) 
                        RETURN a AS {rel['start']}_Start, properties(r) AS {rel['type']}, b AS {rel['end']}_End   
                        LIMIT {n} """
        
        data = self.conn.query(query_rels)
        return data 
    
    
    def extract_multiple_relationships_instances( self,
                            rtriples: List[Any], 
                            n: int,
                            ) -> List[Any]:
        """Extracts n instances of each from a relationships list."""
        extracted = []
        for rtriple in rtriples:
            temp_list = self.extract_relationship_instances(rtriple, n)
            extracted.append(temp_list)
        return extracted

   
        
  

   

    

    



        
