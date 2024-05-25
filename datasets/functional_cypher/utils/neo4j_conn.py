"""Graph database connector and query parsers."""

from typing import Any, Dict, List
import pandas as pd

import neo4j
from neo4j.exceptions import CypherSyntaxError
from neo4j import GraphDatabase

# Import local modules
from utils.utilities import *

class Neo4jGraph:
    """Neo4j wrapper for graph operations."""

    def __init__(
        self, 
        url: str, 
        username: str, 
        password: str, 
        database: str,
        ) -> None:
        
        """Create a new Neo4j graph wrapper instance."""
      
        self._driver = neo4j.GraphDatabase.driver(url,
                                                   auth=(username, password),
                                                   )
        # Set the database name                                           
        self._database = database
        
        self.schema = ""

        # Verify connection
        try:
            self._driver.verify_connectivity()
        except neo4j.exceptions.ServiceUnavailable:
            raise ValueError(
                "Could not connect to Neo4j database. "
                "Please ensure that the url is correct."
            )
        except neo4j.exceptions.AuthError:
            raise ValueError(
                "Could not connect to Neo4j database. "
                "Please ensure that the username and password are correct"
            )
        

    def close(self):
        """Closes the Neo4j connection."""
        if self._driver is not None:
            self._driver.close()
    
    
    def query(self, 
              cypher_query: str, 
              params: dict = {},
              db=None
              ) -> List[Dict[str, Any]]:
        """Query Neo4j database. Outputs a list of dictionaries."""

        target_db = self._database if db is None else db

        with self._driver.session(database=target_db) as session:
            try:
                data = session.run(cypher_query, params)
                return [r.data() for r in data]
            except CypherSyntaxError as e:
                raise ValueError(
                    "Generated Cypher Statement is not valid\n" f"{e}") 

    