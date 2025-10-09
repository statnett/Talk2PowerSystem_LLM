import contextvars

user_datetime_ctx = contextvars.ContextVar("user_datetime_ctx", default=None)
