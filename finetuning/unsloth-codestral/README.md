# Finetuning Codestral using Unsloth

## Using instruct prompt template

* Filename: `codestral_text2cypher_instruct.ipynb`
* Contributed by: [Tomaz Bratanic](https://github.com/tomasonjo)
* Dataset: https://huggingface.co/datasets/tomasonjo/text2cypher-gpt4o-clean
* HuggingFace model: https://huggingface.co/collections/tomasonjo/codestral-text2cypher-6666636c113312a4a955e8af
* Ollama model: https://ollama.com/tomasonjo/codestral-text2cypher

This notebook uses instruct prompt template to finetune Codestral to construct Cypher statements on 16 different graph databases available on demo server.

You can load use it in LangChain using the following code.
First load the model using Ollama and install dependencies.

```bash
ollama pull tomasonjo/codestral-text2cypher
pip install langchain langchain-community neo4j
```

Now you can use the following code to generate Cypher statements with LangChain:

```python
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
llm = ChatOllama(model="tomasonjo/llama3-text2cypher-demo")
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