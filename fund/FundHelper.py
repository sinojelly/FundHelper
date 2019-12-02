# -*- coding: utf-8 -*-

import datetime
import openpyxl
from fund.FastFundSheet import FastFundSheet
from fund.FundSheet import FundSheet
from fund.StockIndexSheet import StockIndexSheet
from fund.InvestSheet import InvestSheet

import sys
import getopt

from io import BytesIO

FAST_RUN = False


def update_work_book(file, fast_run, progress_updater):
    print("Start ...")
    starttime = datetime.datetime.now()
    wb = openpyxl.load_workbook(file)

    invest_sheet = InvestSheet(wb)
    invest_funds = invest_sheet.get_all_funds()

    if fast_run:
        fund_sheet = FastFundSheet(wb)
    else:
        fund_sheet = FundSheet(wb)

    progress_updater(10)  # 更新步骤总数

    fund_sheet.update_funds(invest_funds)

    progress_updater()   # 更新当前步骤

    end_funds_time = datetime.datetime.now()
    print("Finished update funds! It takes", (end_funds_time - starttime).seconds, "seconds.")

    stock_index_sheet = StockIndexSheet(wb)
    stock_index_sheet.update_stock_index()

    progress_updater()  # 更新当前步骤

    end_stock_index_time = datetime.datetime.now()
    print("Finished update stock index! It takes", (end_stock_index_time - end_funds_time).seconds, "seconds.")

    invest_sheet.update_all_invests(fund_sheet, stock_index_sheet)
    # wb.save(file)  # not save to the origin file

    endtime = datetime.datetime.now()
    print("Finished all! It takes", (endtime - starttime).seconds, "seconds.")

    virtual_workbook = BytesIO()
    wb.save(virtual_workbook)

    return virtual_workbook.getvalue()   # 返回临时生成的文件内容，而不是修改文件。避免多应用访问把文件改乱


def str_to_bool(str):
    return True if str.lower() == 'true' else False


# 此文件是总的入口
if __name__ == '__main__':
    try:
        #第一个参数是程序本身 即 parameter.py
        # print(sys.argv[0])
        #解析参数
        opts, args = getopt.getopt(sys.argv[1:], 'f:t:', ["fast=", "target="])
        fast_run = str_to_bool(opts[0][1])   # 目前只有fast一个参数，直接取0号里面的   [('fast','True')]
        # print(opts)
        update_work_book('example_filetest.xlsx', fast_run)
    except getopt.GetoptError as e:
        print("Get opt error:", e)