# -*- coding: utf-8 -*-

import tushare

from datetime import datetime
from datetime import timedelta
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

from SinaStock import SinaStock


TUSHARE_APP_KEY = 'a64231cf514f205f90798848538491d7ed8725255809716c18fb48ee'

# 下面两个值需要配合调整，只调第一个，第二个未调高，可能最低值只取了早期的最低值。最近的低值都未体现。
RECENT_DAY_COUNT = 60
MAX_EXTREMA_COUNT = 7

EXTREMA_DIFF_RATIO = 0.001  # 0.01    # 如果两个极大值之间距离比例小于此值，则忽略新的极值
INIT_IGNORE_COUNT = 10000
MIN_WORTH_VALUE = -99999  # 最小值


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
def filter_similar_index(data, indexes):
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


# data_list已经去掉了第一个元素, 最新的数在前面
# 返回天数和，进入当前趋势时的指数值，便于计算累积增/降幅
def calc_index_continuous_days(data_list, is_increase):
    count = 1
    last_item = data_list.pop(0)
    if len(data_list) < 1:
        return count,last_item
    for item in data_list:
        if last_item >= item:
            if is_increase:
                count = count + 1
                last_item = item
            else:
                return count,last_item
        else:
            if is_increase:
                return count,last_item
            else:
                count = count + 1
                last_item = item

    return count,last_item


# 股票指数
# 用Sina获取实时指数，并用 TuShare获取较全信息
class StockIndex(object):

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.has_realtime_info = False
        self.current_index = None
        self.current_index_time = None
        self.current_index_change_ratio = None
        self.current_amount = None  # 成交额(亿)
        self.continuous_days = None
        self.continuous_ratio = None

        self.index_trend = None    # 获取到的指数趋势列表，包含多于60天的数据
        self.recent_index = None   # 最近60天的指数数据
        self.recent_index_max_indexes = None  # 最近60天，最大值的下标列表
        self.recent_index_min_indexes = None  # 最近60天，最小值的下标列表
        self.recent_index_max = None  # 最近60天，最大值列表
        self.recent_index_min = None  # 最近60天，最小值列表

        # print("[StockIndex TuShare] process :", self.stock_id)

    def initialize(self):
        self.has_realtime_info = self.init_realtime_info()
        if self.fetch_info():
            self.init_info()
            self.calc_index()
            return True
        return self.has_realtime_info

    def fetch_info(self):
        import logging
        _logger = logging.getLogger('werkzeug')
        try:
            _logger.info("Use Tushare to get stock index : " + str(self.stock_id))
            tushare.set_token(TUSHARE_APP_KEY)
            api = tushare.pro_api()
            time_start = datetime.now() - timedelta(days=RECENT_DAY_COUNT+5)
            start_date = time_start.strftime("%Y%m%d")
            end_date = datetime.now().strftime("%Y%m%d")
            self.index_trend = api.index_daily(ts_code=self.stock_id, start_date=start_date, end_date=end_date,
                                   fields='trade_date,close,amount')  # index_trend -- 最新时间在最前面
            if self.index_trend.empty:
                print("Fetch info failed in TuShare.")
                return False
        except Exception as ex:
            _logger.error("Tushare throw exception: " + str(ex))
            return False
        return True

    def init_realtime_info(self):
        sina_stock = SinaStock(self.stock_id)
        if sina_stock.initialize():
            self.current_index = sina_stock.current_index
            self.current_index_time = sina_stock.current_index_time
            self.current_index_change_ratio = sina_stock.current_index_change_ratio
            return True
        return False

    def init_info(self):
        if not self.has_realtime_info:
            self.current_index_time = self.index_trend['trade_date'][0]
            # print("current time:", self.current_index_time)
            self.current_index = self.index_trend['close'][0]
            # print("current index:", self.current_index)
            last_index = self.index_trend['close'][1]
            self.current_index_change_ratio = (self.current_index - last_index) / last_index * 100   # 换算成百分数
            # print("change ratio:", self.current_index_change_ratio)

        # 成交额 （千元），感觉应该是元,https://tushare.pro/document/2?doc_id=27
        # 除以1亿，单位换算为亿
        self.current_amount = self.index_trend['amount'][0]/100000000
        index_list = self.index_trend['close'][1:].tolist()  # 需要把pandas dataframe对象或series对象转换成list
        self.continuous_days, prev_index = calc_index_continuous_days(index_list, self.current_index_change_ratio > 0)
        # print("prev_index:", prev_index)
        self.continuous_ratio = (self.current_index - prev_index) / prev_index * 100
        # print("continuous_days:", self.continuous_days)


    def calc_index(self):
        temp_array = self.index_trend[:RECENT_DAY_COUNT]  # 取最近60个
        self.recent_index = temp_array[::-1]   # 改成最新时间在最后面
        # print(self.recent_index)
        index_list = self.recent_index['close'].tolist()  # 转为list
        index_array = np.array(index_list)
        max_indexes = signal.argrelextrema(index_array, np.greater)
        self.recent_index_max_indexes = filter_similar_index(index_array, max_indexes)
        self.recent_index_max = np.array(self.recent_index)[self.recent_index_max_indexes]

        min_indexes = signal.argrelextrema(-index_array, np.greater)
        self.recent_index_min_indexes = filter_similar_index(-index_array, min_indexes)
        self.recent_index_min = np.array(self.recent_index)[self.recent_index_min_indexes]

        # self.show_debug_info(index_array, self.recent_index_max_indexes, self.recent_index_min_indexes)

    def show_debug_info(self, data, max_indexes, min_indexes, figure=True):
        # print(data)
        print("极大值:")
        print(data[max_indexes])
        print(max_indexes)
        print("极小值:")
        print(data[min_indexes])
        print(min_indexes)

        if figure:
            plt.figure(figsize=(10, 5))
            plt.plot(np.arange(len(data)), data)
            plt.plot(max_indexes, data[max_indexes], 'o')
            plt.plot(min_indexes, data[min_indexes], 'x')
            plt.show()


if __name__ == '__main__':
    index = StockIndex("000001.SH")  # 上证指数
