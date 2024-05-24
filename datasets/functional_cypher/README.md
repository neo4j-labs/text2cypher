# Functional_Cypher_Generator

The functional_Cypher section contains code for generating a supervised fine-tuning dataset consisting of question-Cypher query pairs. Each question is a function of node labels, properties, or relationship types along with their properties. While these questions may appear more mechanical, they can effectively complement naturally phrased questions in the fine-tuning datasets.

Our approach employs approximately 100 generating functions. The question-Cypher queries are generated using a Neo4j graph database by extracting its knowledge graph schema along with several node and relationship instances.

The details on our approach can be foud here: [Cypher Generation: The Good, The Bad and The Messy](https://medium.com/towards-data-science/cypher-generation-the-good-the-bad-and-the-messy-4ec119dd72ea).

To facilitate ease of use and transparency, the dataset generation process is provided in a notebook format. To generate the dataset, obtain your Neo4j knowledge graph credentials and follow the steps outlined in the notebook: `SFT_Functional_Data_Builder.ipynb`. Many steps within the notebook are adjustable to cater to specific user needs. Some functionalities rely on modules found in the `utils` directory.
