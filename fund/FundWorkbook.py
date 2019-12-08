# -*- coding: utf-8 -*-

from openpyxl import load_workbook

from FundSheet import FUND_SHEET_NAME, FundSheet
# from XLSXReader import XLSXReader


class FundWorkbook(object):
    def __init__(self, file):
        # self.reader = XLSXReader(file)   # 为了用这个来计算带公式的excel表格数值，多load workbook一次，可能有问题.=> 加载太慢了。
        self.wb = load_workbook(file)   # self.reader.get_book()
        self.sheet = {FUND_SHEET_NAME: FundSheet(self.wb)}  # 注意不是原始wb 中的Sheet，而是这里的FundSheet包装类对象
        self.sheet_alias = {FUND_SHEET_NAME: 'fund'}

    def get_table(self, sheet_name=None):
        return {self.sheet_alias[FUND_SHEET_NAME]: self.sheet[FUND_SHEET_NAME].get_table()}

    def save_table(self, ):
        pass


