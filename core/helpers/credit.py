import json


def extract_credit_data_key(json_data,key):
    data = json_data
    for item in data:
        if key in item:
            return item[key]
    return None

