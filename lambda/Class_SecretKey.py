import requests
import os
import json

# Class : シークレットキーを取得する
class SecretKey():
  def get():
    secrets_extension_endpoint = "http://localhost:" + \
    secrets_extension_http_port + \
    "/secretsmanager/get?secretId=" + \
    "Amazon_PA-API"
    
    r = requests.get(secrets_extension_endpoint, headers=headers)
    
    secret = json.loads(r.text)["SecretString"]