# Run Talk to Power System LLM with N-Shot Tool

## Serialize the Q&A Dataset as RDF

The train and dev split of the dataset can be serialized as rdf with the following steps:

```bash
cd src/
conda activate Talk2PowerSystemLLM
poetry run qa_dataset2rdf --qa-dataset-path QA_DATASET_PATH --output_folder ../config/n_shot_tool/
```

The result is a turtle file named `qa_dataset.ttl` in the directory `/config/n_shot_tool/`.

## Load the RDF in GraphDB and index it in a vector store

- Configure the embeddings model in the `docker-compose.yaml`. 
You can refer to [the Embeddings API documentation](https://gitlab.ontotext.com/sol/nlp/ontotext-embeddings-api/-/tree/main/app?ref_type=heads#embeddings).
- Start the environment (GraphDB, Weaviate, Embeddings API, Retrieval Plugin API) with:
```bash
cd config/n_shot_tool/
./start.sh
```
The `qa_dataset.ttl` is automatically loaded into the repository.
- Create a Retrieval Connector: Open GraphDB Workbench `http://localhost:7200/sparql` and use the query from `config/n_shot_tool/connector.rq`.
