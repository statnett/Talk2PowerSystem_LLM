# Talk to the Power System Chatbot LLM Service Helm Charts

Helm chart for deploying Talk to the Power System Chatbot LLM Service.

## Quick start

### Prerequisite

- Create a secret for the Redis password

```bash
kubectl --namespace t2ps-chatbot create secret generic redis-secret-properties \
        --from-literal=redis-password=XXXXXXX
```

- Create a secret for the Chatbot LLM service, which holds passwords of external services  
  [*some of the properties can be omitted, when not used*]

```bash
kubectl --namespace t2ps-chatbot create secret generic t2ps-chatbot-llm-secret-properties \
        --from-literal=GRAPHDB_PASSWORD=XXXXXXX \
        --from-literal=REDIS_USERNAME=XXXXXXX \
        --from-literal=REDIS_PASSWORD=XXXXXXX \
        --from-literal=LLM_API_KEY=XXXXXXX \
```

### Run

To run the chart:

```bash
helm upgrade --install --create-namespace --namespace t2ps-chatbot t2ps-chatbot-llm .
```

## Configurations

See [values.yaml](values.yaml).

Note the `configuration` section, which exposes the essential properties required for the application and its resources.
It provides a way to supply application environment variables, adjust the configurations for the agent(s), secrets for
connection to external services and applications.

## Uninstalling

```bash
helm uninstall --namespace t2ps-chatbot t2ps-chatbot-llm
```
