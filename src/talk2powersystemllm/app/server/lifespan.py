import logging
from contextlib import asynccontextmanager

import msal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import (
    FastAPI,
)
from langgraph.checkpoint.redis import AsyncRedisSaver

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.app.server.config import settings
from talk2powersystemllm.app.server.services.healthchecks import (
    GraphDBHealthchecker,
    RedisHealthchecker,
    LLMHealthchecker,
)
from .services import create_redis_client


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    logging.info("Starting the application")

    async with (
        create_redis_client() as redis_client,
        AsyncRedisSaver.from_conn_string(
            redis_client=redis_client,
            ttl={
                "default_ttl": settings.redis.ttl,
                "refresh_on_read": settings.redis.ttl_refresh_on_read,
            }
        ) as redis_saver
    ):
        await redis_saver.asetup()
        RedisHealthchecker(redis_client)

        fastapi_app.state.callbacks = [LLMHealthchecker(redis_client)]

        agent_factory = Talk2PowerSystemAgentFactory(
            settings.agent_config,
            checkpointer=redis_saver,
        )
        fastapi_app.state.agent_factory = agent_factory

        GraphDBHealthchecker(agent_factory)

        if settings.security.enabled and agent_factory.settings.tools.cognite:
            if not agent_factory.settings.tools.cognite.client_secret:
                raise ValueError(
                    "Cognite client secret must be provided in order to register the Cognite tools, "
                    "when the security is enabled."
                )
            fastapi_app.state.confidential_app = msal.ConfidentialClientApplication(
                settings.security.client_id,
                authority=settings.security.authority,
                client_credential=agent_factory.settings.tools.cognite.client_secret,
            )
            fastapi_app.state.cognite_scopes = [f"{agent_factory.settings.tools.cognite.base_url}/.default"]

        scheduler = AsyncIOScheduler()
        scheduler.add_job(update_gtg_info, "interval", seconds=settings.gtg_refresh_interval)
        scheduler.add_job(update_about_info, "interval", seconds=settings.about_refresh_interval)

        scheduler.start()
        fastapi_app.state.scheduler = scheduler

        await update_gtg_info()
        await update_about_info()

        logging.info("Application is running")

        yield

        logging.info("Destroying the application")
        scheduler.shutdown()
        logging.info("Scheduler is stopped")
