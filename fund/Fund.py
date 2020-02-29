# -*- coding: utf-8 -*-

import requests
import time
import execjs
import datetime
import re
import pytz

import numpy as np
import scipy.signal as signal
from JsTools import eval_js
# import matplotlib.pyplot as plt


# 下面两个值需要配合调整，只调第一个，第二个未调高，可能最低值只取了早期的最低值。最近的低值都未体现。
RECENT_DAY_COUNT = 60*2
MAX_EXTREMA_COUNT = 7

EXTREMA_DIFF_RATIO = 0.01  # 0.01    # 如果两个极大值之间距离比例小于此值，则忽略新的极值
INIT_IGNORE_COUNT = 100
MIN_WORTH_VALUE = -99999  # 最小值


# 获得的基金信息里的时间戳都是中国时间
def timestamp2time(timestamp):
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.fromtimestamp(timestamp/1000, tz).strftime("%Y-%m-%d")  # 转换为字符串，规避excel不能设置显示格式的问题


def only_keep_latest_extrema(items, target):
    last_index = items[::-1].index(target)
    # 把反过来的序号换算为正的序号
    last_index = len(items) - last_index - 1
    items.pop(last_index)
    items.insert(last_index, True)    # 最后一个 target 替换为 True
    out_list = []
    # 其他的 target 都替换为False
    for x in items:
        if isinstance(x, int) and x == target:
            out_list.append(False)
        else:
            out_list.append(x)
    return out_list


# 1、找到最大的元素，保留它
# 2、把距离最大元素比例范围 0.005的元素删除
# 重复1、 2，从而去除相近的极值点
# 注意如果剔除相似极值，不是保留最大值，而是保留最近的值。因为最终参考时是先参考最近极值。
def filter_similar_worth(data, indexes):
    origin_index = indexes[0]
    extrema_data = data[indexes]
    # print(extrema_data)

    extrema_len = len(origin_index)
    filter_index_array = [False] * extrema_len
    count = 0
    total_count = 0
    last_extrema_value = 0
    ignore_count = INIT_IGNORE_COUNT

    while True:
        max_index = np.argmax(extrema_data)
        current_extrema_value = extrema_data[max_index] # 当前的最大值
        # 如果当前最大值与上次最大值的比例大于EXTREMA_DIFF_RATIO，才保留
        if last_extrema_value == 0 or abs((last_extrema_value - current_extrema_value)/last_extrema_value) > EXTREMA_DIFF_RATIO:
            if ignore_count != INIT_IGNORE_COUNT:
                filter_index_array = only_keep_latest_extrema(filter_index_array, ignore_count)
            ignore_count = ignore_count + 1
            filter_index_array[max_index] = ignore_count   # 保留找到的最大值
            last_extrema_value = current_extrema_value
            count = count + 1
            extrema_data[max_index] = MIN_WORTH_VALUE    # 已找到的最大值或决定忽略的赋值为0
        else:
            filter_index_array[max_index] = ignore_count  # 保留找到的最大值
            extrema_data[max_index] = MIN_WORTH_VALUE  # 已找到的最大值或决定忽略的赋值为0
        total_count = total_count + 1
        if count >= MAX_EXTREMA_COUNT or count >= extrema_len or total_count >= extrema_len:
            if ignore_count != INIT_IGNORE_COUNT:
                filter_index_array = only_keep_latest_extrema(filter_index_array, ignore_count)
            filter_index_array[len(filter_index_array) - 1] = True  # 保证最新的极大极小值一定包含
            break

    return origin_index[filter_index_array]


# data_list已经去掉了第一个元素
def calc_unit_worth_continuous_days(data_list, is_increase):
    count = 1
    if len(data_list) < 2:
        return count
    temp_list = data_list[::-1]
    last_item = temp_list.pop(0)
    for item in temp_list:
        if last_item['y'] >= item['y']:
            if is_increase:
                count = count + 1
                last_item = item
            else:
                return count
        else:
            if is_increase:
                return count
            else:
                count = count + 1
                last_item = item

    return count


# 用unit worth，计算涨跌幅，需要考虑分红，但self.unit_worth_trend[-1:][0]里面的分红写的是"分红：每份派现金0.5元"
# 用ac_worth的变化率，跟unit worth变化率又不一样
def calc_unit_worth_change_ratio(old_worth, new_worth):
    old_worth_value = old_worth['y']
    new_worth_value = new_worth['y']

    unit_money_value = 0
    new_worth_unit_money = new_worth['unitMoney']
    if new_worth_unit_money != "":
        print("new_worth_unit_money:", new_worth_unit_money)
        regex = re.compile("分红：每份派现金(\d*\.*\d*)元")
        unit_money_str = regex.match(new_worth_unit_money).group(1)
        unit_money_value = float(unit_money_str)
        print("unit_money_value", unit_money_value)

    change_ratio = (new_worth_value + unit_money_value - old_worth_value) / old_worth_value * 100

    return change_ratio


# 基金
# 单位净值 unit worth: {"x":1430841600000,"y":1.0,"equityReturn":0,"unitMoney":""}
#     x-时间, y-净值, equityReturn-净值回报 unitMoney-每份派送金
# 累积净值 ac worth : [1430841600000,1.0]
class Fund(object):

    def __init__(self, fund_id):
        self.fund_id = fund_id
        self.fund_name = ""
        self.unit_worth = None
        self.unit_worth_time = None
        self.unit_worth_change_ratio = None
        self.unit_worth_history = []
        self.continuous_days = None
        self.ac_worth = None

        self.unit_worth_trend = None
        self.unit_worth_max = None
        self.unit_worth_min = None
        self.recent_unit_worth = None

        self.ac_worth_trend = None
        self.ac_worth_max = None
        self.ac_worth_min = None
        self.recent_ac_worth = None
        self.recent_ac_worth_max_indexes = None
        self.recent_ac_worth_min_indexes = None
        self.recent_ac_worth_max = None
        self.recent_ac_worth_min = None
        self.ac_worth_history = []

    def initialize(self):
        if self.init_info():
            self.recent_unit_worth = self.unit_worth_trend[-RECENT_DAY_COUNT:]
            # self.calc_unit_worth_history()   # 必须在逆序前，赋值后  # 表格趋势图改为ac worth
            self.recent_unit_worth = self.recent_unit_worth[::-1]     # 截取最后60天，再逆序，最新时间在前面
            # self.calc_unit_worth()
            self.calc_ac_worth()
            # print("[Fund] process :", self.fund_id, self.fund_name)
            return True
        return False

    def calc_unit_worth_history(self):
        self.unit_worth_history = []
        for worth in self.recent_unit_worth:
            self.unit_worth_history.append(worth['y'])
        # print(self.unit_worth_history)

    def get_url(self):
        head = 'http://fund.eastmoney.com/pingzhongdata/'
        tail = '.js?v=' + time.strftime("%Y%m%d%H%M%S", time.localtime())

        return head + self.fund_id + tail

    def init_info(self):
        import logging
        _logger = logging.getLogger('werkzeug')

        # 用requests获取到对应的文件
        content = requests.get(self.get_url())

        # 使用execjs获取到相应的数据
        js_content = execjs.compile(content.text)
        self.fund_name = eval_js(js_content,'fS_name', '')
        if self.fund_name == '':
            _logger.info("Fund get fund_name failed. fund_id = " + self.fund_id)

        # 单位净值走势
        self.unit_worth_trend = eval_js(js_content,'Data_netWorthTrend', [])
        if len(self.unit_worth_trend) > 0:
            self.unit_worth_time = timestamp2time(self.unit_worth_trend[-1:][0]['x'])
            self.unit_worth = self.unit_worth_trend[-1:][0]['y']
            self.unit_worth_change_ratio = calc_unit_worth_change_ratio(self.unit_worth_trend[-2:-1][0], self.unit_worth_trend[-1:][0])
            # print("self.unit_worth_change_ratio", self.unit_worth_change_ratio)
            self.continuous_days = calc_unit_worth_continuous_days(self.unit_worth_trend[:-1], self.unit_worth_change_ratio > 0)
        else:
            _logger.info("Fund get unit worth failed. fund_id = " + self.fund_id)
            return False

        # 累计净值走势
        self.ac_worth_trend = eval_js(js_content,'Data_ACWorthTrend', [])
        if len(self.ac_worth_trend) > 0:
            self.ac_worth = self.ac_worth_trend[-1:][0][1]
            # last_ac_worth = self.ac_worth_trend[-2:-1][0][1]
            # self.ac_worth_change_ratio = (self.ac_worth - last_ac_worth) / last_ac_worth * 100
            # print("self.ac_worth_change_ratio", self.ac_worth_change_ratio)
        else:
            _logger.info("Fund get ac worth failed. fund_id = " + self.fund_id)
            return False
        return True

    def calc_unit_worth(self):
        unit_worth_list = []

        for day_unit_worth in self.recent_unit_worth:
            unit_worth_list.append(day_unit_worth['y'])

        print(unit_worth_list)
        print(len(unit_worth_list))
        x = np.array(unit_worth_list)
        print(x)
        print(x[signal.argrelextrema(x, np.greater)])
        print(signal.argrelextrema(x, np.greater))
        self.show_figure(x)

    def calc_ac_worth(self):
        self.recent_ac_worth = self.ac_worth_trend[-RECENT_DAY_COUNT:]
        self.ac_worth_history = []
        for day_ac_worth in self.recent_ac_worth:
            self.ac_worth_history.append(day_ac_worth[1])

        # print("ac_worth_list")
        # print(ac_worth_list)
        # ac_worth_list = [1.5203, 1.5819, 1.5665, 1.5864, 1.5757, 1.5667, 1.5639, 1.6061, 1.6016, 1.6381, 1.6539, 1.7254,
        #                  1.7682, 1.7917, 1.7963, 1.7993, 1.8718, 1.8467, 1.821, 1.8158, 1.8268, 1.7878, 1.7976, 1.8371,
        #                  1.8593, 1.9044, 1.9116, 1.8359, 1.7601, 1.7703, 1.7399, 1.712, 1.7485, 1.7918, 1.7731, 1.8277,
        #                  1.7781, 1.7731, 1.7648, 1.7345, 1.7271, 1.7655, 1.7526, 1.7547, 1.7879, 1.8626, 1.8315, 1.8729,
        #                  1.8561, 1.8759, 1.8876, 1.9322, 1.9036, 1.904, 1.8911, 1.8595, 1.8624, 1.9337, 1.9786, 1.9708]

        ac_worth_array = np.array(self.ac_worth_history)
        max_indexes = signal.argrelextrema(ac_worth_array, np.greater)
        self.recent_ac_worth_max_indexes = filter_similar_worth(ac_worth_array, max_indexes)
        self.recent_ac_worth_max = np.array(self.recent_ac_worth)[self.recent_ac_worth_max_indexes]

        min_indexes = signal.argrelextrema(-ac_worth_array, np.greater)
        self.recent_ac_worth_min_indexes = filter_similar_worth(-ac_worth_array, min_indexes)
        self.recent_ac_worth_min = np.array(self.recent_ac_worth)[self.recent_ac_worth_min_indexes]

        # self.show_debug_info(ac_worth_array, self.recent_ac_worth_max_indexes, self.recent_ac_worth_min_indexes)

    # def show_debug_info(self, data, max_indexes, min_indexes, figure=True):
    #     print(data)
    #     print("极大值:")
    #     print(data[max_indexes])
    #     print(max_indexes)
    #     print("极小值:")
    #     print(data[min_indexes])
    #     print(min_indexes)
    #
    #     if figure:
    #         plt.figure(figsize=(10, 5))
    #         plt.plot(np.arange(len(data)), data)
    #         plt.plot(max_indexes, data[max_indexes], 'o')
    #         plt.plot(min_indexes, data[min_indexes], 'x')
    #         plt.show()

    def get_price(self, time_str):
        # print("time_str", time_str)
        for day_unit_worth in self.recent_unit_worth:
            # print(day_unit_worth)
            item_time = datetime.datetime.fromtimestamp(day_unit_worth['x']/1000).strftime("%Y%m%d")
            # print(item_time)
            if str(item_time) == str(time_str):
                return day_unit_worth['y']
        return None

    def get_ac_price(self, time_str):
        # print("get_ac_price time_str", time_str)
        for day_ac_worth in self.recent_ac_worth:
            # print(day_ac_worth)
            item_time = datetime.datetime.fromtimestamp(day_ac_worth[0]/1000).strftime("%Y%m%d")
            # print(item_time)
            if str(item_time) == str(time_str):
                return day_ac_worth[1]
        return None

if __name__ == '__main__':
    fund = Fund('110011')   # 易方达中小盘
    # fund = Fund("005911")  # 广发双引擎
    # fund = Fund("320007")  # 诺安成长混合(320007)
