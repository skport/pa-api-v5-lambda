import json
import requests

import sys, os, base64, datetime, hashlib, hmac

from collections import OrderedDict

import boto3
import botocore.exceptions

# Class : PA-API のjsonデータから最適なものを探す
class ExtractItem():
    __config = {}
    
    def __init__(self, raw_data, keyword):
        self.__raw_data = json.loads(raw_data)
        self.__keyword = keyword
    
    def extract(self):
        entries = []
        i = 0
        for entry in self.__raw_data['SearchResult']['Items']:
            r = self.extract_entry(entry)
            if r != False:
                entries.append(r)
                i += 1
            if i >= 10: # 指定件数に切りつめ
                break
        return json.dumps(entries)
        
    # 1件処理
    def extract_entry(self, entry):
        print(entry)
        
        # 除外カテゴリ（テレビ・映画）
        try:
            if entry['BrowseNodeInfo']['BrowseNodes'][0]['DisplayName'] == 'テレビ' or entry['BrowseNodeInfo']['BrowseNodes'][0]['DisplayName'] == '映画':
                return False
        except:
            pass
        
        # 除外カテゴリ（アプリ）
        try:
            if entry['ItemInfo']['Classifications']['Binding']['DisplayValue'] == 'アプリ':
                return False
        except:
            pass
        
        # 除外　画像が小さすぎる
        try:
            if entry['Images']['Primary']['Large']['Width'] < 100:
                return False
        except:
            pass
        
        
        
        # 禁止文字の置換
        def rep(string):
            r = string.replace('<', '&lt;')
            r = string.replace('>', '&gt;')
            r = string.replace('&', '&amp;')
            r = string.replace('"', '&quot;')
            r = string.replace("'", '&#39;')
            return r
        
        asin = entry['ASIN']
        
        url = entry['DetailPageURL']
        
        title = entry['ItemInfo']['Title']['DisplayValue']
        title = rep(title)
        
        img = entry['Images']['Primary']['Large']['URL']
        img_w = entry['Images']['Primary']['Large']['Width']
        img_h = entry['Images']['Primary']['Large']['Height']
        
        # ブランド
        brand = ''
        try:
            brand = entry['ItemInfo']['ByLineInfo']['Brand']['DisplayValue']
            brand = rep(brand)
        except:
            print('unknown brand : ByLineInfo.Manufacturer')
        
        # 著者等
        contributor = ''
        try:
            contributor = entry['ItemInfo']['ByLineInfo']['Contributors'][0]
            contributor['Name'] = rep(contributor['Name'])
        except:
            print('unknown contributor : ByLineInfo.Contributors')
            
        # メーカー
        manufacturer = ''
        try:
            manufacturer = entry['ItemInfo']['ByLineInfo']['Manufacturer']['DisplayValue']
            manufacturer = rep(manufacturer)
        except:
            print('unknown manufacturer : ByLineInfo.Manufacturer')
            
        # 価格
        price = ''
        try:
            price = entry['Offers']['Summaries'][0]['LowestPrice']['DisplayAmount']
            if price == '￥0':
                price = ''
        except:
            print('unknown price : Offers.Summaries')
            
        # 文字列の切りつめ（全角・半角どちらも1文字とみなす)
        #max_length = 40;
        
        r = {
            'asin': asin,
            'url': url,
            'title': title,#[0:max_length],
            'img': {
                'url': img,
                'width': img_w,
                'height': img_h,
            },
            'brand': brand,
            'manufacturer': manufacturer,
            'contributor': contributor,
            'price': price
        }
        
        return r