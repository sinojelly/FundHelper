# -*- coding: utf-8 -*-

import openpyxl

from openpyxl.styles.numbers import FORMAT_NUMBER_00
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles.fills import PatternFill

from fund.XslxTools import set_p_n_condition


INVEST_SHEET_NAME = "投资"

INVEST_COLUMN_START = 6
INVEST_ROW_START = 3


class InvestSheet(object):
    def __init__(self, wb):
        self.work_book = wb
        self.sheet = wb[INVEST_SHEET_NAME]
        self.stock_sheets = {}

    def get_price_sheet(self, row):
        price_sheet_name = self.sheet.cell(column=1, row=row).value
        # print("row", row)
        # print("price_sheet_name", price_sheet_name)
        price_sheet = self.stock_sheets[price_sheet_name]
        return price_sheet

    def get_fund_or_stockindex_id(self, row):
        fund_id = self.sheet.cell(column=2, row=row).value
        # print("get_fund_or_stockindex_id", fund_id)
        return fund_id

    def get_invest_price(self, row, column):
        price_sheet = self.get_price_sheet(row)
        invest_time = str(self.sheet.cell(column=column, row=2).value)
        invest_price, fund_name = price_sheet.get_invest_price(self.get_fund_id(row), invest_time)
        return invest_price, fund_name

    def get_current_price(self, row):
        price_sheet = self.get_price_sheet(row)

        item_id = self.get_fund_or_stockindex_id(row)
        price = price_sheet.get_current_price(item_id)

        if price is None:
            print("get_current_price fail, row =", row, ", id =", item_id)

        return price

    def process_one_invest(self, row):
        price = self.get_current_price(row)
        if price is None:
            return
        total_invest = 0
        total_income = 0
        need_process = True
        for col in self.sheet.iter_cols(min_row=row, max_row=row, min_col=INVEST_COLUMN_START):
            for cell in col:
                if not need_process:   # 跳过一列，再处理。因为每一组投资都是两列
                    need_process = True
                    continue
                need_process = False
                if cell.value is None:  # 跳过未填写的
                    continue
                invest_amount = float(cell.value)

                invest_price = self.sheet.cell(column=int(cell.col_idx)+1, row=row).value
                if invest_price is None:
                    invest_price, fund_name = self.get_invest_price(row, cell.col_idx)
                    # print("invest_price", invest_price, "fund_name", fund_name)
                    if invest_price is not None:
                        self.sheet.cell(column=int(cell.col_idx) + 1, row=row).value = float(invest_price)  # 写入投资价格
                        self.sheet.cell(column=3, row=row).value = fund_name    # 写入基金名称(指数对应的组合名称不能自动写入)
                if invest_price is None:  # 跳过查询不到投资价格的
                    continue
                invest_price = float(invest_price)

                if invest_amount > 0:
                    total_invest = total_invest + invest_amount
                    ratio = (price - invest_price)/invest_price
                    income = invest_amount * ratio
                    total_income = total_income + income
                    income_cell = self.sheet.cell(column=int(cell.col_idx), row=row + 1)
                    income_cell.value = income
                    income_cell.number_format = FORMAT_NUMBER_00
                    set_p_n_condition(self.sheet, income_cell)
                    ratio_cell = self.sheet.cell(column=int(cell.col_idx) + 1, row=row + 1)
                    ratio_cell.value = ratio * 100  # ratio
                    ratio_cell.number_format = FORMAT_NUMBER_00
                    set_p_n_condition(self.sheet, ratio_cell)
                elif invest_amount < 0:    # 表示后面的投资都已经卖掉了
                    break
            else:
                # Continue if the inner loop wasn't broken.
                continue
            # Inner loop was broken, break the outer.
            break
            # https://stackoverflow.com/questions/189645/how-to-break-out-of-multiple-loops

        if total_invest != 0:
            self.sheet.cell(column=4, row=row).value = total_invest    # 总投资额
            self.sheet.cell(column=5, row=row).value = price           # 当前价格/点数
            self.sheet.cell(column=4, row=row + 1).value = total_income   # 总收益
            self.sheet.cell(column=4, row=row + 1).number_format = FORMAT_NUMBER_00
            set_p_n_condition(self.sheet, self.sheet.cell(column=4, row=row + 1))
            self.sheet.cell(column=5, row=row + 1).value = total_income / total_invest * 100   # 总收益率
            self.sheet.cell(column=5, row=row + 1).number_format = FORMAT_NUMBER_00
            set_p_n_condition(self.sheet, self.sheet.cell(column=5, row=row + 1))

    def update_all_invests(self, *stock_sheets):
        for stock_sheet in stock_sheets:
            self.stock_sheets[stock_sheet.get_sheet_name()] = stock_sheet

        need_process = True
        for col in self.sheet.iter_cols(min_row=INVEST_ROW_START, min_col=1, max_col=1):
            for cell in col:
                if not need_process:  # 跳过一行，再处理。因为每一组投资都是两行
                    need_process = True
                    continue
                need_process = False
                if cell.value is None:  # 跳过未填写的
                    break
                self.process_one_invest(int(cell.row))

    def get_fund_id(self, row):
        category = self.sheet.cell(row=row, column=1).value
        if category is not None and category == "基金":
            return self.sheet.cell(row=row, column=2).value
        return None

    def get_all_funds(self):
        invested_funds = []
        need_process = True
        for col in self.sheet.iter_cols(min_row=INVEST_ROW_START, min_col=1, max_col=1):
            for cell in col:
                if not need_process:  # 跳过一行，再处理。因为每一组投资都是两行
                    need_process = True
                    continue
                need_process = False
                if cell.value is None:  # 跳过未填写的
                    break
                fund_id = self.get_fund_id(int(cell.row))
                if fund_id is not None:
                    invested_funds.append(str(fund_id))
        return invested_funds


if __name__ == '__main__':
    wb = openpyxl.load_workbook('example_filetest2.xlsx')
    import StockIndexSheet
    stock_index_sheet = StockIndexSheet.StockIndexSheet(wb)
    invest_sheet = InvestSheet(wb)
    # my_funds = invest_sheet.get_all_funds()
    # print(my_funds)
    invest_sheet.update_all_invests(stock_index_sheet)
    wb.save('example_filetest2.xlsx')
