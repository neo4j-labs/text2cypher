# Finetuning Codestral using Unsloth

## Using instruct prompt template

* Filename: `codestral_text2cypher_instruct.ipynb`
* Contributed by: [Tomaz Bratanic](https://github.com/tomasonjo)
* Dataset: https://huggingface.co/datasets/tomasonjo/text2cypher-gpt4o-clean
* HuggingFace model: https://huggingface.co/collections/tomasonjo/codestral-text2cypher-6666636c113312a4a955e8af
* Ollama model: https://ollama.com/tomasonjo/codestral-text2cypher

This notebook uses instruct prompt template to finetune Codestral to construct Cypher statements on 16 different graph databases available on demo server.

You can load and use the model in LangChain or LlamaIndex.
First load the model using Ollama

```bash
ollama pull tomasonjo/codestral-text2cypher
```

### LangChain

Now you can use the following code to generate Cypher statements with LangChain:

```python
pip install langchain langchain-community neo4j
from langchain_community.graphs import Neo4jGraph
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

DEMO_URL = "neo4j+s://demo.neo4jlabs.com"
DATABASE = "recommendations"

graph = Neo4jGraph(
    url=DEMO_URL,
    database=DATABASE,
    username=DATABASE,
    password=DATABASE,
    enhanced_schema=True,
    sanitize=True,
)
llm = ChatOllama(model="tomasonjo/codestral-text2cypher")
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given an input question, convert it to a Cypher query. No pre-amble.",
        ),
        (
            "human",
            (
                "Based on the Neo4j graph schema below, write a Cypher query that would answer the user's question: "
                "\n{schema} \nQuestion: {question} \nCypher query:"
            ),
        ),
    ]
)
chain = prompt | llm

question = "How many movies did Tom Hanks play in?"
response = chain.invoke({"question": question, "schema": graph.schema})
print(response.content)
```

### LlamaIndex

Now you can use the following code to generate Cypher statements with LlamaIndex:

```python
pip install llama-index llama-index-embeddings-openai llama-index-graph-stores-neo4j
from llama_index.graph_stores.neo4j import Neo4jPGStore
from llama_index.llms.openai import OpenAI
from llama_index.core.retrievers import TextToCypherRetriever
from llama_index.llms.ollama import Ollama
from llama_index.core import PropertyGraphIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.indices.property_graph import (
    ImplicitPathExtractor,
    SimpleLLMPathExtractor,
)
from llama_index.core.query_engine import RetrieverQueryEngine

DEMO_URL = "neo4j+s://demo.neo4jlabs.com"
DATABASE = "recommendations"
graph_store = Neo4jPGStore(
    username=DATABASE,
    password=DATABASE,
    database=DATABASE,
    url=DEMO_URL,
)
llm = Ollama(model="tomasonjo/codestral-text2cypher", request_timeout=60.0)
cypher_retriever = TextToCypherRetriever(
    graph_store,
    llm=llm
)
# run this if index is already loaded
index = PropertyGraphIndex.from_existing(
    graph_store,
    embed_model=OpenAIEmbedding(model_name="text-embedding-3-small"),
    kg_extractors=[
        ImplicitPathExtractor(),
        SimpleLLMPathExtractor(
            llm=OpenAI(model="gpt-3.5-turbo", temperature=0.3),
            num_workers=4,
            max_paths_per_chunk=10,
        ),
    ],
    show_progress=True,
)
query_engine = RetrieverQueryEngine.from_args(
    index.as_retriever(sub_retrievers=[cypher_retriever]), llm=llm
)

response = query_engine.query("Who played in Pulp Fiction?")
print(str(response))
```