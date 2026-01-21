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

The application can be secured using OpenID.

#### Context Diagram

Talk2PowerSystem Chat Bot Application depends on GraphDB, Azure OpenAI, Redis and optionally on Cognite.

![context-diagram](https://lucid.app/publicSegments/view/f29659b5-21c1-4b8b-b91b-b8b2d4eea769/image.jpeg)

#### Important Endpoints

##### GET /rest/authentication/config

Exposes authentication configuration settings used by the UI

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
    "enabled": {
      "type": "boolean"
    },
    "clientId": {
      "type": "string"
    },
    "frontendAppClientId": {
      "type": "string"
    },
    "scopes": {
      "type": "array",
      "items": [
        {
          "type": "string"
        }
      ]
    },
    "authority": {
      "type": "string"
    },
    "logout": {
      "type": "string"
    },
    "loginRedirect": {
      "type": "string"
    },
    "logoutRedirect": {
      "type": "string"
    }
  },
  "required": [
    "enabled"
  ]
}
```

Sample Response Body:

```json
{
  "enabled": true,
  "clientId": "7b9f2087-68f1-45fe-a21d-023daedd4047",
  "frontendAppClientId": "10acd638-f239-4aa2-8186-761512253325",
  "scopes": [
    "openid",
    "profile",
    "api://7b9f2087-68f1-45fe-a21d-023daedd4047/access_as_user"
  ],
  "authority": "https://login.microsoftonline.com/519ed184-e4d5-4431-97e5-fb4410a3f875",
  "logout": "https://login.microsoftonline.com/519ed184-e4d5-4431-97e5-fb4410a3f875/oauth2/v2.0/logout",
  "loginRedirect": "http://localhost:3000/",
  "logoutRedirect": "http://localhost:3000/"
}
```

##### POST /rest/chat/conversations

Starts a new conversation or adds a message to an existing conversation.

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Content-Type - "application/json"

- Accept - "application/json"

- Authorization - "Bearer <token\>" 

- X-User-Datetime - The date and time at which the message was originated, in ISO 8601 format: ``yyyy-mm-ddTHH:MM:SS±hhmm``

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - Successful Response

- 400 - Conversation not found

- 401 - Unauthorized

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
                        },
                        "graphics": {
                            "type": "array",
                            "items": {
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": [
                                                    "svg"
                                                ]
                                            },
                                            "svg": {
                                                "type": "string"
                                            }
                                        },
                                        "required": [
                                            "type",
                                            "svg"
                                        ],
                                        "additionalProperties": false
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": [
                                                    "image"
                                                ]
                                            },
                                            "url": {
                                                "type": "string",
                                                "format": "uri-reference"
                                            }
                                        },
                                        "required": [
                                            "type",
                                            "url"
                                        ],
                                        "additionalProperties": false
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": [
                                                    "iframe"
                                                ]
                                            },
                                            "url": {
                                                "type": "string",
                                                "format": "uri"
                                            }
                                        },
                                        "required": [
                                            "type",
                                            "url"
                                        ],
                                        "additionalProperties": false
                                    }
                                ]
                            }
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

Sample Response Body Without Graphics:

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

Sample Response Body Including Graphics:

- PowSyBl diagram:
```json
{
    "id": "thread_bd697c94-29d4-46c1-ba96-69615d2538b4",
    "messages": [
        {
            "id": "lc_run--019bc183-1b25-7a30-b8df-d746abdf1d20-0",
            "message": "Here is the **PowSyBl Single-Line Diagram (SLD)** for the **OSLO** substation:\n\n- Substation IRI: `<urn:uuid:f176963c-9aeb-11e5-91da-b8763fd99c5f>`\n- Diagram IRI: `<urn:uuid:a53f9c60-189d-4be2-b3af-0320298e529d>`",
            "usage": {
                "completionTokens": 821,
                "promptTokens": 434519,
                "totalTokens": 435340
            },
            "graphics": [
                {
                    "type": "image",
                    "url": "/rest/chat/diagrams/PowSyBl-SLD-substation-OSLO.svg"
                }
            ]
        }
    ],
    "usage": {
        "completionTokens": 821,
        "promptTokens": 434519,
        "totalTokens": 435340
    }
}
```

- Saved GraphDB Visual Graph
```json
{
    "id": "thread_bd697c94-29d4-46c1-ba96-69615d2538b4",
    "messages": [
        {
            "id": "lc_run--019bc188-fb32-7ed2-8e73-b3ba6601a1e8-0",
            "message": "Here is the **saved VizGraph diagram** for **TopologicalNode ARENDAL**:\n\n- TopologicalNode IRI: `<urn:uuid:47eb7c24-d0f6-11e7-9f7b-b46d83638f70>`\n- VizGraph diagram IRI: `<urn:uuid:83179477-422c-403b-aca8-d577227430b8>`",
            "usage": {
                "completionTokens": 432,
                "promptTokens": 358842,
                "totalTokens": 359274
            },
            "graphics": [
                {
                    "type": "iframe",
                    "url": "https://cim.ontotext.com/graphdb/graphs-visualizations?saved=dc0d824cdbfb4ca196c71ad55d6b1eb1"
                }
            ]
        }
    ],
    "usage": {
        "completionTokens": 432,
        "promptTokens": 358842,
        "totalTokens": 359274
    }
}
```

- GraphDB Visual Graph Saved Configuration
```json
{
    "id": "thread_bd697c94-29d4-46c1-ba96-69615d2538b4",
    "messages": [
        {
            "id": "lc_run--019bc18e-8ac6-7e53-8a19-a303830cba9c-0",
            "message": "Here is the **VizGraph using the “VoltageLevel” configuration** for **HELSINKI420**:\n\n- VoltageLevel IRI: `<urn:uuid:f17696b4-9aeb-11e5-91da-b8763fd99c5f>`\n- Diagram configuration IRI: `<urn:uuid:694c7201-eef8-49c5-8fe7-bd48c01e4cc0>`",
            "usage": {
                "completionTokens": 470,
                "promptTokens": 275045,
                "totalTokens": 275515
            },
            "graphics": [
                {
                    "type": "iframe",
                    "url": "https://cim.ontotext.com/graphdb/graphs-visualizations?config=99638482586148159e97fb379901dc54&uri=urn:uuid:f17696b4-9aeb-11e5-91da-b8763fd99c5f"
                }
            ]
        }
    ],
    "usage": {
        "completionTokens": 470,
        "promptTokens": 275045,
        "totalTokens": 275515
    }
}
```

##### GET /rest/chat/diagrams/{filename}

Serves the static diagrams.

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Accept - "\*/\*"

- Authorization - "Bearer <token\>"

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Cache-Control - "private, max-age=3600"

- Content-Type - "\*/\*"

- Content-Length

- Last-Modified

- Date

- Etag

- Accept-Ranges

Response Status Codes:

- 200 - Successful Response

- 401 - Unauthorized

- 404 - File Not Found

##### POST /rest/chat/conversations/explain/

For a given message in a conversation returns the tools calls made by the AI agent

Request Headers:

- X-Request-Id - version 4 UUID, which can be used to correlate HTTP requests between clients, services and service dependencies; optional, if not provided, it will be automatically generated and returned as a response header

- Content-Type - "application/json"

- Accept - "application/json"

- Authorization - "Bearer <token\>" 

Response Headers:

- X-Request-Id - Same as the Request Header "X-Request-Id"; auto generated version 4 UUID, if the request didn't include it

- Content-Type - "application/json"

Response Status Codes:

- 200 - Successful Response 

- 400 - Conversation or message not found

- 401 - Unauthorized

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

Response Body JSON Schema:

```json
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "ontologies": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "uri": {
                            "type": "string"
                        },
                        "version": {
                            "type": "string"
                        },
                        "date": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "uri"
                    ]
                }
            ]
        },
        "datasets": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "uri": {
                            "type": "string"
                        },
                        "date": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "uri"
                    ]
                }
            ]
        },
        "graphdb": {
            "type": "object",
            "properties": {
                "baseUrl": {
                    "type": "string"
                },
                "repository": {
                    "type": "string"
                },
                "version": {
                    "type": "string"
                },
                "numberOfExplicitTriples": {
                    "type": "integer"
                },
                "numberOfTriples": {
                    "type": "integer"
                },
                "autocompleteIndexStatus": {
                    "type": "string"
                },
                "rdfRankStatus": {
                    "type": "string"
                }
            },
            "required": [
                "baseUrl",
                "repository",
                "version",
                "numberOfExplicitTriples",
                "numberOfTriples",
                "autocompleteIndexStatus",
                "rdfRankStatus"
            ]
        },
        "agent": {
            "type": "object",
            "properties": {
                "assistantInstructions": {
                    "type": "string"
                },
                "llm": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string"
                        },
                        "model": {
                            "type": "string"
                        },
                        "temperature": {
                            "type": "number"
                        },
                        "seed": {
                            "type": "integer"
                        }
                    },
                    "required": [
                        "type",
                        "model",
                        "temperature",
                        "seed"
                    ]
                },
                "tools": {
                    "type": "object",
                    "properties": {
                        "sparql_query": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                }
                            },
                            "required": [
                                "enabled"
                            ]
                        },
                        "display_graphics": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                },
                                "sparql_query_template": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "enabled",
                                "sparql_query_template"
                            ]
                        },
                        "autocomplete_search": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                },
                                "property_path": {
                                    "type": "string"
                                },
                                "sparql_query_template": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "enabled"
                            ]
                        },
                        "sample_sparql_queries": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                },
                                "sparql_query_template": {
                                    "type": "string"
                                },
                                "connector_name": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "enabled"
                            ]
                        },
                        "retrieve_data_points": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                },
                                "base_url": {
                                    "type": "string"
                                },
                                "project": {
                                    "type": "string"
                                },
                                "client_name": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "enabled"
                            ]
                        },
                        "retrieve_time_series": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                },
                                "base_url": {
                                    "type": "string"
                                },
                                "project": {
                                    "type": "string"
                                },
                                "client_name": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "enabled"
                            ]
                        },
                        "now": {
                            "type": "object",
                            "properties": {
                                "enabled": {
                                    "type": "boolean"
                                }
                            },
                            "required": [
                                "enabled"
                            ]
                        }
                    },
                    "required": [
                        "sparql_query",
                        "display_graphics",
                        "autocomplete_search",
                        "sample_sparql_queries",
                        "retrieve_data_points",
                        "retrieve_time_series",
                        "now"
                    ]
                }
            },
            "required": [
                "assistantInstructions",
                "llm",
                "tools"
            ]
        },
        "backend": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string"
                },
                "version": {
                    "type": "string"
                },
                "buildDate": {
                    "type": "string"
                },
                "buildBranch": {
                    "type": "string"
                },
                "gitSHA": {
                    "type": "string"
                },
                "pythonVersion": {
                    "type": "string"
                },
                "dependencies": {
                    "type": "object"
                }
            },
            "required": [
                "description",
                "version",
                "buildDate",
                "buildBranch",
                "gitSHA",
                "pythonVersion",
                "dependencies"
            ]
        }
    },
    "required": [
        "ontologies",
        "datasets",
        "graphdb",
        "agent",
        "backend"
    ]
}
```

Sample Response Body:

```json
{
  "ontologies": [
    {
      "uri": "https://ap-voc.cim4.eu/AssessedElement#Ontology",
      "name": "Assessed Element Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/Assets#Ontology",
      "name": "Asset Vocabulary",
      "date": "2025-08-14",
      "version": "2.0.0"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/AssetCatalogue#Ontology",
      "name": "AssetCatalogue Vocabulary",
      "date": "2025-08-14",
      "version": "2.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/AvailabilitySchedule#Ontology",
      "name": "Availability schedule vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/Contingency#Ontology",
      "name": "Contingency Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/CoreEquipment-EU#Ontology",
      "name": "Core Equipment Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/DatasetMetadata#Ontology",
      "name": "Dataset metadata vocabulary",
      "date": "2024-09-07",
      "version": "2.4.0"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/DiagramLayout-EU#Ontology",
      "name": "Diagram Layout Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/DocumentHeader#Ontology",
      "name": "Document header vocabulary",
      "date": "2024-09-07",
      "version": "2.3.4"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/Dynamics-EU#Ontology",
      "name": "Dynamics Vocabulary",
      "date": "2020-10-12",
      "version": "1.0.0"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/EquipmentBoundary-EU#Ontology",
      "name": "Equipment Boundary Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/EquipmentReliability#Ontology",
      "name": "Equipment Reliability Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/GeographicalLocation-EU#Ontology",
      "name": "Geographical Location Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/GridDisturbance#Ontology",
      "name": "Grid Disturbance vocabulary",
      "date": "2024-09-07",
      "version": "1.1.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/ImpactAssessmentMatrix#Ontology",
      "name": "Impact Assessment Matrix Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/MonitoringArea#Ontology",
      "name": "Monitoring area Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/ObjectRegistry#Ontology",
      "name": "Object Registry vocabulary",
      "date": "2024-09-07",
      "version": "2.2.3"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/Operation-EU#Ontology",
      "name": "Operation Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/PowerSystemProject#Ontology",
      "name": "Power System Project Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/PowerSchedule#Ontology",
      "name": "Power schedule vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/RemedialActionSchedule#Ontology",
      "name": "Remedial Action Schedule Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/RemedialAction#Ontology",
      "name": "Remedial action Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/SecurityAnalysisResult#Ontology",
      "name": "Security Analysis Result Vocabulary",
      "date": "2024-09-07",
      "version": "2.4"
    },
    {
      "uri": "https://ap-voc.cim4.eu/SensitivityMatrix#Ontology",
      "name": "Sensitivity Matrix Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/ShortCircuit-EU#Ontology",
      "name": "Short Circuit Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/StateVariables-EU#Ontology",
      "name": "State Variables Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/StateInstructionSchedule#Ontology",
      "name": "State instruction schedule vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "https://ap-voc.cim4.eu/SteadyStateHypothesisSchedule#Ontology",
      "name": "Steady State Hypothesis Schedule Vocabulary",
      "date": "2024-09-07",
      "version": "1.0.1"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/SteadyStateHypothesis-EU#Ontology",
      "name": "Steady State Hypothesis Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://ap-voc.cim4.eu/SteadyStateInstruction#Ontology",
      "name": "Steady state instruction Vocabulary",
      "date": "2024-09-07",
      "version": "2.3.1"
    },
    {
      "uri": "http://iec.ch/TC57/ns/CIM/Topology-EU#Ontology",
      "name": "Topology Vocabulary",
      "date": "2020-10-12",
      "version": "3.0.0"
    },
    {
      "uri": "https://cim.ucaiug.io/rules#",
      "name": "CIM Inferred Extension Ontology",
      "date": "2025-08-13",
      "version": "1.1"
    }
  ],
  "datasets": [
    {
      "uri": "urn:uuid:eb4d92e6-d4da-11e7-9296-cec278b6b50a",
      "name": "Asset (AS) records for Statnett as asset owner in the enterprise part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.Nordic CPMSM Test model Asset.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:ade44b65-0bfa-41e0-95c5-2ccb345a6fed",
      "name": "Asset Catalogue (AC) from Schneider included in the enterprise part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:75f351c7-75a6-4c25-8f1c-985aa59e90ad",
      "name": "Asset Catalogue (AC) from Siemens Energy included in the enterprise part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:d9a01a85-0ad8-4958-be03-d89ad78ca497",
      "name": "Common Data (CD) included in Network Code part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:84552e03-0040-43d5-aff2-0f77f01668cb",
      "name": "Contingency (CO) included in Network Code part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:f4c70c71-77e2-410e-9903-cbd85305cdc4",
      "name": "DIGIN10 CGMES v3.0 Base Voltage Reference model",
      "date": "2022-04-06"
    },
    {
      "uri": "urn:uuid:5ad50f29-f3e5-4cf9-8519-cef17d71f8de",
      "name": "DIGIN10 CGMES v3.0 Geographical Region Reference model",
      "date": "2022-04-01"
    },
    {
      "uri": "urn:uuid:b39e7379-a9ae-4262-98dc-9ade1200adb0",
      "name": "DIGIN10 CGMES v3.0 High Voltage 1 (HV1) Medium Voltage 1 (MV1) Boundary Model",
      "date": "2022-04-06"
    },
    {
      "uri": "urn:uuid:c47d4310-b8ee-480d-9cf3-e53a81630981",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Core Equipment (EQ) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:596d41fa-11d3-41da-b231-e05724325e9b",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Customer (CU) Modele",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:02c12c37-ced0-4cbd-8fc2-4b51b0c532a6",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Diagram Layout (DL) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:c47d4310-b8ee-480d-9cf3-e53a81630981",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Equipment Operation (OP) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:50ae854b-afb8-4d42-bd4b-e97f1ee1ca6f",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Equipment Short-Circuit (SC) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:9552dc72-0525-4a84-8532-81f160b8fb74",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Geograpical Location (GL) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:2e4ac4ff-692d-48e5-9837-cc0db61ee3dd",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Object Reference (OR) Model",
      "date": "2022-04-11"
    },
    {
      "uri": "urn:uuid:a529556e-aa95-4b28-b729-e9114f90880a",
      "name": "DIGIN10 CGMES v3.0 Low Voltage 1 (LV1) Steady State Hypothesis (SSH) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:d12e4546-e6a5-4211-a4c8-877ac1e24d16",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Core Equipment (EQ) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:5f21a6a1-1d98-45f0-89f1-e4d7aa34691a",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Customer (CU) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:1399ce7d-e052-4714-954a-a17c7d6b4073",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Diagram Layout (DL) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:31b9fe89-c729-4bb3-9f6c-22f885607731",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Equipment Operationa (OP) Model",
      "date": "2022-10-28"
    },
    {
      "uri": "urn:uuid:9f36f713-b4d4-40a6-809f-9c342c3110ce",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Equipment Short-Circuit (SC) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:99790ba1-4bb2-4960-ade7-34d245740654",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Geographical layout (GL) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:f4c70c71-77e2-410e-9903-cbd85305cdc4",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Low Voltage 1 (LV1) Boundary Model",
      "date": "2022-04-06"
    },
    {
      "uri": "urn:uuid:f19668c6-e0a1-4db7-bfee-7645392d0021",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) Steady State Hypothesis (SSH) Model",
      "date": "2021-04-28"
    },
    {
      "uri": "urn:uuid:00db75c5-d443-42e5-927b-ca9a2e14fd48",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) and Low Voltage 1 (LV1) State Variable (SV) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:ef750ad6-a00c-4db3-b5c3-f849c096c2a5",
      "name": "DIGIN10 CGMES v3.0 Medium Voltage 1 (MV1) and Low Voltage 1 (LV1) Topology (TP) Model",
      "date": "2022-03-30"
    },
    {
      "uri": "urn:uuid:14a0302f-aaae-4abd-862f-7b0c86b4dca2",
      "name": "DIGIN10 Low Voltage 1 (LV1) Asset Model",
      "date": "2022-10-28"
    },
    {
      "uri": "urn:uuid:309fe4e7-d477-44e1-a495-de43562b3504",
      "name": "DIGIN10 Manufacture 1 (M1) Asset Catalogue Model",
      "date": "2022-10-28"
    },
    {
      "uri": "urn:uuid:7c2e25c9-331f-46f2-a4d4-d33c2e25d342",
      "name": "DIGIN10 Medium Voltage 1 (MV1) Asset Model",
      "date": "2022-10-28"
    },
    {
      "uri": "urn:uuid:ebef4527-f0bc-4c59-8870-950af8ed9041",
      "name": "Equipment Reliability (ER) included in Network Code part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:971c4254-5365-4aaf-8fa6-02658b3f8e05",
      "name": "Geospartial GridCapacity MAS1",
      "date": "2023-02-21"
    },
    {
      "uri": "urn:uuid:aca7b76a-77d9-42ce-bd34-67f4b12800f9",
      "name": "Measurement Value Source Reference data (RD) based on IEC 61970-301:2020+AMD1:2022",
      "date": "2022-10-24"
    },
    {
      "uri": "urn:uuid:9e3521e2-9504-4122-8c1e-a4c4411ffd7a",
      "name": "Remedial Action (RA) included in Network Code part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:3f3f00a8-b86a-4a3e-ab86-2cd3140fa187",
      "name": "Remedial Action Schedule (RAS) included in Network Code part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:ebe06a74-e44c-491f-bbfe-1cabb232828e",
      "name": "Steady State Instruction (SSI) included in Network Code part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:2e11908e-5e1f-8542-854c-54da76d379d1",
      "name": "Diagram Layout (DL) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:e710212f-f6b2-8d4c-9dc0-365398d8b59c",
      "name": "Equipment (EQ) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:67e97bb0-ec38-481d-9e56-3e9d45e95a33",
      "name": "Equipment Operation (OP) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:167b4832-27c5-ff4f-bd26-6ce3bff1bdb7",
      "name": "Geographical Location (GL) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:5b6a8b13-4c20-4147-8ed6-7249e303e647",
      "name": "State Variable (SV) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:1d08772d-c1d0-4c47-810d-b14908cd94f5",
      "name": "Steady-State Hypothesis (SSH) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    },
    {
      "uri": "urn:uuid:f1d9a88d-0ff5-4e4b-9d6a-c353fe8232c3",
      "name": "Telemark-120_AO",
      "date": "2024-02-06"
    },
    {
      "uri": "urn:uuid:7b3f94c0-bd9b-e74e-866b-f473153c3e70",
      "name": "Topological (TP) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "date": "2025-02-14"
    }
  ],
  "graphdb": {
    "baseUrl": "https://cim.ontotext.com/graphdb",
    "repository": "cim",
    "version": "11.1.1+sha.82602bfa",
    "numberOfExplicitTriples": 122948,
    "numberOfTriples": 323308,
    "autocompleteIndexStatus": "READY",
    "rdfRankStatus": "COMPUTED"
  },
  "agent": {
    "assistantInstructions": "Role & Objective:\n  You are a natural language querying assistant. Your goal is to answer users' questions related to electricity data, including:\n    - A power grid model\n    - Time-series data for power generation and consumption, and electricity prices. The timestamps for the time series data are in UTC time zone, while the user may be in a different time zone, so always assume the time periods are relative to the user's time.\n\nGeneral Reasoning Flow:\n  1. Check Relevance:\n    - Determine if the question is within the scope of the dataset.\n    - If it is out of scope, clearly inform the user (e.g., “That type of data is not available in the current dataset.”).\n  2. Entity Recognition and Resolution:\n    - Determine if the question refers to one or more named entities from the dataset.\n    - If it does, use the `autocomplete_search_tool` to retrieve their IRIs. Always use their IRIs in SPARQL queries; never refer to named entities by name in the SPARQL queries.\n    - Exception - do not use the `autocomplete_search_tool`, when an entity is referred by identifier. Valid identifiers are:\n      - EIC (Energy Identification Code)- always 16 characters, can include uppercase letters, numbers and hyphens, examples: \"10YNO-1--------2\", \"\"50Y73EMZ34CQL9AJ\"; use the predicate: `eu:IdentifiedObject.energyIdentCodeEic` to find the IRI and the class of the entity.\n      - full mRID - always 36 hexadecimal characters, 5 blocks of hexadecimal digits separated by hyphens, example: `f1769d10-9aeb-11e5-91da-b8763fd99c5f`; use the predicate: `cim:IdentifiedObject.mRID` to find the IRI and the class of the entity.\n      - significant part of the mRID - 8 hexadecimal characters, example: `f1769d10`; use the predicate: `cimr:mridSignificantPart` to find the IRI and the class of the entity.\n    In order to validate whether or not a sequence is a valid identifier, you must always use the `sparql_query` to find the entity and the entity class.\n    If the query returns no results, this means that this is a number sequence, and not a valid entity identifier.\n    This means you are mistaken, and should proceed with the next steps.\n\nSPARQL queries guidance:\n  - Use only the classes and properties provided in the schema and don't invent or guess any.\n  - Literal datatypes are significant. In SPARQL, when you compare a literal value (like a number or a date), its datatype is extremely important.\n  If the datatype is not specified or is incorrect, the query will likely fail to return results.\n  The ontology schema given below explicitly defines the expected datatype for properties using `rdfs:range`. \n  You must always consult the `rdfs:range` of the predicate involved in a literal comparison and ensure the literal in your SPARQL query uses the matching `xsd:dataType`.\n  Rule for Literals:\n    * Strings: Use double quotes, optionally with a language tag (e.g., \"hello\"@en). If no language tag, it's typically treated as `xsd:string`.\n    * Numbers, Booleans, Dates, etc.: These must be wrapped in double quotes and explicitly typed using ^^xsd:dataType.\n  Common xsd:dataType examples:\n    * `xsd:integer` (e.g., \"123\"^^xsd:integer)\n    * `xsd:float` (e.g., \"123.0\"^^xsd:float, \"123\"^^xsd:float)\n    * `xsd:double` (e.g., \"1.23\"^^xsd:double)\n    * `xsd:decimal` (e.g., \"1.23\"^^xsd:decimal)\n    * `xsd:boolean` (e.g., \"true\"^^xsd:boolean, \"false\"^^xsd:boolean)\n    * `xsd:dateTime` (e.g., \"2025-06-18T10:00:00Z\"^^xsd:dateTime)\n    * `xsd:date` (e.g., \"2025-06-18\"^^xsd:date)\n  Literal term equality: Two literals are term-equal (the same RDF literal) if and only if the two lexical forms, the two datatype IRIs, and the two language tags (if any) compare equal, character by character. \n  Thus, two literals can have the same value without being the same RDF term. For example:\n    \"1\"^^xs:integer\n    \"01\"^^xs:integer\n  denote the same value, but are not the same literal RDF terms and are not term-equal because their lexical form differs.\n  Hence, you must always use this pattern, when comparing literals \n    ``\n      ?subject ?predicate ?object.\n      FILTER (?object = <value-with-xsd-datatype>)\n    ``\n\nThe ontology schema to use in SPARQL queries is:\n\n```turtle\n{ontology_schema}\n```\n\nPay special attention to ``cims:pragmatics`` from the ontology schema. You can find practical information for the classes and properties.\nAlso, for some predicates you can find the unique object values for this predicate (``skos:example`` also gives all possible values).\n",
    "llm": {
      "type": "azure_openai",
      "model": "gpt-4.1",
      "temperature": 0,
      "seed": 1
    },
    "tools": {
      "sparql_query": {
        "enabled": true
      },
      "display_graphics": {
        "enabled": true,
        "sparql_query_template": "PREFIX dct: <http://purl.org/dc/terms/>\nPREFIX cimd: <https://cim.ucaiug.io/diagrams#>\nPREFIX cim: <https://cim.ucaiug.io/ns#>\nSELECT ?link ?name ?description ?format {{\n    <{iri}> cimd:Diagram.link ?link;\n        cim:IdentifiedObject.name ?name;\n        cim:IdentifiedObject.description ?description;\n        dct:format ?format.\n}}"
      },
      "autocomplete_search": {
        "enabled": true,
        "property_path": "<https://cim.ucaiug.io/ns#IdentifiedObject.name> | <https://cim.ucaiug.io/ns#IdentifiedObject.aliasName> | <https://cim.ucaiug.io/ns#CoordinateSystem.crsUrn>",
        "sparql_query_template": "PREFIX sesame: <http://www.openrdf.org/schema/sesame#>\nPREFIX rank: <http://www.ontotext.com/owlim/RDFRank#>\nPREFIX auto: <http://www.ontotext.com/plugins/autocomplete#>\nSELECT ?iri ?name ?class ?rank {{\n    ?iri auto:query \"{query}\" ;\n        {property_path} ?name ;\n        {filter_clause}\n        sesame:directType ?class;\n        rank:hasRDFRank5 ?rank.\n}}\nORDER BY DESC(?rank)\nLIMIT {limit}\n"
      },
      "sample_sparql_queries": {
        "enabled": true,
        "sparql_query_template": "PREFIX retr: <http://www.ontotext.com/connectors/retrieval#>\nPREFIX retr-index: <http://www.ontotext.com/connectors/retrieval/instance#>\nPREFIX qa: <https://www.statnett.no/Talk2PowerSystem/qa#>\nSELECT (REPLACE(GROUP_CONCAT(?q; separator=\"@\"), \"(.*?)@.*\", \"$1\") AS ?question) ?query {{\n    SELECT ?q ?query ?score {{\n        [] a retr-index:{connector_name} ;\n            retr:query \"{query}\" ;\n            retr:limit 100;\n            retr:entities ?entity .\n        ?entity retr:score ?score;\n            qa:question ?q.\n        ?template qa:paraphrase ?entity;\n            qa:querySparql ?query.\n        FILTER (?score > {score})\n    }}\n    ORDER BY DESC(?score)\n}}\nGROUP BY ?query\nLIMIT {limit}\n",
        "connector_name": "qa_dataset"
      },
      "retrieve_data_points": {
        "enabled": true,
        "base_url": "https://statnett.cognitedata.com",
        "project": "prod",
        "client_name": "talk2powersystem"
      },
      "retrieve_time_series": {
        "enabled": true,
        "base_url": "https://statnett.cognitedata.com",
        "project": "prod",
        "client_name": "talk2powersystem"
      },
      "now": {
        "enabled": true
      }
    }
  },
  "backend": {
    "description": "Talk2PowerSystem Chat Bot Application provides functionality for chatting with the Talk2PowerSystem Chat bot",
    "version": "1.3.1-dev0",
    "buildDate": "2025-10-31T18:50:01Z",
    "buildBranch": "Statnett-256",
    "gitSHA": "616b060d985a461b28c5455f94d7c4629e5d5fec",
    "pythonVersion": "3.12.12 | packaged by conda-forge | (main, Oct 22 2025, 23:25:55) [GCC 14.3.0]",
    "dependencies": {
      "ttyg": "3.0.0",
      "graphrag-eval": "5.3.1",
      "jupyter": "1.1.1",
      "langchain-openai": "1.1.0",
      "langgraph-checkpoint-redis": "0.2.1",
      "jsonlines": "4.0.0",
      "cognite-sdk": "7.90.1",
      "pydantic-settings": "2.12.0",
      "PyYAML": "6.0.3",
      "uvicorn[standard]": "0.38.0",
      "fastapi": "0.123.4",
      "APScheduler": "3.11.1",
      "toml": "0.10.2",
      "markdown": "3.10",
      "python-jose[cryptography]": "3.5.0",
      "cachetools": "6.2.2",
      "importlib_resources": "6.5.2"
    }
  }
}
```

The `ontologies`, `datasets` and `graphdb` sections are updated on a scheduled basis (30 seconds by default). The `agent` and `backend` sections are static and initialized at the start of the application, since the data don't change at run time.
The SPARQL query, which fetches the `ontologies` data is
```
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?uri ?name ?date ?version {
    ?uri a owl:Ontology.
    OPTIONAL {
        ?uri rdfs:label ?name
    }
    OPTIONAL {
        ?uri dct:title ?name
    }
    OPTIONAL {
        ?uri owl:versionInfo ?version
    }
    OPTIONAL {
        ?uri dct:modified ?date
    }
}
ORDER BY ?name
```
The SPARQL query, which fetches the `datasets` data is
```
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?uri ?name ?date {
    ?uri a dcat:Dataset
    OPTIONAL {
        ?uri dct:description ?name.
        FILTER(lang(?name) != "no")
    }
    OPTIONAL {
        ?uri dct:title ?name.
    }
    OPTIONAL {
        SELECT ?uri (SAMPLE(SUBSTR(STR(?dateTime), 1, 10)) AS ?date) {
            ?uri a dcat:Dataset;
            dct:issued ?dateTime
        }
        GROUP BY ?uri
    }
}
ORDER BY ?name
```
The number of triples and explicit triples as well as GraphDB version are collected with the following SPARQL query
```
PREFIX onto: <http://www.ontotext.com/>

DESCRIBE onto:SYSINFO
FROM onto:SYSINFO
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
* OpenID, Microsoft Entra ID
* Redis

## Resolving Known Issues

### Issues

#### GraphDB health check status is not OK

Most probable cause: ["GraphDB can't be queried or is mis-configured"](#graphdb-cant-be-queried-or-is-mis-configured)

#### Calls made by the LLM agent to the tools `sparql_query`, `autocomplete_search`, `retrieval_search` are failing

Most probable cause: ["GraphDB can't be queried or is mis-configured"](#graphdb-cant-be-queried-or-is-mis-configured)

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
- Make sure GraphDB credentials are correct. The application needs read access.
- Make sure GraphDB timeouts are configured correctly according to the network performance.
- Make sure [GraphDB autocomplete index status](https://graphdb.ontotext.com/documentation/11.0/autocomplete-index.html) is `READY`.
- Make sure [GraphDB RDF rank](https://graphdb.ontotext.com/documentation/10.0/rdf-rank.html) is computed and up-to-date. The status must be `COMPUTED`.

##### Verification

- Check the response status code of the `__gtg` endpoint, it must be `200`.
- Check the response body of the `__health` endpoint, GraphDB health check must have status `OK`.

#### Cognite can't be queried or is mis-configured

##### Solution

- Make sure Cognite is reachable from the app host.
- Make sure the application security is enabled, otherwise Cognite won't be accessible.
- Make sure that in the application configuration in Azure `user impersonation` for Cognite is set under API permissions and is approved.
- Make sure the property `tools.cognite.client_secret` is set and has a correct value. To create / obtain it you (or your Azure admin) must:
    1. Go to the Azure Portal → Microsoft Entra ID → App registrations → Your FastAPI Backend App
    2. In the left menu, choose Certificates & secrets
    3. Under Client secrets, click ➕ New client secret
    4. Give it a description and choose an expiry (6 months, 12 months, custom)
    5. Click Add
    Azure will show you:
        - Value – this is your actual secret (copy it now → you can’t view it later)
        - Secret ID – an internal reference (not needed in code)

##### Verification

Users no longer report that the calls made by the LLM agent to the tools `retrieve_time_series`, `retrieve_data_points` are failing.

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
If it does, in the application logs there will be messages containing `429 Too Many Requests`. If this is the case, the rate limits must be increased. 
- Make sure the number of uvicorn [workers](https://fastapi.tiangolo.com/deployment/server-workers/) is configured according to the number of parallel users of the system.

##### Verification

Users no longer report slow responses
