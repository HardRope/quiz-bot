import redis

def get_database_connection(host, port, password):
    database = redis.Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
    )
    return database
