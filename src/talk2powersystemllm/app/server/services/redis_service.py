from redis.asyncio import Redis, RedisCluster

from talk2powersystemllm.app.server.config import RedisSettings


def create_redis_client(redis_settings: RedisSettings) -> Redis | RedisCluster:
    redis_password = redis_settings.password
    redis_auth = ""
    if redis_password:
        redis_auth = f"{redis_settings.username}:{redis_password.get_secret_value()}@"
    redis_url = f"redis://{redis_auth}{redis_settings.host}:{redis_settings.port}"
    connection_kwargs = {
        "socket_connect_timeout": redis_settings.connect_timeout,
        "socket_timeout": redis_settings.read_timeout,
        "health_check_interval": redis_settings.healthcheck_interval,
    }
    if redis_settings.is_a_cluster:
        return RedisCluster.from_url(
            redis_url,
            **connection_kwargs,
        )
    else:
        return Redis.from_url(
            redis_url,
            **connection_kwargs,
        )
