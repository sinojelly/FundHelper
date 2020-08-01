# -*- coding: utf-8 -*-

import requests
import datetime


# 通过访问新浪对应指数网页，然后用Fiddler抓包可以看到路径
# 纳斯达克100 http://hq.sinajs.cn/format=text&list=gb_$ndx

STOCK_INDEX_MAP = {'NDX': "gb_$ndx",    # 纳斯达克100
                   '000001.SH': 'sh000001',  # 上证综指
                   '000016.SH': 'sh000016',  # 上证50
                   '000300.SH': 'sh000300',  # 沪深300
                   '000905.SH': 'sh000905',  # 中证500
                   '000942.CSI': 'sh000942',  # 内地消费
                   '000932.SH': 'sh000932',   # 内地主要消费
                   '000991.SH': 'sh000991',   # 全指医药卫生
                   '000913.SH': 'sh000913',   # 沪深300医药
                   '399975.SZ': 'sz399975',   # 证券公司指数
                   '399006.SZ': 'sz399006',   # 创业版指
                   '399986.CSI': 'sz399986',  # 中证银行
                   '000170.SH': 'sh000170',   # 50AH优选
                   '100.HSI': 'int_hangseng'  # 恒生指数
                   # '000922.CSI': 'sh000922'  # 中证红利  这个获取到数据是全0
                   }


# 新浪财经数据获取
# 能够获得实时数据
# 能够获得股票、期货等各种财经数据
class SinaStock(object):

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.current_index = None
        self.current_index_time = None
        self.current_index_change_ratio = None

        # print("[Sina] process :", self.stock_id)
        # self.initialize()

    def get_url(self):
        head = 'http://hq.sinajs.cn/format=text&list='

        if self.stock_id in STOCK_INDEX_MAP.keys():
            tail = STOCK_INDEX_MAP[self.stock_id]
        else:
            tail = self.stock_id
        return head + tail

    def initialize(self):
        try:
            # 用requests获取到对应的文件
            content = requests.get(self.get_url())
        except NewConnectionError as err:
            _logger.error("[SinaStock] request url fail: " + self.get_url() + " NewConnectionError: " + str(err))
            return False

        if content.status_code != 200:
            print("Fetch info failed in Sina api.")
            return False

        # print(content.text)
        result = content.text.replace('"', '').split('\n')[0]  # 如果有多条记录取最前面一条，实际上每次只提供了一个stock id，不会有多个记录
        result = result.split('=')[1]  # 等号后面的是内容
        result = result.split(',')     # 各项内容由逗号分隔，不过不同股指，项数不同，所以只取了第二项，当前点数
        if len(result) < 2:
            print("Sina get",content.url,"failed. result:", content.text)
            return False
        # 难解析，每种不同指数，格式都不同
        if self.stock_id == 'NDX': # 纳斯达克100
            self.current_index = float(result[1])  # 第0项是名称，第1项是当前实时指数点数
            self.current_index_change_ratio = float(result[2].rstrip("%"))
        elif self.stock_id == '100.HSI':  # 恒生指数
            self.current_index = float(result[1])  # 第0项是名称，第1项是当前实时指数点数
            self.current_index_change_ratio = float(result[3].rstrip("%"))  # 有时候带百分号
        else:  # 中国股市
            self.current_index = float(result[3])
            prev_index = float(result[2])
            if prev_index == 0:
                print("Sina prev_index is 0. self.current_index:", self.current_index)
                return False
            self.current_index_change_ratio = (self.current_index - prev_index) / prev_index * 100

        # print(self.current_index)
        if self.current_index is None or self.current_index == 0:
            print("Sina self.current_index is None or 0.")
            return False
        self.current_index_time = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        return True


if __name__ == '__main__':
    index = SinaStock("NDX")  # 纳斯达克100
    # index = SinaStock('000922.CSI')
