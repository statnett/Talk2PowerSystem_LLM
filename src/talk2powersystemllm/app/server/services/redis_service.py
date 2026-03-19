from redis.asyncio import Redis, RedisCluster


def create_redis_client(settings) -> Redis | RedisCluster:
    redis_password = settings.redis.password
    redis_auth = ""
    if redis_password:
        redis_auth = f"{settings.redis.username}:{redis_password.get_secret_value()}@"
    redis_url = f"redis://{redis_auth}{settings.redis.host}:{settings.redis.port}"
    connection_kwargs = {
        "socket_connect_timeout": settings.redis.connect_timeout,
        "socket_timeout": settings.redis.read_timeout,
        "health_check_interval": settings.redis.healthcheck_interval,
    }
    if settings.redis.is_a_cluster:
        return RedisCluster.from_url(
            redis_url,
            **connection_kwargs,
        )
    else:
        return Redis.from_url(
            redis_url,
            **connection_kwargs,
        )
