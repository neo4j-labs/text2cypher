# Synthetic dataset created with GPT-4-Turbo

Synthetic dataset of text2cypher over 16 different graph schemas.
Both questions and cypher queries were generated using GPT-4-turbo.
The demo database is available at:

```
URI: neo4j+s://demo.neo4jlabs.com
username: name of the database, for example 'movies'
password: name of the database, for example 'movies'
database: name of the database, for example 'movies'
```

Notebooks:

* generate_text2cypher_questions.ipynb: Generate questions and prepare input for OpenAI batch processing job
* process_batch_output.ipynb: Process batch process output and validate the generate Cypher statements by examining if they return any values, have syntax errors, or do queries timeout.