# -*- coding: utf-8 -*-
from json import JSONDecodeError

import requests
import json


class FastFund(object):

    def __init__(self, fund_id):
        self.fund_id = fund_id
        self.fund_name = ""
        self.unit_worth = None
        self.unit_worth_time = None
        self.unit_worth_change_ratio = None
        # self.init_info()
        print("[FastFund] process :", self.fund_id, self.fund_name)

    def get_url(self):
        head = 'http://fundgz.1234567.com.cn/js/'
        tail = '.js?rt=1463558676006'

        return head + self.fund_id + tail

    def initialize(self):
        # 用requests获取到对应的文件
        content = requests.get(self.get_url())
        if content.status_code != 200:
            print("Fetch info failed in FastFund.")
            return False

        # {"fundcode":"001186","name":"富国文体健康股票","jzrq":"2019-11-28","dwjz":"1.1190",
        # "gsz":"1.1130","gszzl":"-0.53","gztime":"2019-11-29 15:00"})
        json_data = content.text[len('jsonpgz('):-2]

        if json_data == '':
            print("FastFund get result fail. content.text =", content.text, "fund_id =", self.fund_id)
            return False

        try:
            json_obj = json.loads(json_data)
        except JSONDecodeError as e:
            print("FastFund decode result fail. content.text =", content.text, "fund_id =", self.fund_id)
            print(e)
            return False

        self.fund_name = json_obj['name']
        self.unit_worth = float(json_obj['gsz'])
        self.unit_worth_time = json_obj['gztime']
        self.unit_worth_change_ratio = float(json_obj['gszzl'])

        return True


if __name__ == '__main__':
    fund = FastFund('001186')   # 易方达中小盘
    # fund = Fund("005911")  # 广发双引擎
    # fund = Fund("320007")  # 诺安成长混合(320007)
