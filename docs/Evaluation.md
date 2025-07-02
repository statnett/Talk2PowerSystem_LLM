# Evaluation of the Talk to Power System LLM

## Run the evaluation

```bash
conda activate Talk2PowerSystemLLM
export GRAPHDB_PASSWORD=***
export LLM_API_KEY=***
poetry run evaluation --chat_config_path FULL_PATH_TO_CHAT_CONFIG --qa-dataset-path QA_DATASET_PATH --results_dir RESULTS_DIR
```

The results will be saved in the specified `RESULTS_DIR` under a sub-folder with name derived from the current date time, and it will include:

- `chat_responses_dev.jsonl` - JSON lines file containing the chat responses on the dev split.
- `evaluation_per_question_dev.json` - Evaluation results per question on the dev split.
- `evaluation_summary_dev.json` - Aggregated evaluation results per question on the dev split.
- `chat_responses_test.jsonl`- JSON lines file containing the chat responses on the test split.
- `evaluation_per_question_test.json` - Evaluation results per question on the test split.
- `evaluation_summary_test.json` - Aggregated evaluation results per question on the test split.

For more details, refer to the [qa-eval documentation](https://github.com/Ontotext-AD/qa-eval).

## Run the evaluation with the N-Shot Tool

### Serialize the Q&A Dataset as RDF

The train and dev split of the dataset can be serialized as rdf with the following steps:

```bash
conda activate Talk2PowerSystemLLM
poetry run qa_dataset2rdf --qa-dataset-path QA_DATASET_PATH --output_folder config/n_shot_tool/
```

The result is a turtle file named `qa_dataset.ttl` in the directory `config/n_shot_tool/`.

### Load the RDF in GraphDB and index it in a vector store

- Configure the embeddings model in the `config/n_shot_tool/docker-compose.yaml`. 
You can refer to [the Embeddings API documentation](https://gitlab.ontotext.com/sol/nlp/ontotext-embeddings-api/-/tree/main/app?ref_type=heads#embeddings).
- Start the environment (GraphDB, Weaviate, Embeddings API, Retrieval Plugin API) with:
```bash
cd config/n_shot_tool/
./start.sh
```
The `qa_dataset.ttl` is automatically loaded into the repository.
- Create a Retrieval Connector: Open GraphDB Workbench `http://localhost:7200/sparql` and use the query from `config/n_shot_tool/connector.rq`.

### Configure and run

- Run the evaluation with
```bash
export GRAPHDB_PASSWORD=***
export LLM_API_KEY=***
poetry run evaluation --chat_config_path FULL_PATH_TO_CHAT_CONFIG --qa-dataset-path QA_DATASET_PATH --results_dir RESULTS_DIR
```

where FULL_PATH_TO_CHAT_CONFIG_PATH is the full path to the [retrieval.yaml](../config/retrieval.yaml)
