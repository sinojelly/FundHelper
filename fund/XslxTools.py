# -*- coding: utf-8 -*-

from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles.fills import PatternFill
from openpyxl.styles import Font


# 设置positive, negative 条件格式
def set_p_n_condition(sheet, cell):
    red_text = Font(color="AA110D")
    red_fill = PatternFill(start_color='AA110D', end_color='FFC7CE', fill_type='solid')
    sheet.conditional_formatting.add(cell.coordinate, CellIsRule(operator='greaterThan', formula=['0'], stopIfTrue=True, font=red_text, fill=red_fill))
    green_text = Font(color="006100")
    green_fill = PatternFill(start_color='006100', end_color='C6EFCE', fill_type='solid')
    sheet.conditional_formatting.add(cell.coordinate, CellIsRule(operator='lessThan', formula=['0'], stopIfTrue=True, font=green_text, fill=green_fill))


def get_non_none_value(value):
    if value is None:
        return ''
    return value
