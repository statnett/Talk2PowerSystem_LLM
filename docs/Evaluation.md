# Evaluation of the Talk to Power System LLM

## Run the evaluation

```bash
conda activate Talk2PowerSystemLLM
export GRAPHDB_PASSWORD=***
export AZURE_OPENAI_API_KEY=***
poetry run evaluation --chat_config_path CHAT_CONFIG_PATH --gsc-path GSC_PATH --results_dir RESULTS_DIR
```

The output will be saved in the specified `RESULTS_DIR`, including:
- `evaluation_per_question_{timestamp}.json`
- `evaluation_summary_{timestamp}.json`

For more details, refer to the [ttyg-evaluation documentation](https://github.com/Ontotext-AD/ttyg-evaluation).
