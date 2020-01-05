# -*- coding: utf-8 -*-

import requests
import json
import datetime


JUHE_APP_KEY = 'f95b84a65d4d51d4af05bbca424d2e40'


# 股票指数
# TuShare获取不到的指数信息
# Eastmoney push获取的数据也不准确的(比如纳斯达克100)
class JuheStockIndex(object):

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.current_index = None
        self.current_index_time = None
        self.current_index_change_ratio = None
        self.prev_index = None

        # print("[Juhe] process :", self.stock_id)
        # self.initialize()

    def get_url(self):
        head = 'http://web.juhe.cn:8080/finance/stock/usa?gid='
        tail = "&key=" + JUHE_APP_KEY
        return head + self.stock_id + tail

    def initialize(self):
        import logging
        _logger = logging.getLogger('werkzeug')

        # 用requests获取到对应的文件
        content = requests.get(self.get_url())

        if content.status_code != 200:
            _logger.error("Fetch info failed in Juhe api.")
            return False

        try:
            json_content = json.loads(content.text)
            data = json_content['result'][0]['data']
            self.current_index = float(data['lastestpri'])
            self.prev_index = float(data['formpri'])
            time_str = data['chtime']
            time_obj = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            self.current_index_time = datetime.datetime.strftime(time_obj, '%Y%m%d')
            # print("self.current_index_time:", self.current_index_time)
            self.current_index_change_ratio = (self.current_index - self.prev_index) / self.prev_index * 100
            # print("self.current_index_change_ratio", self.current_index_change_ratio)
        except IndexError as err:
            _logger.error("Juhe parse json_content for stock(" + self.stock_id + ") IndexError. content.text = " + content.text)
        if self.current_index is None:
            _logger.error("Juhe self.current_index is None.")
            return False
        return True

if __name__ == '__main__':
    index = JuheStockIndex("NDX")  # 纳斯达克100
