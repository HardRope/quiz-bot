import redis

def get_database_connection(host, port, password):
    global database
    if database is None:
        database = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True,
        )
    return database
