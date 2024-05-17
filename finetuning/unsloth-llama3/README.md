# Finetuning Llama3 using Unsloth

We have two notebooks here:

## Using simple prompt template

* Filename: `llama3_text2cypher_simple.ipynb`
* Contributed by: [Geraldus Wilsen](https://github.com/projectwilsen/)
* Dataset: synthetic_gpt4turbo_demodbs
* Originally published: https://github.com/projectwilsen/KnowledgeGraphLLM

This notebook uses simple prompt completion template to finetune Llama3 to construct Cypher statements on a single database (recommendations).

For more information, you could watch this video tutorial: https://www.youtube.com/watch?v=7VU-xWJ39ng

## Using chat prompt template

* Filename: `llama3_text2cypher_chat.ipynb`
* Contributed by: [Tomaz Bratanic](https://github.com/tomasonjo)
* Dataset: synthetic_gpt4o_demodbs
* HuggingFace model: https://huggingface.co/tomasonjo/text2cypher-demo-16bit
* Ollama model: https://ollama.com/tomasonjo/llama3-text2cypher-demo

This notebook uses chat prompt template (system,user,assistant) to finetune Llama3 to construct Cypher statements on 16 different graph databases available on demo server.

You can load use it in LangChain using the following code.
First load the model using Ollama and install dependencies.

```bash
ollama pull tomasonjo/llama3-text2cypher-demo
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