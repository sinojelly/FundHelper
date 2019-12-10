# -*- coding: utf-8 -*-

from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles.fills import PatternFill
from openpyxl.styles import Font
# from openpyxl.cell.cell import TYPE_FORMULA
import re


# 设置positive, negative 条件格式
def set_p_n_condition(sheet, cell):
    red_text = Font(color="AA110D")
    red_fill = PatternFill(start_color='AA110D', end_color='FFC7CE', fill_type='solid')
    sheet.conditional_formatting.add(cell.coordinate, CellIsRule(operator='greaterThan', formula=['0'], stopIfTrue=True, font=red_text, fill=red_fill))
    green_text = Font(color="006100")
    green_fill = PatternFill(start_color='006100', end_color='C6EFCE', fill_type='solid')
    sheet.conditional_formatting.add(cell.coordinate, CellIsRule(operator='lessThan', formula=['0'], stopIfTrue=True, font=green_text, fill=green_fill))


def get_cell_value(sheet, cell, default=''):
    if cell.value is None:
        return default
    if cell.data_type is not cell.TYPE_FORMULA:
        return cell.value

    #计算公式
    formula = cell.value[1:]  # 去掉等号
    match = re.match(".*?([A-Z]\d+).*?([A-Z]\d+).*?([A-Z]\d+).*", formula)
    for address in match.groups():
        formula = formula.replace(address, str(sheet[address].value))
    value = eval(formula)
    return value


def set_cell_value(cell, value):
    if cell.data_type is cell.TYPE_FORMULA:
        return       # not change the formula
    cell.value = value


def find_value_row_index(sheet, start_row, col, value):
    for row in sheet.iter_rows(min_row=start_row, min_col=col, max_col=col):
        for cell in row:
            if str(cell.value) == str(value):
                return cell.row
    return None


# 把col列为value的行都删除
def delete_rows(sheet, start_row, col, value):
    while True:
        row_index = find_value_row_index(sheet, start_row, col, value)
        if row_index is None:
            break
        sheet.delete_rows(row_index, 1)   # 删除一行


def find_last_row_index(sheet, start_row, col):
    row_index = start_row
    for row in sheet.iter_rows(min_row=start_row, min_col=col, max_col=col):
        for cell in row:
            if cell.value is None or str(cell.value).strip() == '':    # 找到None或该单元格内容为空，认为到达最后一行
                return cell.row
        row_index += 1
    return row_index


def set_row_data(sheet, row_index, data, columns):
    array_index = 0
    for column in columns:
        cell = sheet.cell(row=row_index, column=column)
        set_cell_value(cell, data[array_index])
        array_index += 1


# 在最后一行后面插入一行
def insert_row(sheet, start_row, id_col, data, columns):
    last_row_index = find_last_row_index(sheet, start_row, id_col)
    set_row_data(sheet, last_row_index, data, columns)

