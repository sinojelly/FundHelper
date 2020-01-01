#!flask/bin/python
# -- coding: utf-8 --

__author__ = 'jelly'

from flask import Flask, url_for, request, json, jsonify
from flask import render_template, make_response, session, redirect

import threading
import random
import time
import datetime
import os
import subprocess
from datetime import timedelta
import sys
from flask_wtf.csrf import CSRFProtect
from flask import current_app

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
update_status ={}

DEFAULT_USER = 'Guest'
ADMIN_USER = 'Jelly'

FUND_HELPER_DATA_KEY = 'FUND_HELPER_DATA'


def generate_thread_id():
    thread_id = random.randint(0, 10000)

    work_book[thread_id] = FundWorkbook(get_model_name())
    update_status[thread_id] = 'Model'    # 未更新
    # print("thread id:", thread_id, "username: ", session['username'], "model_name:", get_model_name())

    return thread_id


def get_model_name():
    username = session['username']
    data_dir = os.getenv(FUND_HELPER_DATA_KEY, 'fund')
    excel_model = data_dir + "/" + username + "_model.xlsx"
    return excel_model


@app.route('/')
@app.route('/index')
@app.route('/index/<int:thread_id>/')
def index(thread_id=None):
    session.permanent = True
    # session['username'] = DEFAULT_USER
    session.setdefault('username', DEFAULT_USER)   # 如果未设置，则设置为guest，避免KeyError; 如果已设置则不改变

    if thread_id is None:
        try:
            thread_id = generate_thread_id()
        except FileNotFoundError as err:
            return str(err)   # docker服务器重启，会遇到 model 文件找不到
            # FileNotFoundError: [Errno 2]
            # No such file or directory: '/usr/local/fundhelper-data/Guest_model.xlsx'

    # print('task id: #%s' % thread_id)
    if session['username'] == ADMIN_USER:
        return render_template("admin.html", title='Admin', user=session['username'], thread_id=thread_id)
    return render_template("index.html", title='Home', thread_id=thread_id)


@app.route('/update-excel/<int:thread_id>/<int:request_id>')
@app.route('/update-excel/<int:thread_id>/<int:request_id>/<fast_run>')
def update_excel(thread_id, request_id, fast_run='True'):
    # print('update_excel thread id: #%s' % thread_id, "fast_run:", fast_run)
    progress_updater = make_progress_updater(thread_id, request_id)
    is_fast_run = str_to_bool(fast_run)
    update_status[thread_id] = 'Fast' if is_fast_run is True else 'Full'
    work_book[thread_id].update_funds(is_fast_run, progress_updater)
    username = session.get('username')
    if username is None:
        return "No username in session. May be your browser does not support cookie, or there is a bug(android browser has the bug), use firefox instead."
    if username == ADMIN_USER:
        return redirect(url_for('index') + "/" + str(thread_id))
    return download_excel(thread_id)   # 非admin登录，直接下载excel


@app.route('/download-excel/<int:thread_id>/')
def download_excel(thread_id):
    content = work_book[thread_id].download_excel()
    file_name = datetime.datetime.now().strftime("Funds_%Y-%m-%d_%H_%M_%S.xlsx")
    username = session.get('username')
    if username is None:
        return "No username in session. May be your browser does not support cookie, or there is a bug(android browser has the bug), use firefox instead."
    file_name = username + "_" + update_status[thread_id] + "_" + file_name
    response = make_response(content)
    response.headers["Content-Disposition"] = "attachment; filename=" + file_name
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response


def make_progress_updater(thread_id, request_id):
    global progress_current
    global progress_total
    progress_current[(thread_id, request_id)] = 0
    progress_total[(thread_id, request_id)] = 0

    def update_progress(total=None, finished=False):   # total: 第一次调用传回total； finished:最后一次调用传入true,避免永不结束的情况
        global progress_current
        old_value = progress_current.get((thread_id, request_id), 0)
        progress_current[(thread_id, request_id)] = old_value + 1
        if total is not None:
            global progress_total
            global progress_start_time
            progress_total[(thread_id, request_id)] = total
            progress_start_time[(thread_id, request_id)] = datetime.datetime.now()
        if finished and progress_current[(thread_id, request_id)] != progress_total[(thread_id, request_id)]:
            # print("Finished! current =", progress_current[thread_id], "total =", progress_total[thread_id])
            progress_current[(thread_id, request_id)] = progress_total[(thread_id, request_id)]
        # print("thread:", thread_id, "request:", request_id, "total:", progress_total[(thread_id, request_id)],
        # "current:", progress_current[(thread_id, request_id)])
    return update_progress


# 解决第二次点击update不能更新进度的问题，似乎第一次结束时最后一次get process未调用，使得它未清零，
# 下次进来直接返回53/53，进度已结束。有一种解决办法是每次请求生成一个递增数，该数也作为下标。
@app.route('/progress/<int:thread_id>/<int:request_id>')
def progress(thread_id, request_id):
    global progress_current
    global progress_total

    current = progress_current.get((thread_id, request_id), 0)
    total = progress_total.get((thread_id, request_id), 0)
    result = {'current': current, 'total': total, 'time': 0}
    start_time = progress_start_time.get((thread_id, request_id), None)
    # print("start time:", start_time)
    if current >= total and start_time is not None:
        result['time'] = (datetime.datetime.now() - start_time).seconds
    # print("get progress in thread:", thread_id, result)
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
            current_app.logger.info("admin log in success.")
            thread_id = generate_thread_id()
            return render_template("admin.html", title='Admin', user=username, thread_id=thread_id)
        else:
            session['username'] = DEFAULT_USER
            print("log in fail.")
            current_app.logger.info("log in fail.")
            thread_id = generate_thread_id()
            return render_template("guest.html", title='Guest', user=username, thread_id=thread_id)


@app.route('/load-fund-data/<int:thread_id>')
def load_fund_data(thread_id):
    # print("load fund data .....", thread_id)
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


def run_external_cmd(cmd, msg_in=''):
    try:
        proc = subprocess.Popen(cmd,
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                )
        stdout_value, stderr_value = proc.communicate(msg_in)
        return stdout_value, stderr_value, proc.returncode
    except ValueError as err:
        # print("ValueError: %s" % err)
        return "ValueError exception.".encode(encoding='utf-8'), err.encode(encoding='utf-8'), -1000
    except IOError as err:
        # print("IOError: %s" % err)
        return "IOError exception.".encode(encoding='utf-8'), err.encode(encoding='utf-8'), -1000


def run_git_submit(work_dir):
    # git_cmd = "\"D:\\Program Files\\Git\\bin\git.exe\" --git-dir=" + work_dir + "/.git --work-tree=" + work_dir + " "
    git_cmd = "git --git-dir=" + work_dir + "/.git --work-tree=" + work_dir + " "
    commit_cmd = git_cmd + "commit -am \"automatically submit.\""
    push_cmd = git_cmd + "push"
    # status_cmd = git_cmd + "status"
    cmd = commit_cmd + " & " + push_cmd  # + " & " + status_cmd
    # result = os.popen(cmd).read()
    stdout_value, stderr_value, returncode = run_external_cmd(cmd)
    # print(stdout_value.decode())
    # print("---------------err-------------")
    # print(stderr_value.decode())
    # print('returncode', returncode)
    return stdout_value.decode("utf8", "ignore"), stderr_value.decode("utf8", "ignore"), returncode


@app.route('/git-submit/<int:thread_id>', methods=['GET'])
def git_submit(thread_id):
    # work_dir = "D:\\Develop\\projects\\web-projects\\fundhelper-data"
    work_dir = "/usr/local/fundhelper-data"
    stdout_value, stderr_value, returncode = run_git_submit(work_dir)
    return jsonify({'stdout': stdout_value, 'stderr':stderr_value, 'returncode':returncode})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
