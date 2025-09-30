# Benchmark GraphDB TTYG

Steps to run the evaluation against the GraphDB TTYG agent:
1. Create the agent from GraphDB Workbench
1. Set GraphDB password as environment variable:
```bash
export GRAPHDB_PASSWORD=***
```
You must escape any `$` signs in the password with `\`!
1. Obtain the agent id. Sample command:
```bash
curl -H "Authorization: Basic $(printf "%s" "<username>:${GRAPHDB_PASSWORD}" | base64)" <graphdb-base-url>/rest/chat/agents
```
In the json output find your agent by name and copy its uuid.
1. Create GraphDB config file. Sample content:
```yaml
base_url: "<graphdb-base-url>"
repository_id: "repository-id"
connect_timeout: <connect-timeout>
read_timeout: <read-timeout>
sparql_timeout: <sparql-timeout>
ttyg_agent_id: "<agent-id>"
username: "<username>"
```
1. Run the evaluation:

```bash
conda activate Talk2PowerSystemLLM
poetry run benchmark_graphdb_ttyg --path_to_graphdb_config_yaml FULL_PATH_TO_GRAPHDB_CONFIG --qa-dataset-path FULL_PATH_TO_QA_DATASET --results_dir RESULTS_DIR --n_templates MAX_NUMBER_OF_TEMPLATES_FOR_DEV_AND_TEST
```

The results will be saved in the specified `RESULTS_DIR` under a sub-folder with name derived from the current date time, and it will include:

- `gdb_responses_dev.txt` - File containing the agent responses on the dev split.
- `evaluation_per_question_dev.yaml` - Evaluation results per question on the dev split.
- `evaluation_summary_dev.yaml` - Aggregated evaluation results per question on the dev split.
- `gdb_responses_test.txt`- File containing the agent responses on the test split.
- `evaluation_per_question_test.yaml` - Evaluation results per question on the test split.
- `evaluation_summary_test.yaml` - Aggregated evaluation results per question on the test split.

For more details, refer to the [graphrag-eval documentation](https://github.com/Ontotext-AD/graphrag-eval).
