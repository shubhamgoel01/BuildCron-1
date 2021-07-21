from pymongo import MongoClient


def get_db_handle(connection_string, db_name):
    client = MongoClient(connection_string)
    db_handle = client[db_name]
    return db_handle
