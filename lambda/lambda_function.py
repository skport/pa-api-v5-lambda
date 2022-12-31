import json
import requests

import sys, os, base64, datetime, hashlib, hmac

import boto3
import botocore.exceptions

import Class_ManageCache
import Class_AmzApi5
import Class_ExtractItem

# エラー時のレスポンス
def responseErrorBody():
    return {
        'message': 'Fail',
        'statusCode': 200,
        'body': json.dumps("{'missing':'true'}") 
    }

def lambda_handler(event, context):
    # Validate Parameters
    try:
        #keywords = event['body']['action']
        #print(type(event['body']))
        
        #event['body'] = '{"action":"iPhone"}'
        
        request_body = json.loads(event['body'])
        keywords = request_body['action']
        print('Keywords:' + keywords)
        #return
    except KeyError:
        return {
            'statusCode': 403,
            'body': 'error'
        }
    
    # ********************************************
    # PA-APIに与えるパラメータ
    pa_api_req_attr = {
        'endpoint': 'https://webservices.amazon.co.jp/paapi5/searchitems',
        'host': 'webservices.amazon.co.jp',
        'path': '/paapi5/searchitems',
        'request_parameters': {
            'Keywords': keywords, # PA-APIで検索したい文字列
            'PartnerType': 'Associates',
            'Operation': 'SearchItems',
            'SortBy': 'Relevance', # Default: Relevance
            'MinPrice': 500,
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
    }
    #event['queryStringParameters']['q']
    
    # ********************************************
    # S3 のオブジェクトが有効なら返し、無効なら PA-API にアクセスする
    
    # Bucket名、オブジェクト(キャッシュ)有効期限はS3のライフサイクルで設定
    cache_bucket_name = 'amzapi-storage'
    cache_bucket_folder = {
        'lock': 'lock',
        'data': 'data'
    }
    manage_cache = Class_ManageCache.ManageCache(cache_bucket_name)
    
    # オブジェクトキー生成（ハッシュ値）
    # シードとして、PA-APIに与えるパラメータを利用
    object_key = manage_cache.create_object_key(json.dumps(pa_api_req_attr))
    cache_data_object_key = cache_bucket_folder['data'] + '/' + object_key
    cache_lock_object_key = cache_bucket_folder['lock'] + '/' + object_key
    print('cache_data_object_key:' + cache_data_object_key)
    print('cache_lock_object_key:' + cache_lock_object_key)
    
    # オブジェクトが有効なら、キャッシュを読み込み返して、ここで終了
    cache_r = manage_cache.get(cache_data_object_key)
    if cache_r != False:
        cache_raw_data = manage_cache.read(cache_r)
        extract_items = Class_ExtractItem.ExtractItem(cache_raw_data, keywords)
        cache_exatrac_items = extract_items.extract()
        return {
            'message': 'Succeeded',
            'statusCode': 200,
            'body': cache_exatrac_items
        }

    # ********************************************
    # PA-API にリクエスト
    
    # キャッシュに書込中（ロックファイル有効）なら、以降の処理を拒否して終了 (PA-APIの同一リクエストを拒否)
    cache_r = manage_cache.get(cache_lock_object_key)
    if cache_r != False:
        return responseErrorBody()
    
    # リクエスト発生中を示すためのロックファイル生成
    cache_r = manage_cache.put(cache_lock_object_key, "lock")
    
    # Retrieve product information from within Amazon
    amz_api = Class_AmzApi5.AmzAPi5('xxxxx', 'xxxxx')
    
    # Set region & market place
    # https://webservices.amazon.co.jp/paapi5/documentation/common-request-parameters.html#host-and-region
    amz_api.set_region('us-west-2')
    amz_api.set_market_place('www.amazon.co.jp')
    
    # Set your partner tag
    amz_api.set_partner_tag('xxxxx-22')
    
    # Create Signature & POST Request PA-API (SearchItems)
    # Parameters: x-amz-target, endpoint, host, path, request_parameters(without PartnerTag & MarketPlace)
    r = amz_api.request_post('com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems',
        pa_api_req_attr['endpoint'],
        pa_api_req_attr['host'],
        pa_api_req_attr['path'],
        pa_api_req_attr['request_parameters']
    )
    
    # エラー時
    if r.status_code != 200:
        print('PA-API Error:' + r.status_code + ' ' + r.text)
        return responseErrorBody()
        
    # S3 にキャッシュとして保存
    cache_r = manage_cache.put(cache_data_object_key, r.text)
    
    extract_items = Class_ExtractItem.ExtractItem(r.text, keywords)
    cache_exatrac_items = extract_items.extract()
    
    # ロックファイル削除
    cache_r = manage_cache.delete(cache_lock_object_key)
        
    # リクエストを返す
    return {
        'message': 'Succeeded',
        'statusCode': r.status_code,
        'body': cache_exatrac_items
    }
