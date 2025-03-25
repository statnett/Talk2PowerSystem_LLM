# Talk2PowerSystem Jupyter Notebooks

- Clone https://github.com/Ontotext-AD/nlq-notebooks.
- Follow the steps in the README on how to create an environment.
- Configure the chatbot by providing the GraphDB base url and repository and the LLM setup (Azure endpoint, deployment name, Azure API version, temperature, seed, timeout) in [config.yaml](config.yaml). Do not put the API key in the configuration file! The notebook will prompt you to provide the key and store it in an environment variable.
- Run
```
jupyter notebook Talk2PowerSystem.ipynb
```
