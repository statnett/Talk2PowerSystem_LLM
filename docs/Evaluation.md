# Evaluation of the Talk to Power System LLM

## Run the evaluation

```bash
cd src/
conda activate Talk2PowerSystemLLM
export GRAPHDB_PASSWORD=***
export AZURE_OPENAI_API_KEY=***
poetry run evaluation --chat_config_path CHAT_CONFIG_PATH --qa-dataset-path QA_DATASET_PATH --results_dir RESULTS_DIR
```

The results will be saved in the specified `RESULTS_DIR` under a sub-folder with name derived from the current date time, and it will include:

- `chat_responses_dev.jsonl` - JSON lines file containing the chat responses on the dev split.
- `evaluation_per_question_dev.json` - Evaluation results per question on the dev split.
- `evaluation_summary_dev.json` - Aggregated evaluation results per question on the dev split.
- `chat_responses_test.jsonl`- JSON lines file containing the chat responses on the test split.
- `evaluation_per_question_test.json` - Evaluation results per question on the test split.
- `evaluation_summary_test.json` - Aggregated evaluation results per question on the test split.

For more details, refer to the [ttyg-evaluation documentation](https://github.com/Ontotext-AD/ttyg-evaluation).
