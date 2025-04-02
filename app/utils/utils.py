import pymongo
import logging
import requests
import streamlit as st

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_mongo_client():
    try:
        client = pymongo.MongoClient(st.secrets.mongo_secrets.uri)
        logging.info('MongoDB connection established successfully')
        return client
    except Exception as e:
        logging.error(f'Error connecting to MongoDB: {e}')

def get_documents(db_name:str, collection_name:str, query:dict={}):
    try:
        client     = get_mongo_client()
        db         = client[db_name]
        collection = db[collection_name]
        documents  = collection.find(query)

        return list(documents)
    except Exception as e:
        logging.error(f'Error getting documents from MongoDB: {e}')

def insert_document(db_name:str, collection_name:str, document:dict):
    try:
        client     = get_mongo_client()
        db         = client[db_name]
        collection = db[collection_name]
        collection.insert_one(document)

        logging.info(f'Document inserted successfully: {document}')
    except Exception as e:
        logging.error(f'Error inserting document into MongoDB: {e}')

def turn_on_pump():
    try:
        response = requests.get(st.secrets.app_config.trigger_on_url)

        if response.status_code == 200:
            logging.info("🟢 - Pump turned on")
            st.toast("Pump turned on", icon="🟢")
        else:
            logging.error(f"Error turning on device: {response}")
    except Exception as e:
        logging.error(f"Error turning on device: {e}")

def turn_off_pump():
    try:
        response = requests.get(st.secrets.app_config.trigger_off_url)

        if response.status_code == 200:
            logging.info("🔴 - Pump turned off")
            st.toast("Pump turned off", icon="🔴")
        else:
            logging.error(f"Error turning off device: {response}")
    except Exception as e:
        logging.error(f"Error turning off device: {e}")

def is_summer(datetime_obj):
    return datetime_obj.month in [6, 7, 8]