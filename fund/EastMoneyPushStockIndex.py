# -*- coding: utf-8 -*-

import requests
import json


# 股票指数
# TuShare获取不到的指数信息
class EastMoneyPushStockIndex(object):

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.current_index = None
        self.current_index_time = None
        self.current_index_change_ratio = None
        self.prev_index = None

        print("[EastMoneyPush] process :", self.stock_id)
        # self.initialize()

    def get_url(self):
        head = 'http://push2.eastmoney.com/api/qt/stock/get?secid='

        return head + self.stock_id

    def initialize(self):
        # 用requests获取到对应的文件
        content = requests.get(self.get_url())

        json_content = json.loads(content.text)
        if json_content['data'] is None:
            print("Fetch info failed in East money push")
            return False

        self.current_index = json_content['data']['f43']/100
        self.prev_index = json_content['data']['f60']/100
        time_str = json_content['data']['f80']
        time_json = json.loads(time_str)
        time_start = time_json[0]
        self.current_index_time = str(int(time_start['b'] / 10000))  # 取早上开盘时间
        # print(self.current_index_time)
        self.current_index_change_ratio = (self.current_index - self.prev_index) / self.prev_index * 100
        # print("self.current_index_change_ratio", self.current_index_change_ratio)
        if self.current_index is None:
            return False
        return True

if __name__ == '__main__':
    # index = EastMoneyPushStockIndex("100.NDX")  # 纳斯达克100
    index = EastMoneyPushStockIndex("100.HSI")  # 恒生指数
