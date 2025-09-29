import re

from rdflib import Graph, URIRef, Namespace, RDF, Literal


def replace_object_identity(match):
    # match group looks like: "0, cim:SynchronousMachineOperatingMode"
    text = match.group(1).strip()
    return f"<<<{text}>>>"


def replace_value_filter(match):
    # match group looks like: "cim:GeneratingUnit, cim:GeneratingUnit.maxOperatingP, xsd:float"
    parts = match.group(1).split(",")
    if parts:
        return f"<<<{parts[-1].split(':')[-1].strip()}>>>"
    return match.group(0)


def transform_paraphrase(paraphrase: str) -> str:
    paraphrase = re.sub(r"\$ObjectIdentity\((.*?)\)", replace_object_identity, paraphrase)
    return re.sub(r"\$ValueFilter\((.*?)\)", replace_value_filter, paraphrase)


def transform_sparql(sparql_query: str) -> str:
    sparql_query = re.sub(r"{\$ObjectIdentity\((.*?)\)}", replace_object_identity, sparql_query)
    return re.sub(r"{\$ValueFilter\((.*?)\)}", replace_value_filter, sparql_query)


def verify_unique_placeholders(text: str) -> bool:
    # Find all <<< >>> placeholders
    placeholders = re.findall(r'<<<(.*?)>>>', text)

    # Check uniqueness
    unique_placeholders = set(placeholders)

    if len(placeholders) == len(unique_placeholders):
        return True
    else:
        print("❌ Duplicate placeholders found:")
        print(text)
        seen = set()
        for ph in placeholders:
            if ph in seen:
                print(f"   - {ph}")
            else:
                seen.add(ph)
        return False


def build_qa_dataset_graph(split):
    base_ns = "https://www.statnett.no/Talk2PowerSystem/QA/"
    qa_dataset_ns = Namespace("https://www.statnett.no/Talk2PowerSystem/qa#")
    graph = Graph()
    graph.bind("qa", qa_dataset_ns)

    for template in split:
        template_iri = URIRef(f"Template_{template['template_id']}", base_ns)
        graph.add((template_iri, RDF.type, qa_dataset_ns.Template))
        sparql_template = template["sparql_template"]

        for n, paraphrase in enumerate(template["paraphrases"]):
            paraphrase_iri = URIRef(f"Paraphrase_{template['template_id']}_{n}", base_ns)
            graph.add((paraphrase_iri, RDF.type, qa_dataset_ns.Paraphrase))
            graph.add((template_iri, qa_dataset_ns.paraphrase, paraphrase_iri))
            graph.add((paraphrase_iri, qa_dataset_ns.question, Literal(transform_paraphrase(paraphrase))))
            verify_unique_placeholders(transform_paraphrase(paraphrase))
            graph.add((paraphrase_iri, qa_dataset_ns.sparql_query, Literal(transform_sparql(sparql_template))))
    return graph
