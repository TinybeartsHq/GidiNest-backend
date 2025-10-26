from json import dumps as json_dumps
from random import choice
from string import ascii_lowercase
import uuid
import os
from decouple import config
import boto3

class WriteJsonToFile:

    @staticmethod
    def unique_string():
        length = 5
        result = ''.join((choice(ascii_lowercase) for x in range(length)))
        return result

    @staticmethod
    def write_to_file(data):
        unique_id = WriteJsonToFile.unique_string()
        extra_id = str(uuid.uuid4())
        file_name = f'{extra_id}-{unique_id}.json'
        file_path = f'tmp/{file_name}'

        # Ensure the 'tmp/' directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as jsonf:
            json_string = json_dumps(data, indent=4)
            jsonf.write(json_string)
        
        return file_path, file_name

    @staticmethod
    def json_to_s3(data):

        bucket_name = config('AWS_STORAGE_BUCKET_NAME')
        folder_name = "credit_analysis/response"

        file_path, file_name = WriteJsonToFile.write_to_file(data)

        client = boto3.client('s3')

        # Construct the file path by adding the folder name before the file name
        s3_file_path = f"{folder_name}/{file_name}"

        with open(file_path, 'rb') as file:
            client.upload_fileobj(
                file,
                bucket_name,
                s3_file_path
            )
        
        return f"https://{bucket_name}.s3.amazonaws.com/{s3_file_path}"