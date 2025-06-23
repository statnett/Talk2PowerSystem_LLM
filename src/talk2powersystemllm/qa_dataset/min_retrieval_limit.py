from ttyg.graphdb import GraphDB


def retrieve(graphdb: GraphDB, query: str, limit: int) -> list[str]:
    results = graphdb.eval_sparql_query(
        "PREFIX retr: <http://www.ontotext.com/connectors/retrieval#>"
        "PREFIX retr-index: <http://www.ontotext.com/connectors/retrieval/instance#>"
        "SELECT ?entity {" +
        "   [] a retr-index:qa_dataset ;" +
        f"  retr:query \"{query}\" ;" +
        f"  retr:limit {limit} ;" +
        "   retr:entities ?entity ." +
        "  ?entity retr:score ?score." +
        " }" +
        "ORDER BY DESC(?score)",
        validation=False
    )
    return [
        entity["entity"]["value"].replace('https://www.statnett.no/Talk2PowerSystem/QA/Question_', '')
        for entity in results["results"]["bindings"]
    ]


def find_global_min_limit(graphdb: GraphDB, split: list[dict], max_limit: int) -> int:
    limit = 1

    for template in split:
        for question in template["questions"]:
            question_id = question["id"]
            nl_question = question["nl_question"]

            entities = retrieve(graphdb, nl_question, limit)

            while question_id not in entities:
                limit += 1
                entities = retrieve(graphdb, nl_question, limit)

                if limit == max_limit:
                    print(f"Warning. Reached maximum limit.")
                    break

            if limit == max_limit:
                break

        if limit == max_limit:
            break

    return limit
