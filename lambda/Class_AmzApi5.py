import json
import requests

import sys, os, base64, datetime, hashlib, hmac

import boto3
import botocore.exceptions

# Class : Amazon PA-API にリクエスト
class AmzAPi5():
    __config = {
        'content_encoding': 'amz-1.0',
        'content_type': 'application/json; charset=utf-8',
        'service': 'ProductAdvertisingAPI'
    }
    
    def __init__(self, access_key, secret_key):
        self.__access_key = access_key
        self.__secret_key = secret_key
        
    def set_region(self, region):
        self.__region = region
        
    def set_market_place(self, market_place):
        self.__market_place = market_place
        
    def set_partner_tag(self, partner_tag):
        self.__partner_tag = partner_tag
        
    def request_post(self, amz_target, endpoint, host, path, request_parameters):
        # Set Marketplace and PartnerTag
        request_parameters['Marketplace'] = self.__market_place
        request_parameters['PartnerTag'] = self.__partner_tag

        # ********************************************
        # Create Signature (AWS4-HMAC-SHA256)
        # ********************************************
        # Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
        #
        # This file is licensed under the Apache License, Version 2.0 (the "License").
        # You may not use this file except in compliance with the License. A copy of the
        # License is located at
        #
        # http://aws.amazon.com/apache2.0/
        #
        # This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
        # OF ANY KIND, either express or implied. See the License for the specific
        # language governing permissions and limitations under the License.
        #
        # Original Code : Example Using POST (Python) See:
        # https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html#sig-v4-examples-post
        # ********************************************
        
        # Key derivation functions. See:
        # http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        
        def getSignatureKey(key, dateStamp, regionName, serviceName):
            kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
            kRegion = sign(kDate, regionName)
            kService = sign(kRegion, serviceName)
            kSigning = sign(kService, 'aws4_request')
            return kSigning
        
        # Read AWS access key from env. variables or configuration file. Best practice is NOT
        # to embed credentials in code.
        access_key = self.__access_key
        secret_key = self.__secret_key
        if access_key is None or secret_key is None:
            print('No access key is available.')
            sys.exit()
            
        # Create a date for headers and the credential string
        t = datetime.datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
        
        # ************* TASK 1: CREATE A CANONICAL REQUEST *************
        # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
        
        # Step 1 is to define the verb (GET, POST, etc.)--already done.
        
        # Step 2: Create canonical URI--the part of the URI from domain to query 
        # string (use '/' if no path)
        canonical_uri = path
        
        ## Step 3: Create the canonical query string. In this example, request
        # parameters are passed in the body of the request and the query string
        # is blank.
        canonical_querystring = ''
        
        # Step 4: Create the canonical headers and signed headers. Header names
        # must be trimmed and lowercase, and sorted in code point order from
        # low to high. Note that there is a trailing \n.
        # Required fields : content-type, host, x-amz-date, x-amz-target,
        # https://webservices.amazon.co.jp/paapi5/documentation/sending-request.html#signing
        canonical_headers = 'content-type:' + self.__config['content_type'] + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n' + 'x-amz-target:' + amz_target + '\n'
        
        # Step 5: Create the list of signed headers. This lists the headers
        # in the canonical_headers list, delimited with ";" and in alpha order.
        # Note: The request can include any headers; canonical_headers and
        # signed_headers lists those that you want to be included in the 
        # hash of the request. "Host" and "x-amz-date" are always required.
        signed_headers = 'content-type;host;x-amz-date;x-amz-target'
        
        # Step 6: Create payload hash. In this example, the payload (body of
        # the request) contains the request parameters.
        request_parameters_dump = json.dumps(request_parameters)
        payload_hash = hashlib.sha256(request_parameters_dump.encode('utf-8')).hexdigest()
        
        # Step 7: Combine elements to create canonical request
        canonical_request = 'POST' + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
        
        # ************* TASK 2: CREATE THE STRING TO SIGN*************
        # Match the algorithm to the hashing algorithm you use, either SHA-1 or
        # SHA-256 (recommended)
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = date_stamp + '/' + self.__region + '/' + self.__config['service'] + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        
        # ************* TASK 3: CALCULATE THE SIGNATURE *************
        # Create the signing key using the function defined above.
        signing_key = getSignatureKey(self.__secret_key, date_stamp, self.__region, self.__config['service'])
        
        # Sign the string_to_sign using the signing_key
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
    
        # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
        # The signing information can be either in a query string value or in 
        # a header named Authorization. This code shows how to use a header.
        # Create authorization header and add to request headers
        authorization_header = algorithm + ' ' + 'Credential=' + self.__access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
        
        # ********************************************
        # Create Header
        headers = {
            'content-encoding': self.__config['content_encoding'],
            'content-type': self.__config['content_type'],
            'x-amz-date': amz_date,
            'x-amz-target': amz_target,
            'Authorization': authorization_header
        }
        
        print(authorization_header)
        
        # ************* SEND THE REQUEST *************
        r = requests.post(endpoint, data=json.dumps(request_parameters), headers=headers)
        return r
    