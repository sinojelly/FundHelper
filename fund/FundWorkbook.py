# -*- coding: utf-8 -*-

from openpyxl import load_workbook

from FundSheet import FUND_SHEET_NAME, FundSheet


class FundWorkbook(object):
    def __init__(self, file):
        self.wb = load_workbook(file)   # self.reader.get_book()
        self.sheet = {FUND_SHEET_NAME: FundSheet(self.wb)}  # 注意不是原始wb 中的Sheet，而是这里的FundSheet包装类对象
        self.sheet_alias = {FUND_SHEET_NAME: 'fund'}  # 使用英文别名，便于在javascript中直接访问
        self.alias_to_sheet = {}
        for key,value in self.sheet_alias.items():   # 根据前面配置自动配置sheet_alias 到 sheet对象映射表，便于数据更新
            self.alias_to_sheet[value] = self.sheet[key]

    def get_table(self, sheet_name=None):
        return {self.sheet_alias[FUND_SHEET_NAME]: self.sheet[FUND_SHEET_NAME].get_table()}

    def save_table(self, data):
        for key,value in data.items():
            # 每个key对应一个sheet
            self.alias_to_sheet[key].save_table(value)


