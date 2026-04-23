import os

USE_RESPONSES_API = os.getenv("LLM_USE_RESPONSES_API", "false").lower() == "true"
