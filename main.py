#!flask/bin/python
# -- coding: utf-8 --

__author__ = 'jelly'

from flask import Flask, url_for, request, json, jsonify
from flask import render_template, make_response, session

import threading
import random
import time
import datetime
import os
from datetime import timedelta
import sys
from flask_wtf.csrf import CSRFProtect

sys.path.append(os.path.join(os.getcwd(), 'fund'))

from FundHelper import update_work_book, str_to_bool
from FundWorkbook import FundWorkbook


app = Flask(__name__)
CSRFProtect(app)

app.config['SECRET_KEY'] = os.urandom(24)  # 设置为24位的字符,每次运行服务器都是不同的，所以服务器启动一次上次的session就清除。
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 设置session的保存时间。
# 添加数据到session
# 操作的时候更操作字典是一样的
# secret_key:----------盐，为了混淆加密。

progress_current = {}   # 当前处理到的步骤序号
progress_total = {}     # 所有步骤总数
progress_start_time = {}      # 记录开始时间

work_book = {}

DEFAULT_USER = 'Guest'
ADMIN_USER = 'Jelly'


def generate_thread_id():
    thread_id = random.randint(0, 10000)

    global progress_current
    global progress_total
    global progress_start_time
    progress_current[thread_id] = 0
    progress_total[thread_id] = 0
    progress_start_time[thread_id] = None
    work_book[thread_id] = FundWorkbook(get_model_name())
    print("thread id:", thread_id, "username: ", session['username'], "model_name:", get_model_name())

    return thread_id


def get_model_name():
    username = session['username']
    excel_model = "fund/" + username + "_model.xlsx"
    return excel_model


@app.route('/')
@app.route('/index')
def index():
    session.permanent = True
    # session['username'] = DEFAULT_USER
    session.setdefault('username', DEFAULT_USER)   # 如果未设置，则设置为guest，避免KeyError; 如果已设置则不改变

    thread_id = generate_thread_id()

    print('task id: #%s' % thread_id)
    if session['username'] == ADMIN_USER:
        return render_template("admin.html", title='Admin', user=session['username'], thread_id=thread_id)
    return render_template("index.html", title='Home', thread_id=thread_id)


@app.route('/update-excel/<int:thread_id>/')
@app.route('/update-excel/<int:thread_id>/<fast_run>')
def update_excel(thread_id, fast_run='True'):
    print('update_excel thread id: #%s' % thread_id, "fast_run:", fast_run)
    progress_updater = make_progress_updater(thread_id)
    is_fast_run = str_to_bool(fast_run)
    content = update_work_book(get_model_name(), is_fast_run, progress_updater)
    file_name = datetime.datetime.now().strftime("Funds_%Y-%m-%d_%H_%M_%S.xlsx")
    if is_fast_run:
        file_name = username + "_Fast_" + file_name
    else:
        file_name = username + "_Full_" + file_name
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


# get :  username = request.args.get("username")
@app.route('/user-login', methods=['POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username == ADMIN_USER or username == 'jelly') and password == '$henF@n':   # 允许j为小写
            session['username'] = ADMIN_USER
            print("admin log in success.")
            thread_id = generate_thread_id()
            return render_template("admin.html", title='Admin', user=username, thread_id=thread_id)
        else:
            session['username'] = DEFAULT_USER
            print("log in fail.")
            thread_id = generate_thread_id()
            return render_template("guest.html", title='Guest', user=username, thread_id=thread_id)


@app.route('/load-fund-data/<int:thread_id>')
def load_fund_data(thread_id):
    print("load fund data .....", thread_id)
    # result = {'data': [["005911", "广发双擎升级混合", "5", "2.0368", "0.17", "-15.21", "20191021", "-1.02", "20191120"]]} # 必须是两重数组
    result = work_book[thread_id].get_table()
    return jsonify(result)


@app.route('/save-data/<int:thread_id>', methods=['POST'])
def save_data(thread_id):
    print("save data .....", thread_id)
    if request.method == 'POST':
        # data = request.form['data']
        # data = request.form.get('data', None)
        # print("type of request.get_json(): ", type(request.get_json()))
        work_book[thread_id].save_table(request.get_json())
    result = {'result': 'ok'}
    return jsonify(result)


@app.route('/update-model', methods=['GET'])
def update_model():
    if request.method == 'GET':
        fund_id_str = request.args.get('fund_id', default='', type=str)
        fund_level_str = request.args.get('fund_level', default='', type=str)
        fund_high_date_str = request.args.get('fund_high_date', default='', type=str)
        fund_low_date_str = request.args.get('fund_low_date', default='', type=str)
        remove_fund_id_str = request.args.get('remove_fund_id', default='', type=str)
        fund_ids = fund_id_str.split(' ')
        fund_levels = fund_level_str.split(' ')
        fund_high_dates = fund_high_date_str.split(' ')
        fund_low_dates = fund_low_date_str.split(' ')
        remove_fund_ids = remove_fund_id_str.split(' ')
        print("fund_id_str:", fund_ids)
        print("fund_level_str",fund_levels)
        print("fund_high_date_str",fund_high_dates)
        print("fund_low_date_str", fund_low_dates)
        print("remove_fund_id_str", remove_fund_ids)
    print("000000000 - update model")
    return jsonify({'msg': 'finished'})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
