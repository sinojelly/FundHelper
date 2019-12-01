#!flask/bin/python
# -- coding: utf-8 --

__author__ = 'jelly'

from flask import Flask
from flask import render_template

from fund.FundHelper import update_work_book, str_to_bool

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'} # fake user
    return render_template("index.html", title='Home', user=user)


@app.route('/update-excel/')
@app.route('/update-excel/<fast_run>')
def update_excel(fast_run='True'):
    update_work_book('example_filetest.xlsx', str_to_bool(fast_run))
    return 'Click.' + fast_run


if __name__ == '__main__':
    app.run(host='0.0.0.0')
