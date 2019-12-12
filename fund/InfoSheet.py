# -*- coding: utf-8 -*-

import openpyxl
from XslxTools import get_cell_value, set_row_data, find_value_row_index, delete_rows, insert_row

INFO_SHEET_NAME = "信息"

WEB_SHOW_COLUMNS = [1, 2, 3, 4, 5, 6, 7, 8]


class InfoSheet(object):
    def __init__(self, wb):
        self.work_book = wb
        self.sheet = wb[INFO_SHEET_NAME]

    def get_table(self):
        result = []
        row_index = 2
        for row in self.sheet.iter_rows(min_row=row_index, max_col=1):
            for cell in row:
                if cell.value is None:  # 遇到空行(id为空)，则后面不再更新
                    break
                row_result = []
                for column in WEB_SHOW_COLUMNS:
                    cell = self.sheet.cell(row=row_index, column=column)
                    value = get_cell_value(self.sheet, cell)
                    row_result.append(value)
                result.append(row_result)
                row_index = row_index + 1
            else:
                # Continue if the inner loop wasn't broken.
                continue
            # Inner loop was broken, break the outer.
            break
        return result

    def save_table(self, data):
        for row_data in data:   # for each row data
            row_index = find_value_row_index(self.sheet, 2, 1, row_data[0])
            if row_index is None:   # 原来不存在添加行
                insert_row(self.sheet, 2, 1, row_data, WEB_SHOW_COLUMNS)
            else:
                set_row_data(self.sheet, row_index, row_data, WEB_SHOW_COLUMNS, 2)


if __name__ == '__main__':
    pass
