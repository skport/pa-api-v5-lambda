import json
import requests

import sys, os, base64, datetime, hashlib, hmac

import boto3
import botocore.exceptions

# Class : キャッシュ運用 (S3)
class ManageCache():
    __config = {
        # オブジェクトの拡張子
        'ext': '.json'
    }
    
    def __init__(self, bucket_name):
        self.__bucket_name = bucket_name
        self.init_bucket()
        
    def init_bucket(self):
        self.__client = boto3.client('s3')
        
    def create_object_key(self, body):
        # Convert SHA-1
        key = hashlib.sha1(body.encode('utf-8')).hexdigest();
        
        # Create Folder Name
        folder_name = key[0]
        
        # Join Key & ext
        return folder_name + '/' + key + self.__config['ext']
    
    # 指定のオブジェクトキーで内容を保存
    # エラーが起きた際は False を返す
    def put(self, key, body):
        r = self.__client.put_object(
                Bucket = self.__bucket_name,
                Key = key,
                Body = body
            )
        return r
    
    # 指定のオブジェクトキーの内容を取得
    # エラーが起きた際は False を返す
    def get(self, key):
        try:
            r = self.__client.get_object(
                    Bucket = self.__bucket_name,
                    Key = key
                )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(e.response['Error'])
            else:
                raise
            return False
        return r
        
    # 指定のオブジェクトキーを削除
    # エラーが起きた際は False を返す
    def delete(self, key):
        try:
            r = self.__client.delete_object(
                    Bucket = self.__bucket_name,
                    Key = key
                )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(e.response['Error'])
            else:
                raise
            return False
        return r
        
    # レスポンスの内容からボディを返す
    def read(self, r):
        body = r['Body'].read().decode('utf-8')
        return body