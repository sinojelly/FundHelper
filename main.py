#!flask/bin/python
# -- coding: utf-8 --

__author__ = 'jelly'

from flask import Flask, url_for, request, json, jsonify
from flask import render_template, make_response

from fund.FundHelper import update_work_book, str_to_bool

import threading
import random
import time
import datetime

app = Flask(__name__)

progress_current = {}   # 当前处理到的步骤序号
progress_total = {}     # 所有步骤总数
progress_start_time = {}      # 记录开始时间


@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'} # fake user

    thread_id = random.randint(0, 10000)

    global progress_current
    global progress_total
    global progress_start_time
    progress_current[thread_id] = 0
    progress_total[thread_id] = 0
    progress_start_time[thread_id] = None

    print('task id: #%s' % thread_id)
    return render_template("index.html", title='Home', user=user, thread_id=thread_id)


@app.route('/update-excel/<int:thread_id>/')
@app.route('/update-excel/<int:thread_id>/<fast_run>')
def update_excel(thread_id, fast_run='True'):
    print('update_excel thread id: #%s' % thread_id, "fast_run:", fast_run)
    progress_updater = make_progress_updater(thread_id)
    is_fast_run = str_to_bool(fast_run)
    content = update_work_book('fund/example_filetest.xlsx', is_fast_run, progress_updater)
    file_name = datetime.datetime.now().strftime("Funds_%Y-%m-%d_%H_%M_%S.xlsx")
    if is_fast_run:
        file_name = "Fast_" + file_name
    else:
        file_name = "Full_" + file_name
    response = make_response(content)
    response.headers["Content-Disposition"] = "attachment; filename=" + file_name
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response


def make_progress_updater(thread_id):
    global progress_current
    global progress_total
    progress_current[thread_id] = 0
    progress_total[thread_id] = 0

    def update_progress(total=None, finished=False):   # total: 第一次调用传回total； finished:最后一次调用传入true,避免永不结束的情况
        global progress_current
        progress_current[thread_id] += 1
        if total is not None:
            global progress_total
            global progress_start_time
            progress_total[thread_id] = total
            progress_start_time[thread_id] = datetime.datetime.now()
        if finished and progress_current[thread_id] != progress_total[thread_id]:
            print("Finished! current =", progress_current[thread_id], "total =", progress_total[thread_id])
            progress_current[thread_id] = progress_total[thread_id]
        print("thread:", thread_id, "total:", progress_total[thread_id], "current:", progress_current[thread_id])
    return update_progress


@app.route('/progress/<int:thread_id>')
def progress(thread_id):
    global progress_current
    global progress_total

    print("get progress in thread:", thread_id)
    # return str(exporting_threads[thread_id].progress)
    result = {'current': progress_current[thread_id], 'total': progress_total[thread_id], 'time': 0}
    if progress_current[thread_id] >= progress_total[thread_id] and progress_start_time[thread_id] is not None:
        result['time'] = (datetime.datetime.now() - progress_start_time[thread_id]).seconds
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
