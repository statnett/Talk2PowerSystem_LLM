[TOC]

# Troubleshooting Talk2PowerSystem Chat Bot Application

Synopsis: a document designed to help identify and resolve known issues with Talk2PowerSystem Chat Bot Application.

## Introduction

This document is designed to help troubleshoot the Talk2PowerSystem Chat Bot Application.
It [describes](#service-overview) the service, the [context](#context-diagram) in which it resides, and lists its
most [important endpoints](#important-endpoints).

The reader of this document should have the [prerequisite](#prerequisites) skills for the document to be
effective. [Known issues](#resolving-known-issues) and solutions are documented.

### Service Overview

The application is implemented in Python and uses Fast API. It's served with the uvicorn server.
It provides functionality for chatting with the Talk2PowerSystem Chat Bot.
It doesn't provide functionalities for:

- creating, updating or deleting chat bots
- conversations / chats histories

The chat bot memory is persisted in Redis.

#### Context Diagram

Talk2PowerSystem Chat Bot Application depends on GraphDB, Azure OpenAI, Redis and optionally on Cognite.

![context-diagram](https://lucid.app/publicSegments/view/f29659b5-21c1-4b8b-b91b-b8b2d4eea769/image.jpeg)

#### Important Endpoints

##### POST /rest/chat/conversations

Starts a new conversation or adds message to an existing conversation

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Content-Type - "application/json"

- Accept - "application/json"

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - Successful Response

- 400 - Conversation not found

- 422 - Validation Error

Request Body JSON Schema:
```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "conversationId": {
      "type": "string"
    },
    "question": {
      "type": "string"
    }
  },
  "required": [
    "question"
  ]
}
```

Sample Request Bodies:

- New conversation

```json
{
  "question": "List all transformers within substation OSLO."
}
```

- Adding messages to existing conversation

```json
{
 "conversationId": "thread_x8PTAw42sC3Mzl7vr6JP8ZMa",
 "question": "List all transformers within substation OSLO."
}
```

Response Body JSON Schema:

```json
{
 "$schema": "http://json-schema.org/draft-04/schema#",
 "type": "object",
 "properties": {
   "id": {
     "type": "string"
   },
   "messages": {
     "type": "array",
     "items": [
       {
         "type": "object",
         "properties": {
           "id": {
             "type": "string"
           },
           "message": {
             "type": "string"
           },
           "usage": {
             "type": "object",
             "properties": {
               "completionTokens": {
                 "type": "integer"
               },
               "promptTokens": {
                 "type": "integer"
               },
               "totalTokens": {
                 "type": "integer"
               }
             },
             "required": [
               "completionTokens",
               "promptTokens",
               "totalTokens"
             ]
           }
         },
         "required": [
           "id",
           "message",
           "usage"
         ]
       }
     ]
   },
   "usage": {
     "type": "object",
     "properties": {
       "completionTokens": {
         "type": "integer"
       },
       "promptTokens": {
         "type": "integer"
       },
       "totalTokens": {
         "type": "integer"
       }
     },
     "required": [
       "completionTokens",
       "promptTokens",
       "totalTokens"
     ]
   }
 },
 "required": [
   "id",
   "messages",
   "usage"
 ]
}
```

Sample Response Body:

```json
{
    "id": "thread_x8PTAw42sC3Mzl7vr6JP8ZMa",
    "messages": [
        {
            "id": "msg_sObdXPBa0RBtvwl2BR6hUVd9",
            "message": "The following transformers are within substation OSLO:\n\n1. OSLO T1\n2. OSLO T2\n\nLet me know if you need more details about these transformers.",
            "usage": {
                "completionTokens": 38,
                "promptTokens": 57322,
                "totalTokens": 57360
            }
        }
    ],
    "usage": {
        "completionTokens": 38,
        "promptTokens": 57322,
        "totalTokens": 57360
    }
}
```

##### POST /rest/chat/conversations/explain/

For a given message in a conversation returns the tools calls made by the AI agent

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Content-Type - "application/json"

- Accept - "application/json"

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - Successful Response 

- 400 - Conversation or message not found

- 422 - Validation error

Request Body JSON Schema:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "conversationId": {
      "type": "string"
    },
    "messageId": {
      "type": "string"
    }
  },
  "required": [
    "conversationId",
    "messageId"
  ]
}
```

Sample Request Body:

```json
{
    "conversationId": "thread_x8PTAw42sC3Mzl7vr6JP8ZMa",
    "messageId": "msg_sObdXPBa0RBtvwl2BR6hUVd9"
}
```

Response Body JSON Schema:

```json
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "conversationId": {
            "type": "string"
        },
        "messageId": {
            "type": "string"
        },
        "queryMethods": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "args": {
                            "type": "object"
                        },
                        "query": {
                            "type": "string",
                            "description": "Present only if the queryType is present."
                        },
                        "queryType": {
                            "enum": [
                                "sparql"
                            ]
                        },
                        "errorOutput": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "name",
                        "args"
                    ]
                }
            ]
        }
    },
    "required": [
        "conversationId",
        "messageId",
        "queryMethods"
    ]
}
```

Sample Response Body:

```json
{
    "conversationId": "thread_x8PTAw42sC3Mzl7vr6JP8ZMa",
    "messageId": "msg_sObdXPBa0RBtvwl2BR6hUVd9",
    "queryMethods": [
        {
            "name": "autocomplete_search",
            "args": {
                "query": "OSLO",
                "result_class": "cim:Substation"
            },
            "query": "\nPREFIX sesame: <http://www.openrdf.org/schema/sesame#>\nPREFIX rank: <http://www.ontotext.com/owlim/RDFRank#>\nPREFIX auto: <http://www.ontotext.com/plugins/autocomplete#>\nSELECT ?iri ?name ?class ?rank {\n    ?iri auto:query \"OSLO\" ;\n        <https://cim.ucaiug.io/ns#IdentifiedObject.name> | <https://cim.ucaiug.io/ns#IdentifiedObject.aliasName> | <https://cim.ucaiug.io/ns#CoordinateSystem.crsUrn> ?name ;\n        a cim:Substation ;\n        sesame:directType ?class;\n        rank:hasRDFRank5 ?rank.\n}\nORDER BY DESC(?rank)\nLIMIT 10",
            "queryType": "sparql"
        },
        {
            "name": "sparql_query",
            "args": {
                "query": "SELECT ?class WHERE { <urn:uri:1234> a ?class }"
            },
            "query": "SELECT ?class WHERE { <urn:uri:1234> a ?class }",
            "queryType": "sparql",
            "errorOutput": "Error: ValueError('The following IRIs are not used in the data stored in GraphDB: <urn:uri:1234>') Please fix your mistakes."
        },
        {
            "name": "sparql_query",
            "args": {
                "query": "\nSELECT ?transformer ?name WHERE {\n  ?transformer a cim:PowerTransformer .\n  ?transformer cim:Equipment.EquipmentContainer <urn:uuid:f176963c-9aeb-11e5-91da-b8763fd99c5f> .\n  OPTIONAL { ?transformer cim:IdentifiedObject.name ?name }\n} ORDER BY ?name"
            },
            "query": "\nPREFIX cim: <https://cim.ucaiug.io/ns#>\nSELECT ?transformer ?name WHERE {\n  ?transformer a cim:PowerTransformer .\n  ?transformer cim:Equipment.EquipmentContainer <urn:uuid:f176963c-9aeb-11e5-91da-b8763fd99c5f> .\n  OPTIONAL { ?transformer cim:IdentifiedObject.name ?name }\n} ORDER BY ?name",
            "queryType": "sparql"
        },
        {
            "name": "retrieve_data_points",
            "args": {
                "external_id": "9bb00faf-0f2f-831a-e040-1e828c94e833_estimated_value",
                "aggregates": [
                    "average",
                    "count"
                ],
                "granularity": "2days"
            }
        }
    ]
}
```

##### GET /__health

Returns the health status of the application

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Accept - "application/json"

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - Successful Response

Response Body JSON Schema:

```json
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "status": {
            "type": "string"
        },
        "healthChecks": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string"
                        },
                        "severity": {
                            "type": "string"
                        },
                        "id": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "type": {
                            "type": "string"
                        },
                        "impact": {
                            "type": "string"
                        },
                        "troubleshooting": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        },
                        "message": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "status",
                        "severity",
                        "id",
                        "name",
                        "type",
                        "impact",
                        "troubleshooting",
                        "description",
                        "message"
                    ]
                }
            ]
        }
    },
    "required": [
        "status",
        "healthChecks"
    ]
}
```

Sample Response Body:

```json
{
    "status": "OK",
    "healthChecks": [
        {
            "status": "OK",
            "severity": "HIGH",
            "id": "http://talk2powersystem.no/talk2powersystem-api/redis-healthcheck",
            "name": "Redis Health Check",
            "type": "redis",
            "impact": "Redis is inaccessible and the chat bot can't function",
            "troubleshooting": "http://localhost:8000/__trouble#redis-health-check-status-is-not-ok",
            "description": "Checks if Redis can be queried.",
            "message": "Redis can be queried."
        },
        {
            "status": "OK",
            "severity": "HIGH",
            "id": "http://talk2powersystem.no/talk2powersystem-api/cognite-healthcheck",
            "name": "Cognite Health Check",
            "type": "cognite",
            "impact": "Chat bot won't be able to query Cognite or tools may not function as expected.",
            "troubleshooting": "http://localhost:8000/__trouble#cognite-health-check-status-is-not-ok",
            "description": "Checks if Cognite can be queried by listing the time series with limit of 1.",
            "message": "Cognite can be queried."
        },
        {
            "status": "OK",
            "severity": "HIGH",
            "id": "http://talk2powersystem.no/talk2powersystem-api/graphdb-healthcheck",
            "name": "GraphDB Health Check",
            "type": "graphdb",
            "impact": "Chat bot won't be able to query GraphDB or tools may not function as expected.",
            "troubleshooting": "http://localhost:8000/__trouble#graphdb-health-check-status-is-not-ok",
            "description": "Checks if GraphDB repository can be queried. Also checks that the autocomplete is enabled, and RDF rank is computed.",
            "message": "GraphDB repository can be queried and it's configured correctly."
        }
    ]
}
```

##### GET /__gtg

Returns if the service is good to go

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Accept - "application/json"

Query Parameters:

- cache (boolean, defaults to `true`) - whether to return the last cached value or force a new check of the system health and refresh the cache

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - The service is good to go

- 503 - The service is unavailable

Response Body JSON Schema:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "gtg": {
      "type": "string"
    }
  },
  "required": [
    "gtg"
  ]
}
```

Sample Response Body:

```json
{
  "gtg": "OK"
}
```

##### GET /__about

Describes the application and provides build info about the component

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Accept - "application/json"

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - Successful Response

Sample Response Body

```json
{
  "description": "Talk2PowerSystem Chat Bot Application provides functionality for chatting with the Talk2PowerSystem Chat bot",
  "version": "0.0.0a0",
  "buildDate": "2024-01-09T13:31:49Z",
  "buildBranch": "COOL-BRANCH-NAME",
  "gitSHA": "a730751ac055a4f2dad3dc3e5658bb1bf30ff412",
  "pythonVersion": "3.12.11",
  "systemVersion": "3.12.11 | packaged by conda-forge | (main, Jun  4 2025, 14:45:31) [GCC 13.3.0]",
  "fastApiVersion": "0.115.14",
  "uvicornVersion": "0.35.0"
}
```

##### GET /__trouble

Returns an html rendering of the trouble document for the application

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Accept - "text/html"

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "text/html"

Response Status Codes:

- 200 - Successful Response

## Prerequisites

Users, maintainers and testers who wish to effectively troubleshoot the Talk2PowerSystem Chat Bot Application must be
experienced with the following:

* REST (curl/postman)
* docker, k8s, helm
* bash
* GraphDB
* Cognite
* Azure OpenAI
* Redis

## Resolving Known Issues

### Issues

#### GraphDB health check status is not OK

Most probable cause: ["GraphDB can't be queried or is mis-configured"](#graphdb-cant-be-queried-or-is-mis-configured)

#### Calls made by the LLM agent to the tools `sparql_query`, `autocomplete_search`, `retrieval_search` are failing

Most probable cause: ["GraphDB can't be queried or is mis-configured"](#graphdb-cant-be-queried-or-is-mis-configured)

#### Cognite health check status is not OK

Most probable cause: ["Cognite can't be queried or is mis-configured"](#cognite-cant-be-queried-or-is-mis-configured)

#### Calls made by the LLM agent to the tools `retrieve_time_series`, `retrieve_data_points` are failing

Most probable cause: ["Cognite can't be queried or is mis-configured"](#cognite-cant-be-queried-or-is-mis-configured)

#### Redis health check status is not OK

Most probable cause: ["Redis can't be queried or is mis-configured"](#redis-cant-be-queried-or-is-mis-configured)

#### Users are experiencing slow responses

Most probable cause: ["Mis-configurations"](#mis-configurations)

### Causes

This section lists the causes of known issues and provides solutions.

#### GraphDB can't be queried or is mis-configured

##### Solution

- Make sure GraphDB is reachable from the app host.
- Make sure GraphDB credentials are correct.
- Make sure GraphDB timeouts are configured correctly according to the network performance.
- Make sure [GraphDB autocomplete index is enabled](https://graphdb.ontotext.com/documentation/11.0/autocomplete-index.html).
- Make sure [GraphDB RDF rank](https://graphdb.ontotext.com/documentation/10.0/rdf-rank.html) is computed and up-to-date. The status must be `COMPUTED`.

##### Verification

- Check the response status code of the `__gtg` endpoint, it must be `200`.
- Check the response body of the `__health` endpoint, GraphDB health check must have status `OK`.

#### Cognite can't be queried or is mis-configured

##### Solution

- Make sure Cognite is reachable from the app host.
- Make sure Cognite credentials are correct.

##### Verification

- Check the response status code of the `__gtg` endpoint, it must be `200`.
- Check the response body of the `__health` endpoint, Cognite health check must have status `OK`.

#### Redis can't be queried or is mis-configured

##### Solution

- Make sure Redis is reachable from the app host.
- Make sure Redis connect and read timeouts are configured correctly.
- Make sure Redis credentials are correct.

##### Verification

- Check the response status code of the `__gtg` endpoint, it must be `200`.
- Check the response body of the `__health` endpoint, Redis health check must have status `OK`.

#### Mis-configurations

##### Solution

- Make sure GraphDB timeouts are configured correctly according to the network performance.
- Make sure Redis connect and read timeouts are configured correctly.
- Make sure the application is not hitting [Azure OpenAI rate limits](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/quotas-limits?tabs=REST).
If this is the case, they must be increased. 
- Make sure the number of uvicorn [workers](https://fastapi.tiangolo.com/deployment/server-workers/) is configured according to the number of parallel users of the system.

##### Verification

Users no longer report slow responses
