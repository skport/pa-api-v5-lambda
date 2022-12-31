import json
import sys, os, base64, datetime, hashlib, hmac 
import requests

def lambda_handler(event, context):
    # Validation
    # APIからパラメータの取得
    if 'queryStringParameters' in event == False:
        return {
            'statusCode': 403,
            'body': 'error'
        }
    
    # 処理を行うために必要なパラメータをまとめる
    requestData = {
        'query': 'iPhone' #event['queryStringParameters']['q']
    }
    
    # APIにリクエスト
    # https://webservices.amazon.co.jp/paapi5/documentation/sending-request.html#signing
    
    scheme = 'https'
    host = 'webservices.amazon.co.jp'
    path = '/paapi5/searchitems'
    endpoint = scheme + '://' + host + path
    accessKey = 'XXXXX'
    secretKey = 'XXXXX'
    partnerTag = 'XXXXX-22'
    content_encoding = 'amz-1.0'
    content_type = 'application/json; charset=utf-8'
    amz_target = 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems'
    
    request_parameters = {
        'Keywords': requestData['query'],
        'Marketplace': 'www.amazon.co.jp',
        'PartnerTag': partnerTag,
        'PartnerType': 'Associates',
        'Operation': 'SearchItems',
        'Resources': [
            'BrowseNodeInfo.BrowseNodes',
            'BrowseNodeInfo.BrowseNodes.Ancestor',
            'BrowseNodeInfo.BrowseNodes.SalesRank',
            'BrowseNodeInfo.WebsiteSalesRank',
            'CustomerReviews.Count',
            'CustomerReviews.StarRating',
            'Images.Primary.Small',
            'Images.Primary.Medium',
            'Images.Primary.Large',
            'Images.Variants.Small',
            'Images.Variants.Medium',
            'Images.Variants.Large',
            'ItemInfo.ByLineInfo',
            'ItemInfo.ContentInfo',
            'ItemInfo.ContentRating',
            'ItemInfo.Classifications',
            'ItemInfo.ExternalIds',
            'ItemInfo.Features',
            'ItemInfo.ManufactureInfo',
            'ItemInfo.ProductInfo',
            'ItemInfo.TechnicalInfo',
            'ItemInfo.Title',
            'ItemInfo.TradeInInfo',
            'Offers.Listings.Availability.MaxOrderQuantity',
            'Offers.Listings.Availability.Message',
            'Offers.Listings.Availability.MinOrderQuantity',
            'Offers.Listings.Availability.Type',
            'Offers.Listings.Condition',
            'Offers.Listings.Condition.ConditionNote',
            'Offers.Listings.Condition.SubCondition',
            'Offers.Listings.DeliveryInfo.IsAmazonFulfilled',
            'Offers.Listings.DeliveryInfo.IsFreeShippingEligible',
            'Offers.Listings.DeliveryInfo.IsPrimeEligible',
            'Offers.Listings.DeliveryInfo.ShippingCharges',
            'Offers.Listings.IsBuyBoxWinner',
            'Offers.Listings.LoyaltyPoints.Points',
            'Offers.Listings.MerchantInfo',
            'Offers.Listings.Price',
            'Offers.Listings.ProgramEligibility.IsPrimeExclusive',
            'Offers.Listings.ProgramEligibility.IsPrimePantry',
            'Offers.Listings.Promotions',
            'Offers.Listings.SavingBasis',
            'Offers.Summaries.HighestPrice',
            'Offers.Summaries.LowestPrice',
            'Offers.Summaries.OfferCount',
            'ParentASIN',
            'RentalOffers.Listings.Availability.MaxOrderQuantity',
            'RentalOffers.Listings.Availability.Message',
            'RentalOffers.Listings.Availability.MinOrderQuantity',
            'RentalOffers.Listings.Availability.Type',
            'RentalOffers.Listings.BasePrice',
            'RentalOffers.Listings.Condition',
            'RentalOffers.Listings.Condition.ConditionNote',
            'RentalOffers.Listings.Condition.SubCondition',
            'RentalOffers.Listings.DeliveryInfo.IsAmazonFulfilled',
            'RentalOffers.Listings.DeliveryInfo.IsFreeShippingEligible',
            'RentalOffers.Listings.DeliveryInfo.IsPrimeEligible',
            'RentalOffers.Listings.DeliveryInfo.ShippingCharges',
            'RentalOffers.Listings.MerchantInfo',
            'SearchRefinements'
        ]
    }
    
    # ----------------
    # 署名を作成 (AWS4-HMAC-SHA256)
    # https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html#sig-v4-examples-post
    # ************* REQUEST VALUES *************
    method = 'POST'
    service = 'ProductAdvertisingAPI'
    region = 'us-west-2' #https://webservices.amazon.co.jp/paapi5/documentation/common-request-parameters.html#host-and-region
    
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
    access_key = accessKey
    secret_key = secretKey
    if access_key is None or secret_key is None:
        print('No access key is available.')
        sys.exit()
    
    # Create a date for headers and the credential string
    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
    
    
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
    canonical_headers = 'content-encoding:' + content_encoding + '\n' + 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n' + 'x-amz-target:' + amz_target + '\n'
    
    # Step 5: Create the list of signed headers. This lists the headers
    # in the canonical_headers list, delimited with ";" and in alpha order.
    # Note: The request can include any headers; canonical_headers and
    # signed_headers lists those that you want to be included in the 
    # hash of the request. "Host" and "x-amz-date" are always required.
    signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'
    
    # Step 6: Create payload hash. In this example, the payload (body of
    # the request) contains the request parameters.
    request_parameters_dump = json.dumps(request_parameters)
    payload_hash = hashlib.sha256(request_parameters_dump.encode('utf-8')).hexdigest()
    
    # Step 7: Combine elements to create canonical request
    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    
    
    # ************* TASK 2: CREATE THE STRING TO SIGN*************
    # Match the algorithm to the hashing algorithm you use, either SHA-1 or
    # SHA-256 (recommended)
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    
    # ************* TASK 3: CALCULATE THE SIGNATURE *************
    # Create the signing key using the function defined above.
    signing_key = getSignatureKey(secret_key, datestamp, region, service)
    
    # Sign the string_to_sign using the signing_key
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
    # The signing information can be either in a query string value or in 
    # a header named Authorization. This code shows how to use a header.
    # Create authorization header and add to request headers
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    # ----------------
    
    # Python note: The 'host' header is added automatically by the Python 'requests' library.
    headers = {
        'content-encoding': content_encoding,
        'content-type': content_type,
        'x-amz-date': amzdate,
        'x-amz-target': amz_target,
        'Authorization': authorization_header
    }
    
    # ************* SEND THE REQUEST *************
    r = requests.post(endpoint, data=json.dumps(request_parameters), headers=headers)
    
    # エラー時
    if r.status_code != 200:
        return {
            'message': 'Failed',
            'statusCode': r.status_code,
            'body': r.text
        }
    
    # リクエストを返す
    return {
        'message': 'Succeeded',
        'statusCode': r.status_code,
        'body': r.text
    }