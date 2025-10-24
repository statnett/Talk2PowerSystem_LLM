import random
import re
from datetime import datetime
from unittest import TestCase

import requests
from requests import Response

from .openai_mock import mock_openai, mock_openai_verify, mock_openai_reset


def is_valid_uuid_v4(s: str) -> bool:
    pattern = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
    return pattern.match(s) is not None


# Endpoints
API_ENDPOINT = "http://talk2powersystem:8000/"
GTG_ENDPOINT = API_ENDPOINT + "__gtg"
HEALTH_ENDPOINT = API_ENDPOINT + "__health"
ABOUT_ENDPOINT = API_ENDPOINT + "__about"
TROUBLE_ENDPOINT = API_ENDPOINT + "__trouble"
SECURITY_CONFIG_ENDPOINT = API_ENDPOINT + "/rest/authentication/config"
CONVERSATION_ENDPOINT = API_ENDPOINT + "/rest/chat/conversations"
EXPLAIN_ENDPOINT = API_ENDPOINT + "/rest/chat/conversations/explain"


class AcceptanceTestsApp(TestCase):

    def setUp(self):
        super(AcceptanceTestsApp, self).setUp()
        mock_openai_reset()

    def tearDown(self):
        super(AcceptanceTestsApp, self).tearDown()
        mock_openai_verify()

    def validate_response_and_return_json_body(
            self,
            response: Response,
            expected_status_code: int = 200,
            expected_x_request_id: str = None
    ) -> dict:
        self.assertEqual(expected_status_code, response.status_code)
        if expected_x_request_id:
            self.assertEqual(expected_x_request_id, response.headers.get("X-Request-Id"))
        else:
            self.assertTrue(is_valid_uuid_v4(response.headers.get("X-Request-Id")))
        return response.json()

    def test_gtg(self) -> None:
        response = requests.get(GTG_ENDPOINT, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response)
        expected_response_json = {"gtg": "OK"}
        self.assertEqual(expected_response_json, actual_response_json)

        response = requests.get(GTG_ENDPOINT, headers={"X-Request-Id": "test"}, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response, expected_x_request_id="test")
        self.assertEqual(expected_response_json, actual_response_json)

    def test_health(self) -> None:
        response = requests.get(HEALTH_ENDPOINT, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response)
        self.assertEqual(2, len(actual_response_json))
        self.assertTrue("status" in actual_response_json)
        self.assertEqual("OK", actual_response_json["status"])
        self.assertTrue("healthChecks" in actual_response_json)
        self.assertEqual(2, len(actual_response_json["healthChecks"]))
        self.assertTrue(
            {
                "status": "OK",
                "severity": "HIGH",
                "id": "http://talk2powersystem.no/talk2powersystem-api/graphdb-healthcheck",
                "name": "GraphDB Health Check",
                "type": "graphdb",
                "impact": "Chat bot won't be able to query GraphDB or tools may not function as expected.",
                "troubleshooting": "http://talk2powersystem:8000/__trouble#graphdb-health-check-status-is-not-ok",
                "description": "Checks if GraphDB repository can be queried. Also checks that the status of "
                               "the autocomplete index is READY, and the RDF rank status is COMPUTED.",
                "message": "GraphDB repository can be queried and it's configured correctly."
            } in actual_response_json["healthChecks"]
        )
        self.assertTrue(
            {
                "status": "OK",
                "severity": "HIGH",
                "id": "http://talk2powersystem.no/talk2powersystem-api/redis-healthcheck",
                "name": "Redis Health Check",
                "type": "redis",
                "impact": "Redis is inaccessible and the chat bot can't function",
                "troubleshooting": "http://talk2powersystem:8000/__trouble#redis-health-check-status-is-not-ok",
                "description": "Checks if Redis can be queried.",
                "message": "Redis can be queried."
            } in actual_response_json["healthChecks"]
        )

        response = requests.get(HEALTH_ENDPOINT, headers={"X-Request-Id": "test"}, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response, expected_x_request_id="test")
        self.assertEqual(2, len(actual_response_json))
        self.assertTrue("status" in actual_response_json)
        self.assertEqual("OK", actual_response_json["status"])
        self.assertTrue("healthChecks" in actual_response_json)
        self.assertEqual(2, len(actual_response_json["healthChecks"]))
        self.assertTrue(
            {
                "status": "OK",
                "severity": "HIGH",
                "id": "http://talk2powersystem.no/talk2powersystem-api/graphdb-healthcheck",
                "name": "GraphDB Health Check",
                "type": "graphdb",
                "impact": "Chat bot won't be able to query GraphDB or tools may not function as expected.",
                "troubleshooting": "http://talk2powersystem:8000/__trouble#graphdb-health-check-status-is-not-ok",
                "description": "Checks if GraphDB repository can be queried. Also checks that the status of "
                               "the autocomplete index is READY, and the RDF rank status is COMPUTED.",
                "message": "GraphDB repository can be queried and it's configured correctly."
            } in actual_response_json["healthChecks"]
        )
        self.assertTrue(
            {
                "status": "OK",
                "severity": "HIGH",
                "id": "http://talk2powersystem.no/talk2powersystem-api/redis-healthcheck",
                "name": "Redis Health Check",
                "type": "redis",
                "impact": "Redis is inaccessible and the chat bot can't function",
                "troubleshooting": "http://talk2powersystem:8000/__trouble#redis-health-check-status-is-not-ok",
                "description": "Checks if Redis can be queried.",
                "message": "Redis can be queried."
            } in actual_response_json["healthChecks"]
        )

    def verify_about_response(self, actual_response_json: dict) -> None:
        self.assertTrue("ontologies" in actual_response_json)
        self.assertEqual(3, len(actual_response_json["ontologies"]))
        self.assertEqual(
            "https://ap-voc.cim4.eu/ImpactAssessmentMatrix#Ontology", actual_response_json["ontologies"][0]["uri"]
        )
        self.assertEqual(
            "https://ap-voc.cim4.eu/AssessedElement#Ontology", actual_response_json["ontologies"][1]["uri"]
        )
        self.assertEqual(
            "Assessed Element Vocabulary", actual_response_json["ontologies"][1]["name"]
        )
        self.assertEqual(
            "2.3.1", actual_response_json["ontologies"][1]["version"]
        )
        self.assertEqual(
            "2024-09-07", actual_response_json["ontologies"][1]["date"]
        )
        self.assertEqual(
            "https://cim.ucaiug.io/rules#", actual_response_json["ontologies"][2]["uri"]
        )
        self.assertEqual(
            "CIM Inferred Extension Ontology", actual_response_json["ontologies"][2]["name"]
        )
        self.assertEqual(
            "1.1", actual_response_json["ontologies"][2]["version"]
        )
        self.assertEqual(
            "2025-08-13", actual_response_json["ontologies"][2]["date"]
        )

        self.assertTrue("datasets" in actual_response_json)
        self.assertEqual(3, len(actual_response_json["datasets"]))
        self.assertEqual(
            "urn:uuid:f1d9a88d-0ff5-4e4b-9d6a-c353fe8232c3", actual_response_json["datasets"][0]["uri"]
        )
        self.assertEqual(
            "urn:uuid:5ad50f29-f3e5-4cf9-8519-cef17d71f8de", actual_response_json["datasets"][1]["uri"]
        )
        self.assertEqual(
            "DIGIN10-30-GeographicalRegion_RD", actual_response_json["datasets"][1]["name"]
        )
        self.assertEqual(
            "2022-04-01", actual_response_json["datasets"][1]["date"]
        )
        self.assertEqual(
            "urn:uuid:5b6a8b13-4c20-4147-8ed6-7249e303e647", actual_response_json["datasets"][2]["uri"]
        )
        self.assertEqual(
            "State Variable (SV) part of the Nordic 44-bus synthetic test model "
            "developed by Statnett SF of the Nordic region.",
            actual_response_json["datasets"][2]["name"]
        )
        self.assertTrue(actual_response_json["datasets"][2]["date"] in ("2025-02-14", "2025-06-14"))

        self.assertTrue("graphdb" in actual_response_json)
        self.assertTrue("baseUrl" in actual_response_json["graphdb"])
        self.assertEqual("http://graphdb:7200", actual_response_json["graphdb"]["baseUrl"])
        self.assertTrue("repository" in actual_response_json["graphdb"])
        self.assertEqual("cim", actual_response_json["graphdb"]["repository"])
        self.assertTrue("version" in actual_response_json["graphdb"])
        self.assertTrue("numberOfExplicitTriples" in actual_response_json["graphdb"])
        self.assertTrue("numberOfTriples" in actual_response_json["graphdb"])
        self.assertTrue("autocompleteIndexStatus" in actual_response_json["graphdb"])
        self.assertEqual("READY", actual_response_json["graphdb"]["autocompleteIndexStatus"])
        self.assertTrue("rdfRankStatus" in actual_response_json["graphdb"])
        self.assertEqual("COMPUTED", actual_response_json["graphdb"]["rdfRankStatus"])

        self.assertTrue("agent" in actual_response_json)
        self.assertTrue("assistantInstructions" in actual_response_json["agent"])
        self.assertEqual(
            "Mocked responses. Prompt doesn't matter.\n",
            actual_response_json["agent"]["assistantInstructions"]
        )
        self.assertTrue("llm" in actual_response_json["agent"])
        self.assertTrue("type" in actual_response_json["agent"]["llm"])
        self.assertEqual("azure_openai", actual_response_json["agent"]["llm"]["type"])
        self.assertTrue("model" in actual_response_json["agent"]["llm"])
        self.assertEqual("gpt-4.1", actual_response_json["agent"]["llm"]["model"])
        self.assertTrue("temperature" in actual_response_json["agent"]["llm"])
        self.assertEqual(0, actual_response_json["agent"]["llm"]["temperature"])
        self.assertTrue("seed" in actual_response_json["agent"]["llm"])
        self.assertEqual(1, actual_response_json["agent"]["llm"]["seed"])
        self.assertTrue("tools" in actual_response_json["agent"])
        self.assertTrue("sparql_query" in actual_response_json["agent"]["tools"])
        self.assertTrue("enabled" in actual_response_json["agent"]["tools"]["sparql_query"])
        self.assertTrue(actual_response_json["agent"]["tools"]["sparql_query"]["enabled"])
        self.assertTrue("autocomplete_search" in actual_response_json["agent"]["tools"])
        self.assertTrue("enabled" in actual_response_json["agent"]["tools"]["autocomplete_search"])
        self.assertTrue(actual_response_json["agent"]["tools"]["autocomplete_search"]["enabled"])
        self.assertTrue("property_path" in actual_response_json["agent"]["tools"]["autocomplete_search"])
        self.assertEqual(
            "<https://cim.ucaiug.io/ns#IdentifiedObject.name> | "
            "<https://cim.ucaiug.io/ns#IdentifiedObject.aliasName> | "
            "<https://cim.ucaiug.io/ns#CoordinateSystem.crsUrn>",
            actual_response_json["agent"]["tools"]["autocomplete_search"]["property_path"]
        )
        self.assertTrue("sparql_query_template" in actual_response_json["agent"]["tools"]["autocomplete_search"])
        self.assertEqual(
            """PREFIX sesame: <http://www.openrdf.org/schema/sesame#>
PREFIX rank: <http://www.ontotext.com/owlim/RDFRank#>
PREFIX auto: <http://www.ontotext.com/plugins/autocomplete#>
SELECT ?iri ?name ?class ?rank {{
    ?iri auto:query "{query}" ;
        {property_path} ?name ;
        {filter_clause}
        sesame:directType ?class;
        rank:hasRDFRank5 ?rank.
}}
ORDER BY DESC(?rank)
LIMIT {limit}
""",
            actual_response_json["agent"]["tools"]["autocomplete_search"]["sparql_query_template"]
        )
        self.assertTrue("sample_sparql_queries" in actual_response_json["agent"]["tools"])
        self.assertTrue("enabled" in actual_response_json["agent"]["tools"]["sample_sparql_queries"])
        self.assertFalse(actual_response_json["agent"]["tools"]["sample_sparql_queries"]["enabled"])
        self.assertTrue("retrieve_data_points" in actual_response_json["agent"]["tools"])
        self.assertTrue("enabled" in actual_response_json["agent"]["tools"]["retrieve_data_points"])
        self.assertFalse(actual_response_json["agent"]["tools"]["retrieve_data_points"]["enabled"])
        self.assertTrue("retrieve_time_series" in actual_response_json["agent"]["tools"])
        self.assertTrue("enabled" in actual_response_json["agent"]["tools"]["retrieve_time_series"])
        self.assertFalse(actual_response_json["agent"]["tools"]["retrieve_time_series"]["enabled"])
        self.assertTrue("now" in actual_response_json["agent"]["tools"])
        self.assertTrue("enabled" in actual_response_json["agent"]["tools"]["now"])
        self.assertTrue(actual_response_json["agent"]["tools"]["now"]["enabled"])

        self.assertTrue("backend" in actual_response_json)
        self.assertTrue("description" in actual_response_json["backend"])
        self.assertEqual(
            "Talk2PowerSystem Chat Bot Application provides functionality for chatting with the "
            "Talk2PowerSystem Chat bot",
            actual_response_json["backend"]["description"]
        )
        self.assertTrue("version" in actual_response_json["backend"])
        self.assertTrue("buildDate" in actual_response_json["backend"])
        self.assertIsNotNone(actual_response_json["backend"]["buildDate"])
        self.assertTrue(actual_response_json["backend"]["buildDate"].strip())
        build_date = actual_response_json["backend"]["buildDate"]
        try:
            parsed = datetime.strptime(build_date, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            self.fail(f"String '{build_date}' is not a valid ISO 8601 UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)")
        self.assertIsInstance(parsed, datetime)
        self.assertTrue("buildBranch" in actual_response_json["backend"])
        self.assertIsNotNone(actual_response_json["backend"]["buildBranch"])
        self.assertTrue(actual_response_json["backend"]["buildBranch"].strip())
        self.assertTrue("gitSHA" in actual_response_json["backend"])
        self.assertIsNotNone(actual_response_json["backend"]["gitSHA"])
        self.assertTrue(actual_response_json["backend"]["gitSHA"].strip())
        self.assertTrue("pythonVersion" in actual_response_json["backend"])
        self.assertTrue("dependencies" in actual_response_json["backend"])

    def test_about(self) -> None:
        response = requests.get(ABOUT_ENDPOINT, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response)
        self.verify_about_response(actual_response_json)

        response = requests.get(ABOUT_ENDPOINT, headers={"X-Request-Id": "test"}, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response, expected_x_request_id="test")
        self.verify_about_response(actual_response_json)

    def test_trouble(self) -> None:
        response = requests.get(TROUBLE_ENDPOINT, timeout=(2, 10))
        self.assertEqual(200, response.status_code)
        self.assertTrue(is_valid_uuid_v4(response.headers.get("X-Request-Id")))

        response = requests.get(TROUBLE_ENDPOINT, headers={"X-Request-Id": "test"}, timeout=(2, 10))
        self.assertEqual(200, response.status_code)
        self.assertEqual("test", response.headers.get("X-Request-Id"))

    def test_security_config(self) -> None:
        response = requests.get(SECURITY_CONFIG_ENDPOINT, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response)
        self.assertTrue("enabled" in actual_response_json)
        self.assertEqual(False, actual_response_json["enabled"])

        response = requests.get(SECURITY_CONFIG_ENDPOINT, headers={"X-Request-Id": "test"}, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response, expected_x_request_id="test")
        self.assertTrue("enabled" in actual_response_json)
        self.assertEqual(False, actual_response_json["enabled"])

    def test_conversation_endpoint_conversation_not_found(self) -> None:
        request_json = {
            "question": "Who am I?",
            "conversationId": "thread_not_found"
        }
        response = requests.post(CONVERSATION_ENDPOINT, json=request_json, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response, expected_status_code=400)
        self.assertEqual(
            {"message": "Conversation with id \"thread_not_found\" not found."},
            actual_response_json
        )

    def test_explain_endpoint_conversation_not_found(self) -> None:
        request_json = {
            "conversationId": "thread_not_found",
            "messageId": "message_not_found",
        }
        response = requests.post(EXPLAIN_ENDPOINT, json=request_json, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(response, expected_status_code=400)
        self.assertEqual(
            {"message": "Conversation with id \"thread_not_found\" not found."},
            actual_response_json
        )

    def test_explain_endpoint_message_not_found(self) -> None:
        question = "Hello."
        answer = "Hello. How can I help you today?"
        prompt_tokens = random.randint(10, 20)
        completion_tokens = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question,
                    "role": "user"
                }
            ],
            response_content=answer,
            response_prompt_tokens=prompt_tokens,
            response_completion_tokens=completion_tokens,
            n_times=1
        )

        conversation_request_body = {"question": question}
        conversation_response = requests.post(CONVERSATION_ENDPOINT, json=conversation_request_body, timeout=(2, 10))
        conversation_response_body = self.validate_response_and_return_json_body(conversation_response)
        self.assertEqual(3, len(conversation_response_body))

        self.assertTrue("messages" in conversation_response_body)
        self.assertTrue(1, len(conversation_response_body["messages"]))
        self.assertEqual(3, len(conversation_response_body["messages"][0]))
        self.assertTrue("id" in conversation_response_body["messages"][0])
        self.assertTrue("message" in conversation_response_body["messages"][0])
        self.assertEqual(answer, conversation_response_body["messages"][0]["message"])
        self.assertTrue("usage" in conversation_response_body["messages"][0])
        self.assertEqual(
            {
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": prompt_tokens + completion_tokens
            },
            conversation_response_body["messages"][0]["usage"]
        )

        self.assertTrue("id" in conversation_response_body)
        self.assertTrue(conversation_response_body["id"].startswith("thread_"))
        self.assertTrue(is_valid_uuid_v4(conversation_response_body["id"].replace("thread_", "")))

        self.assertTrue("usage" in conversation_response_body)
        self.assertEqual(
            {
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": prompt_tokens + completion_tokens
            },
            conversation_response_body["usage"]
        )

        explain_request_body = {
            "conversationId": conversation_response_body["id"],
            "messageId": "message_not_found"
        }
        explain_response = requests.post(EXPLAIN_ENDPOINT, json=explain_request_body, timeout=(2, 10))
        actual_response_json = self.validate_response_and_return_json_body(explain_response, expected_status_code=400)
        self.assertEqual(
            {"message": "Message with id \"message_not_found\" not found."},
            actual_response_json
        )

    def test_explain_endpoint_no_query_methods(self) -> None:
        question = "Hello."
        answer = "Hello. How can I help you today?"
        prompt_tokens = random.randint(10, 20)
        completion_tokens = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question,
                    "role": "user"
                }
            ],
            response_content=answer,
            response_prompt_tokens=prompt_tokens,
            response_completion_tokens=completion_tokens,
            n_times=1
        )

        conversation_request_body = {"question": question}
        conversation_response = requests.post(CONVERSATION_ENDPOINT, json=conversation_request_body, timeout=(2, 10))
        conversation_response_body = self.validate_response_and_return_json_body(conversation_response)
        self.assertEqual(3, len(conversation_response_body))

        self.assertTrue("messages" in conversation_response_body)
        self.assertTrue(1, len(conversation_response_body["messages"]))
        self.assertEqual(3, len(conversation_response_body["messages"][0]))
        self.assertTrue("id" in conversation_response_body["messages"][0])
        self.assertTrue("message" in conversation_response_body["messages"][0])
        self.assertEqual(answer, conversation_response_body["messages"][0]["message"])
        self.assertTrue("usage" in conversation_response_body["messages"][0])
        self.assertEqual(
            {
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": prompt_tokens + completion_tokens
            },
            conversation_response_body["messages"][0]["usage"]
        )

        self.assertTrue("id" in conversation_response_body)
        self.assertTrue(conversation_response_body["id"].startswith("thread_"))
        self.assertTrue(is_valid_uuid_v4(conversation_response_body["id"].replace("thread_", "")))

        self.assertTrue("usage" in conversation_response_body)
        self.assertEqual(
            {
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": prompt_tokens + completion_tokens
            },
            conversation_response_body["usage"]
        )

        explain_request_body = {
            "conversationId": conversation_response_body["id"],
            "messageId": conversation_response_body["messages"][0]["id"]
        }
        explain_response = requests.post(EXPLAIN_ENDPOINT, json=explain_request_body, timeout=(2, 10))
        explain_response_body = self.validate_response_and_return_json_body(explain_response)
        self.assertEqual(
            {
                "conversationId": conversation_response_body["id"],
                "messageId": conversation_response_body["messages"][0]["id"],
                "queryMethods": []
            },
            explain_response_body
        )

    def test_explain_endpoint_with_query_methods_with_errors(self) -> None:
        question = "list substations"
        answer = "Here are the substations in the KG: 1. .."
        prompt_tokens1 = random.randint(10, 20)
        completion_tokens1 = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question,
                    "role": "user"
                }
            ],
            response_tool_calls=[
                {
                    "id": "sparql_query_call_1",
                    "type": "function",
                    "function": {
                        "name": "sparql_query",
                        "arguments": "{ \"query\": \"SELECT * { ?substation a cim:Substation }\" }"
                    }
                }
            ],
            response_prompt_tokens=prompt_tokens1,
            response_completion_tokens=completion_tokens1,
            n_times=1
        )
        prompt_tokens2 = random.randint(10, 20)
        completion_tokens2 = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question,
                    "role": "user"
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": "sparql_query_call_1",
                            "function": {
                                "name": "sparql_query",
                                "arguments": "{\"query\": \"SELECT * { ?substation a cim:Substation }\"}"
                            }
                        }
                    ]
                },
                {
                    "content": "Error: ValueError('The following prefixes are undefined: cim')\n Please fix your mistakes.",
                    "role": "tool",
                    "tool_call_id": "sparql_query_call_1"
                }
            ],
            response_content=answer,
            response_prompt_tokens=prompt_tokens2,
            response_completion_tokens=completion_tokens2,
            n_times=1
        )

        conversation_request_body = {"question": question}
        conversation_response = requests.post(CONVERSATION_ENDPOINT, json=conversation_request_body, timeout=(2, 10))
        conversation_response_body = self.validate_response_and_return_json_body(conversation_response)
        self.assertEqual(3, len(conversation_response_body))

        self.assertTrue("messages" in conversation_response_body)
        self.assertTrue(1, len(conversation_response_body["messages"]))
        self.assertEqual(3, len(conversation_response_body["messages"][0]))
        self.assertTrue("id" in conversation_response_body["messages"][0])
        self.assertTrue("message" in conversation_response_body["messages"][0])
        self.assertEqual(answer, conversation_response_body["messages"][0]["message"])
        self.assertTrue("usage" in conversation_response_body["messages"][0])
        self.assertEqual(
            {
                "promptTokens": prompt_tokens2,
                "completionTokens": completion_tokens2,
                "totalTokens": prompt_tokens2 + completion_tokens2
            },
            conversation_response_body["messages"][0]["usage"]
        )

        self.assertTrue("id" in conversation_response_body)
        self.assertTrue(conversation_response_body["id"].startswith("thread_"))
        self.assertTrue(is_valid_uuid_v4(conversation_response_body["id"].replace("thread_", "")))

        self.assertTrue("usage" in conversation_response_body)
        self.assertEqual(
            {
                "promptTokens": prompt_tokens1 + prompt_tokens2,
                "completionTokens": completion_tokens1 + completion_tokens2,
                "totalTokens": prompt_tokens1 + prompt_tokens2 + completion_tokens1 + completion_tokens2
            },
            conversation_response_body["usage"]
        )

        explain_request_body = {
            "conversationId": conversation_response_body["id"],
            "messageId": conversation_response_body["messages"][0]["id"]
        }
        explain_response = requests.post(EXPLAIN_ENDPOINT, json=explain_request_body, timeout=(2, 10))
        explain_response_body = self.validate_response_and_return_json_body(explain_response)
        self.assertEqual(
            {
                "conversationId": conversation_response_body["id"],
                "messageId": conversation_response_body["messages"][0]["id"],
                "queryMethods": [
                    {
                        "name": "sparql_query",
                        "args": {
                            "query": "SELECT * { ?substation a cim:Substation }"
                        },
                        "errorOutput": "Error: ValueError('The following prefixes are undefined: cim')\n Please fix your mistakes."
                    }
                ]
            },
            explain_response_body
        )

    def test_explain_endpoint(self) -> None:
        question_1 = "list substations"
        answer_1 = "Here are the substations in the KG: 1. .."
        question_2 = "and what time is now"
        answer_2 = "the current time is .."
        prompt_tokens1 = random.randint(10, 20)
        completion_tokens1 = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question_1,
                    "role": "user"
                }
            ],
            response_tool_calls=[
                {
                    "id": "sparql_query_call_1",
                    "type": "function",
                    "function": {
                        "name": "sparql_query",
                        "arguments": "{ \"query\": \"SELECT * { ?substation a <https://cim.ucaiug.io/ns#Substation> }\" }"
                    }
                }
            ],
            response_prompt_tokens=prompt_tokens1,
            response_completion_tokens=completion_tokens1,
            n_times=1
        )
        prompt_tokens2 = random.randint(10, 20)
        completion_tokens2 = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question_1,
                    "role": "user"
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": "sparql_query_call_1",
                            "function": {
                                "name": "sparql_query",
                                "arguments": "{\"query\": \"SELECT * { ?substation a <https://cim.ucaiug.io/ns#Substation> }\"}"
                            }
                        }
                    ]
                },
                {
                    "content": "{\n  \"head\": {\n    \"vars\": [\n      \"substation\"\n    ]\n  },\n  \"results\": {\n    \"bindings\": [\n      {\n        \"substation\": {\n          \"type\": \"uri\",\n          \"value\": \"urn:uuid:f176961e-9aeb-11e5-91da-b8763fd99c5f\"\n        }\n      }\n    ]\n  }\n}",
                    "role": "tool",
                    "tool_call_id": "sparql_query_call_1"
                }
            ],
            response_content=answer_1,
            response_prompt_tokens=prompt_tokens2,
            response_completion_tokens=completion_tokens2,
            n_times=1
        )

        conversation_request_body1 = {"question": question_1}
        conversation_response1 = requests.post(CONVERSATION_ENDPOINT, json=conversation_request_body1, timeout=(2, 10))
        conversation_response_body1 = self.validate_response_and_return_json_body(conversation_response1)

        prompt_tokens3 = random.randint(10, 20)
        completion_tokens3 = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question_1,
                    "role": "user"
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": "sparql_query_call_1",
                            "function": {
                                "name": "sparql_query",
                                "arguments": "{\"query\": \"SELECT * { ?substation a <https://cim.ucaiug.io/ns#Substation> }\"}"
                            }
                        }
                    ]
                },
                {
                    "content": "{\n  \"head\": {\n    \"vars\": [\n      \"substation\"\n    ]\n  },\n  \"results\": {\n    \"bindings\": [\n      {\n        \"substation\": {\n          \"type\": \"uri\",\n          \"value\": \"urn:uuid:f176961e-9aeb-11e5-91da-b8763fd99c5f\"\n        }\n      }\n    ]\n  }\n}",
                    "role": "tool",
                    "tool_call_id": "sparql_query_call_1"
                },
                {
                    "content": answer_1,
                    "role": "assistant",
                },
                {
                    "content": question_2,
                    "role": "user",
                }
            ],
            response_tool_calls=[
                {
                    "id": "now_call_1",
                    "type": "function",
                    "function": {
                        "name": "now",
                        "arguments": "{}"
                    }
                }
            ],
            response_prompt_tokens=prompt_tokens3,
            response_completion_tokens=completion_tokens3,
            n_times=1
        )
        prompt_tokens4 = random.randint(10, 20)
        completion_tokens4 = random.randint(10, 20)
        mock_openai(
            request_messages=[
                {
                    "content": question_1,
                    "role": "user"
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": "sparql_query_call_1",
                            "function": {
                                "name": "sparql_query",
                                "arguments": "{\"query\": \"SELECT * { ?substation a <https://cim.ucaiug.io/ns#Substation> }\"}"
                            }
                        }
                    ]
                },
                {
                    "content": "{\n  \"head\": {\n    \"vars\": [\n      \"substation\"\n    ]\n  },\n  \"results\": {\n    \"bindings\": [\n      {\n        \"substation\": {\n          \"type\": \"uri\",\n          \"value\": \"urn:uuid:f176961e-9aeb-11e5-91da-b8763fd99c5f\"\n        }\n      }\n    ]\n  }\n}",
                    "role": "tool",
                    "tool_call_id": "sparql_query_call_1"
                },
                {
                    "content": answer_1,
                    "role": "assistant",
                },
                {
                    "content": question_2,
                    "role": "user",
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": "now_call_1",
                            "function": {
                                "name": "now",
                                "arguments": "{}"
                            }
                        }
                    ]
                },
                {
                    "content": "${json-unit.ignore-element}",  # the actual now tool is called and this changes
                    "role": "tool",
                    "tool_call_id": "now_call_1",
                }
            ],
            response_content=answer_2,
            response_prompt_tokens=prompt_tokens4,
            response_completion_tokens=completion_tokens4,
            n_times=1
        )
        conversation_request_body2 = {"question": question_2, "conversationId": conversation_response_body1["id"]}
        conversation_response2 = requests.post(CONVERSATION_ENDPOINT, json=conversation_request_body2, timeout=(2, 10))
        conversation_response_body2 = self.validate_response_and_return_json_body(conversation_response2)

        explain_request_body1 = {
            "conversationId": conversation_response_body1["id"],
            "messageId": conversation_response_body1["messages"][0]["id"]
        }
        explain_response1 = requests.post(EXPLAIN_ENDPOINT, json=explain_request_body1, timeout=(2, 10))
        explain_response_body1 = self.validate_response_and_return_json_body(explain_response1)
        self.assertEqual(
            {
                "conversationId": conversation_response_body1["id"],
                "messageId": conversation_response_body1["messages"][0]["id"],
                "queryMethods": [
                    {
                        "name": "sparql_query",
                        "args": {
                            "query": "SELECT * { ?substation a <https://cim.ucaiug.io/ns#Substation> }"
                        },
                        "query": "SELECT * { ?substation a <https://cim.ucaiug.io/ns#Substation> }",
                        "queryType": "sparql"
                    }
                ]
            },
            explain_response_body1
        )

        explain_request_body2 = {
            "conversationId": conversation_response_body2["id"],
            "messageId": conversation_response_body2["messages"][0]["id"]
        }
        explain_response2 = requests.post(EXPLAIN_ENDPOINT, json=explain_request_body2, timeout=(2, 10))
        explain_response_body2 = self.validate_response_and_return_json_body(explain_response2)
        self.assertEqual(
            {
                "conversationId": conversation_response_body2["id"],
                "messageId": conversation_response_body2["messages"][0]["id"],
                "queryMethods": [
                    {
                        "name": "now",
                        "args": {}
                    }
                ]
            },
            explain_response_body2
        )
