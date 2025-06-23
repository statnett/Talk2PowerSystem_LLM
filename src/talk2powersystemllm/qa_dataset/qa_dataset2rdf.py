from rdflib import Graph, URIRef, Namespace, RDF, Literal


def parameter_to_placeholder(parameter: str) -> str:
    """
    Examples:
    $ObjectIdentity(0, cim:SubGeographicalRegion) will be replaced with <SubGeographicalRegion>
    $ValueFilter(cim:GeneratingUnit, cim:GeneratingUnit.maxOperatingP, xsd:float) will be replaced with <float>
    """
    replacement = parameter[(parameter.rindex(",") + 1):-1]
    replacement = replacement[(replacement.index(":") + 1):]
    return f"<{replacement}>"


def build_qa_dataset_graph(split):
    base_ns = "https://www.statnett.no/Talk2PowerSystem/QA/"
    qa_dataset_ns = Namespace("https://www.statnett.no/Talk2PowerSystem/qa#")
    graph = Graph()
    graph.bind("qa", qa_dataset_ns)

    for template in split:
        template_iri = URIRef(f"Template_{template['template_id']}", base_ns)
        graph.add((template_iri, RDF.type, qa_dataset_ns.Template))

        for question in template["questions"]:
            question_iri = URIRef(f"Question_{question['id']}", base_ns)
            graph.add((question_iri, RDF.type, qa_dataset_ns.Question))
            graph.add((template_iri, qa_dataset_ns.question, question_iri))

            nl_question = question["nl_question"]
            parameter_bindings = question["parameter_bindings"]

            for parameter, binding in parameter_bindings.items():
                if parameter.startswith("$ObjectIdentity"):
                    if not binding.startswith("urn:uuid:"):
                        if binding in nl_question:
                            if nl_question.index(binding) != nl_question.rindex(binding):
                                raise Exception
                            nl_question = nl_question.replace(binding, parameter_to_placeholder(parameter))
                        else:
                            binding = binding[binding.rindex(".") + 1:]
                            if binding in nl_question:
                                if nl_question.index(binding) != nl_question.rindex(binding):
                                    raise Exception
                                nl_question = nl_question.replace(binding, parameter_to_placeholder(parameter))
                            else:
                                raise Exception
                    else:
                        if binding in nl_question:
                            if nl_question.index(binding) != nl_question.rindex(binding):
                                raise Exception
                            nl_question = nl_question.replace(binding, parameter_to_placeholder(parameter))
                        else:
                            binding = binding.replace("urn:uuid:", "")
                            iri_discovery_steps = [
                                step
                                for steps in question["expected_steps"]
                                for step in steps
                                if step["name"] == "iri_discovery"
                            ]
                            iri_discovery_output_to_step = {
                                step["output"].replace("urn:uuid:", ""): step
                                for step in iri_discovery_steps
                            }
                            iri_discovery_step = iri_discovery_output_to_step[binding]
                            iri_discovery_query = iri_discovery_step["args"]["query"]
                            if iri_discovery_query in nl_question:
                                nl_question = nl_question.replace(
                                    iri_discovery_query, parameter_to_placeholder(parameter)
                                )

            for parameter, binding in parameter_bindings.items():
                if parameter.startswith("$ValueFilter"):
                    if binding in nl_question:
                        if nl_question.index(binding) != nl_question.rindex(binding):
                            raise Exception
                        nl_question = nl_question.replace(binding, parameter_to_placeholder(parameter))
                    else:
                        raise Exception

            graph.add((question_iri, qa_dataset_ns.nl_question, Literal(nl_question)))
            sparql_query_step = question["expected_steps"][-1][0]
            sparql_query = sparql_query_step["args"]["query"]
            graph.add((question_iri, qa_dataset_ns.sparql_query, Literal(sparql_query)))
    return graph
