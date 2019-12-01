#!flask/bin/python
# -- coding: utf-8 --

__author__ = 'jelly'

from flask import Flask
from flask import render_template

from fund.FundHelper import update_work_book, str_to_bool

import threading
import random
import time

app = Flask(__name__)
app.debug = True
exporting_threads = {}


class ExportingThread(threading.Thread):
    def __init__(self):
        self.progress = 0
        super().__init__()

    def run(self):
        # Your exporting stuff goes here ...
        for _ in range(10):
            time.sleep(1)
            self.progress += 10


@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'} # fake user
    # return render_template("index.html", title='Home', user=user)
    global exporting_threads

    thread_id = random.randint(0, 10000)
    exporting_threads[thread_id] = ExportingThread()
    exporting_threads[thread_id].start()

    print('task id: #%s' % thread_id)
    return render_template("index.html", title='Home', user=user, thread_id=thread_id)


@app.route('/update-excel/')
@app.route('/update-excel/<fast_run>')
def update_excel(fast_run='True'):
    update_work_book('fund/example_filetest.xlsx', str_to_bool(fast_run))
    return 'Click.' + fast_run


@app.route('/progress/<int:thread_id>')
def progress(thread_id):
    global exporting_threads

    return str(exporting_threads[thread_id].progress)


@app.route('/form_data', methods=['GET', 'POST'])
def form_data():
    if request.method=='GET':
        username = request.args.get("username")
        #dumps和loads方法，来自json模块，而json模块是python中的，可以直接导入：
        #而jsonify是flask封装的扩展包
        return jsonify({'status': '0', 'username': username, 'errmsg': '登录成功!'})
    else:
        username = request.form['username']
        return jsonify({'status': '0', 'username': username, 'errmsg': '登录成功!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
