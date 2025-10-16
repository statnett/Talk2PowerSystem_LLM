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
  "clientId": "6f8c5e30-b4b4-4b78-bdba-0ac5f5947fb6",
  "authority": "https://login.microsoftonline.com/519ed184-e4d5-4431-97e5-fb4410a3f875",
  "logout": "https://login.microsoftonline.com/519ed184-e4d5-4431-97e5-fb4410a3f875/oauth2/logout",
  "loginRedirect": "http://localhost:3000",
  "logoutRedirect": "http://localhost:3000/login"
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
      "name": "Assessed Element Vocabulary",
      "uri": "https://ap-voc.cim4.eu/AssessedElement#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Asset Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/Assets#Ontology",
      "version": "2.0.0",
      "date": "2025-08-14"
    },
    {
      "name": "AssetCatalogue Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/AssetCatalogue#Ontology",
      "version": "2.0.0",
      "date": "2025-08-14"
    },
    {
      "name": "Availability schedule vocabulary",
      "uri": "https://ap-voc.cim4.eu/AvailabilitySchedule#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Contingency Vocabulary",
      "uri": "https://ap-voc.cim4.eu/Contingency#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Core Equipment Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/CoreEquipment-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Dataset metadata vocabulary",
      "uri": "https://ap-voc.cim4.eu/DatasetMetadata#Ontology",
      "version": "2.4.0",
      "date": "2024-09-07"
    },
    {
      "name": "Diagram Layout Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/DiagramLayout-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Document header vocabulary",
      "uri": "https://ap-voc.cim4.eu/DocumentHeader#Ontology",
      "version": "2.3.4",
      "date": "2024-09-07"
    },
    {
      "name": "Dynamics Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/Dynamics-EU#Ontology",
      "version": "1.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Equipment Boundary Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/EquipmentBoundary-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Equipment Reliability Vocabulary",
      "uri": "https://ap-voc.cim4.eu/EquipmentReliability#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Geographical Location Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/GeographicalLocation-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Grid Disturbance vocabulary",
      "uri": "https://ap-voc.cim4.eu/GridDisturbance#Ontology",
      "version": "1.1.1",
      "date": "2024-09-07"
    },
    {
      "name": "Impact Assessment Matrix Vocabulary",
      "uri": "https://ap-voc.cim4.eu/ImpactAssessmentMatrix#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Monitoring area Vocabulary",
      "uri": "https://ap-voc.cim4.eu/MonitoringArea#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Object Registry vocabulary",
      "uri": "https://ap-voc.cim4.eu/ObjectRegistry#Ontology",
      "version": "2.2.3",
      "date": "2024-09-07"
    },
    {
      "name": "Operation Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/Operation-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Power System Project Vocabulary",
      "uri": "https://ap-voc.cim4.eu/PowerSystemProject#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Power schedule vocabulary",
      "uri": "https://ap-voc.cim4.eu/PowerSchedule#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Remedial Action Schedule Vocabulary",
      "uri": "https://ap-voc.cim4.eu/RemedialActionSchedule#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Remedial action Vocabulary",
      "uri": "https://ap-voc.cim4.eu/RemedialAction#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Security Analysis Result Vocabulary",
      "uri": "https://ap-voc.cim4.eu/SecurityAnalysisResult#Ontology",
      "version": "2.4",
      "date": "2024-09-07"
    },
    {
      "name": "Sensitivity Matrix Vocabulary",
      "uri": "https://ap-voc.cim4.eu/SensitivityMatrix#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Short Circuit Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/ShortCircuit-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "State Variables Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/StateVariables-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "State instruction schedule vocabulary",
      "uri": "https://ap-voc.cim4.eu/StateInstructionSchedule#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Steady State Hypothesis Schedule Vocabulary",
      "uri": "https://ap-voc.cim4.eu/SteadyStateHypothesisSchedule#Ontology",
      "version": "1.0.1",
      "date": "2024-09-07"
    },
    {
      "name": "Steady State Hypothesis Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/SteadyStateHypothesis-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "Steady state instruction Vocabulary",
      "uri": "https://ap-voc.cim4.eu/SteadyStateInstruction#Ontology",
      "version": "2.3.1",
      "date": "2024-09-07"
    },
    {
      "name": "Topology Vocabulary",
      "uri": "http://iec.ch/TC57/ns/CIM/Topology-EU#Ontology",
      "version": "3.0.0",
      "date": "2020-10-12"
    },
    {
      "name": "CIM Inferred Extension Ontology",
      "uri": "https://cim.ucaiug.io/rules#",
      "version": "1.1",
      "date": "2025-08-13"
    }
  ],
  "datasets": [
    {
      "name": "20160101_N44-ENT-Schneider_AC_v3-0-0-beta-1",
      "uri": "urn:uuid:ade44b65-0bfa-41e0-95c5-2ccb345a6fed",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-ENT-Siemens_AC_v3-0-0-beta-1",
      "uri": "urn:uuid:75f351c7-75a6-4c25-8f1c-985aa59e90ad",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-ENT-Statnett_AS_v3-0-0-beta-1",
      "uri": "urn:uuid:eb4d92e6-d4da-11e7-9296-cec278b6b50a",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-NC-HV_CD_v3-0-0-beta-1",
      "uri": "urn:uuid:d9a01a85-0ad8-4958-be03-d89ad78ca497",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-NC-HV_CO_v3-0-0-beta-1",
      "uri": "urn:uuid:84552e03-0040-43d5-aff2-0f77f01668cb",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-NC-HV_ER_v3-0-0-beta-1",
      "uri": "urn:uuid:ebef4527-f0bc-4c59-8870-950af8ed9041",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-NC-HV_RAS_v3-0-0-beta-1",
      "uri": "urn:uuid:3f3f00a8-b86a-4a3e-ab86-2cd3140fa187",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-NC-HV_RA_v3-0-0-beta-1",
      "uri": "urn:uuid:9e3521e2-9504-4122-8c1e-a4c4411ffd7a",
      "date": "2025-02-14"
    },
    {
      "name": "20160101_N44-NC-HV_SSI_v3-0-0-beta-1",
      "uri": "urn:uuid:ebe06a74-e44c-491f-bbfe-1cabb232828e",
      "date": "2025-02-14"
    },
    {
      "name": "DIGIN10-30-BaseVoltage_RD",
      "uri": "urn:uuid:f4c70c71-77e2-410e-9903-cbd85305cdc4",
      "date": "2022-04-01"
    },
    {
      "name": "DIGIN10-30-GeographicalRegion_RD",
      "uri": "urn:uuid:5ad50f29-f3e5-4cf9-8519-cef17d71f8de",
      "date": "2022-04-01"
    },
    {
      "name": "DIGIN10-30-HV1-MV1_BM",
      "uri": "urn:uuid:b39e7379-a9ae-4262-98dc-9ade1200adb0",
      "date": "2022-04-06"
    },
    {
      "name": "DIGIN10-30-LV1_AS",
      "uri": "urn:uuid:14a0302f-aaae-4abd-862f-7b0c86b4dca2",
      "date": "2022-10-28"
    },
    {
      "name": "DIGIN10-30-LV1_CU",
      "uri": "urn:uuid:596d41fa-11d3-41da-b231-e05724325e9b",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-LV1_DL",
      "uri": "urn:uuid:02c12c37-ced0-4cbd-8fc2-4b51b0c532a6",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-LV1_EQ",
      "uri": "urn:uuid:c47d4310-b8ee-480d-9cf3-e53a81630981",
      "date": "2022-10-28"
    },
    {
      "name": "DIGIN10-30-LV1_GL",
      "uri": "urn:uuid:9552dc72-0525-4a84-8532-81f160b8fb74",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-LV1_OP",
      "uri": "urn:uuid:c47d4310-b8ee-480d-9cf3-e53a81630981",
      "date": "2022-10-28"
    },
    {
      "name": "DIGIN10-30-LV1_OR",
      "uri": "urn:uuid:2e4ac4ff-692d-48e5-9837-cc0db61ee3dd",
      "date": "2022-04-11"
    },
    {
      "name": "DIGIN10-30-LV1_SC",
      "uri": "urn:uuid:50ae854b-afb8-4d42-bd4b-e97f1ee1ca6f",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-LV1_SSH",
      "uri": "urn:uuid:a529556e-aa95-4b28-b729-e9114f90880a",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-M1_AC",
      "uri": "urn:uuid:309fe4e7-d477-44e1-a495-de43562b3504",
      "date": "2022-10-28"
    },
    {
      "name": "DIGIN10-30-MV1-LV1_BM",
      "uri": "urn:uuid:f4c70c71-77e2-410e-9903-cbd85305cdc4",
      "date": "2022-04-01"
    },
    {
      "name": "DIGIN10-30-MV1-LV1_SV",
      "uri": "urn:uuid:00db75c5-d443-42e5-927b-ca9a2e14fd48",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1-LV1_TP",
      "uri": "urn:uuid:ef750ad6-a00c-4db3-b5c3-f849c096c2a5",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1_AS",
      "uri": "urn:uuid:7c2e25c9-331f-46f2-a4d4-d33c2e25d342",
      "date": "2022-10-28"
    },
    {
      "name": "DIGIN10-30-MV1_CU",
      "uri": "urn:uuid:5f21a6a1-1d98-45f0-89f1-e4d7aa34691a",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1_DL",
      "uri": "urn:uuid:1399ce7d-e052-4714-954a-a17c7d6b4073",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1_EQ",
      "uri": "urn:uuid:d12e4546-e6a5-4211-a4c8-877ac1e24d16",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1_GL",
      "uri": "urn:uuid:99790ba1-4bb2-4960-ade7-34d245740654",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1_OP",
      "uri": "urn:uuid:31b9fe89-c729-4bb3-9f6c-22f885607731",
      "date": "2022-10-28"
    },
    {
      "name": "DIGIN10-30-MV1_SC",
      "uri": "urn:uuid:9f36f713-b4d4-40a6-809f-9c342c3110ce",
      "date": "2022-03-30"
    },
    {
      "name": "DIGIN10-30-MV1_SSH",
      "uri": "urn:uuid:f19668c6-e0a1-4db7-bfee-7645392d0021",
      "date": "2021-04-28"
    },
    {
      "name": "DIGIN10-30-MeasurementValueSource_RD",
      "uri": "urn:uuid:aca7b76a-77d9-42ce-bd34-67f4b12800f9",
      "date": "2022-10-24"
    },
    {
      "name": "DIGIN10-30-WattApp-GL",
      "uri": "urn:uuid:971c4254-5365-4aaf-8fa6-02658b3f8e05",
      "date": "2023-02-21"
    },
    {
      "name": "Diagram Layout (DL) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:2e11908e-5e1f-8542-854c-54da76d379d1",
      "date": "2025-02-14"
    },
    {
      "name": "Equipment (EQ) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:e710212f-f6b2-8d4c-9dc0-365398d8b59c",
      "date": "2025-02-14"
    },
    {
      "name": "Equipment Operation (OP) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:67e97bb0-ec38-481d-9e56-3e9d45e95a33",
      "date": "2025-02-14"
    },
    {
      "name": "Geographical Location (GL) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:167b4832-27c5-ff4f-bd26-6ce3bff1bdb7",
      "date": "2025-02-14"
    },
    {
      "name": "State Variable (SV) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:5b6a8b13-4c20-4147-8ed6-7249e303e647",
      "date": "2025-02-14"
    },
    {
      "name": "Steady-State Hypothesis (SSH) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:1d08772d-c1d0-4c47-810d-b14908cd94f5",
      "date": "2025-02-14"
    },
    {
      "name": "Telemark-120_AO",
      "uri": "urn:uuid:f1d9a88d-0ff5-4e4b-9d6a-c353fe8232c3",
      "date": "2024-02-06"
    },
    {
      "name": "Topological (TP) part of the Nordic 44-bus synthetic test model developed by Statnett SF of the Nordic region.",
      "uri": "urn:uuid:7b3f94c0-bd9b-e74e-866b-f473153c3e70",
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
      "autocomplete_search": {
        "enabled": true,
        "property_path": "<https://cim.ucaiug.io/ns#IdentifiedObject.name> | <https://cim.ucaiug.io/ns#IdentifiedObject.aliasName> | <https://cim.ucaiug.io/ns#CoordinateSystem.crsUrn>",
        "sparql_query_template": "PREFIX sesame: <http://www.openrdf.org/schema/sesame#>\nPREFIX rank: <http://www.ontotext.com/owlim/RDFRank#>\nPREFIX auto: <http://www.ontotext.com/plugins/autocomplete#>\nSELECT ?iri ?name ?class ?rank {{\n    ?iri auto:query \"{query}\" ;\n        {property_path} ?name ;\n        {filter_clause}\n        sesame:directType ?class;\n        rank:hasRDFRank5 ?rank.\n}}\nORDER BY DESC(?rank)\nLIMIT {limit}\n"
      },
      "sample_sparql_queries": {
        "enabled": true,
        "sparql_query_template": "PREFIX retr: <http://www.ontotext.com/connectors/retrieval#>\nPREFIX retr-index: <http://www.ontotext.com/connectors/retrieval/instance#>\nPREFIX qa: <https://www.statnett.no/Talk2PowerSystem/qa#>\nSELECT ?question ?query {{\n    [] a retr-index:{connector_name} ;\n      retr:query \"{query}\" ;\n      retr:limit {limit} ;\n      retr:entities ?entity .\n    ?entity retr:score ?score;\n      qa:question ?question;\n      qa:sparql_query ?query.\n    FILTER (?score > {score})\n}}\nORDER BY DESC(?score)\n",
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
    "version": "1.1.0a0",
    "buildDate": "2024-01-09T13:31:49Z",
    "buildBranch": "COOL-BRANCH-NAME",
    "gitSHA": "a730751ac055a4f2dad3dc3e5658bb1bf30ff412",
    "pythonVersion": "3.12.11 | packaged by conda-forge | (main, Jun  4 2025, 14:45:31) [GCC 13.3.0]",
    "dependencies": {
      "ttyg": "1.9.0",
      "graphrag-eval": "5.1.2",
      "jupyter": "1.1.1",
      "langchain-openai": "0.3.32",
      "langgraph-checkpoint-redis": "0.1.1",
      "jsonlines": "4.0.0",
      "cognite-sdk": "7.86.0",
      "pydantic-settings": "2.10.1",
      "PyYAML": "6.0.2",
      "uvicorn[standard]": "0.35.0",
      "fastapi": "0.116.1",
      "toml": "0.10.2",
      "markdown": "3.8.2",
      "python-jose[cryptography]": "3.5.0",
      "cachetools": "6.2.0",
      "importlib_resources": "6.5.2"
    }
  }
}
```

The `ontologies`, `datasets` and `graphdb` sections are updated on a scheduled basis (30 seconds by default). The `agent` and `backend` sections are static and initialized at the start of the application, since the data don't change at run time.
The SPARQL query, which fetches the `ontologies` data is
```
PREFIX onto: <http://www.ontotext.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?uri ?name ?version ?date
FROM onto:explicit {
    ?uri a owl:Ontology.
    OPTIONAL {
        ?uri dct:title ?title
    }
    OPTIONAL {
        ?uri rdfs:label ?label
    }
    OPTIONAL {
        ?uri owl:versionInfo ?version
    }
    OPTIONAL {
        ?uri dct:modified ?date
    }
    BIND(COALESCE(?title, ?label) AS ?name)
}
ORDER BY ?name
```
The SPARQL query, which fetches the `datasets` data is
```
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX onto: <http://www.ontotext.com/>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT DISTINCT ?uri ?name ?date
FROM onto:explicit {
    ?uri a dcat:Dataset
    OPTIONAL {
        SELECT ?uri (SAMPLE(SUBSTR(STR(?dateTime), 1, 10)) AS ?date) {
            ?uri a dcat:Dataset;
            dct:issued ?dateTime
        }
        GROUP BY ?uri
    }
    OPTIONAL {
        ?uri dct:title ?title
    }
    OPTIONAL {
        ?uri dct:description ?descr
    }
    BIND(COALESCE(?title, ?descr) AS ?name)
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
If it does, in the application logs there will be messages containing `429 Too Many Requests`. If this is the case, the rate limits must be increased. 
- Make sure the number of uvicorn [workers](https://fastapi.tiangolo.com/deployment/server-workers/) is configured according to the number of parallel users of the system.

##### Verification

Users no longer report slow responses
