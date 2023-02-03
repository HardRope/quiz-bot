import redis

def get_database_connection():
    global database
    if database is None:
        database = redis.Redis(
            host=env('REDiS_HOST'),
            port=env('REDIS_PORT'),
            password=env('REDIS_PASSWORD'),
            decode_responses=True,
        )
    return database
