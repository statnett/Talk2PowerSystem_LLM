# Evaluation of the Talk to Power System LLM

## Prerequisites

- Before running the evaluation make sure that the chat config points to the `cim-subset-pretty.ttl`, which corresponds to the data loaded in GraphDB.
The file lives in [the Talk2PowerSystem repository](https://github.com/statnett/Talk2PowerSystem/blob/main/data/subset-ontology/cim-subset-pretty-ontology.ttl).
- Make sure the Q&A dataset is up-to-date. If there is a new version of the dataset, the data loaded in the GraphDB repository must be updated.
To serialize the Q&A dataset as rdf (train and dev split) execute the following steps:
```bash
conda activate Talk2PowerSystemLLM
poetry run qa_dataset2rdf --qa-dataset-path QA_DATASET_PATH --output_folder OUTPUT_FOLDER
```

The result is a trig file named `qa_dataset.trig` in `OUTPUT_FOLDER`, which must be imported manually into the GraphDB repository.

## Run the evaluation

```bash
conda activate Talk2PowerSystemLLM
export LLM_API_KEY=***
poetry run evaluation --chat_config_path FULL_PATH_TO_CHAT_CONFIG --qa-dataset-path QA_DATASET_PATH --results_dir RESULTS_DIR --n_templates MAX_NUMBER_OF_TEMPLATES_FOR_DEV_AND_TEST
```

where FULL_PATH_TO_CHAT_CONFIG_PATH is the full path to the [dev+retrieval.yaml](../config/dev+retrieval.yaml).
If you want to run the evaluation without the N-Shot tool, use the [dev.yaml](../config/dev.yaml).

The results will be saved in the specified `RESULTS_DIR` under a sub-folder with name derived from the current date time, and it will include:

- `chat_responses_dev.jsonl` - JSON lines file containing the chat responses on the dev split.
- `evaluation_per_question_dev.yaml` - Evaluation results per question on the dev split.
- `evaluation_summary_dev.yaml` - Aggregated evaluation results per question on the dev split.
- `chat_responses_test.jsonl`- JSON lines file containing the chat responses on the test split.
- `evaluation_per_question_test.yaml` - Evaluation results per question on the test split.
- `evaluation_summary_test.yaml` - Aggregated evaluation results per question on the test split.

For more details, refer to the [graphrag-eval documentation](https://github.com/Ontotext-AD/graphrag-eval).
