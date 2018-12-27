# coding: utf-8
import re
import datetime
import os

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from werkzeug.contrib.cache import FileSystemCache
import requests

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('fund', __name__)
cache = FileSystemCache('cache')


@bp.route('/')
@login_required
def index():
    funds = get_all_funds()

    return render_template('fund/index.html', funds=funds)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':
        code = request.form['code']
        is_monitor = request.form.get('is_monitor', "0")
        db = get_db()
        error = None

        if db.execute('SELECT * FROM fund WHERE code=?', (code,)
                      ).fetchone() is not None:
            error = 'code {} 已经存在'.format(code)

        if error is None:
            db.execute('INSERT INTO fund (code, is_monitor) VALUES (?, ?)', (code, int(is_monitor)))
            db.commit()
            return redirect(url_for('index'))

        flash(error)

    return render_template('fund/add.html')


@bp.route('/<int:id>/edit', methods=('POST', 'GET'))
@login_required
def edit(id):
    fund = get_fund(id)

    if request.method == 'POST':
        is_monitor = request.form.get('is_monitor', "0")
        db = get_db()
        db.execute('UPDATE fund SET is_monitor=? where id=?', (int(is_monitor), id))
        db.commit()

        return redirect(url_for('index'))

    return render_template('fund/edit.html', fund=fund)


@bp.route('/<int:id>/delete', methods=('POST', 'GET'))
@login_required
def delete(id):
    fund = get_fund(id)

    if request.method == 'POST':
        db = get_db()
        db.execute('DELETE from fund where id=?', (id,))
        db.commit()

        flash('delete code {} successful!'.format(fund['code']))
        return redirect(url_for('index'))


@bp.route('/chart')
@login_required
def fund_chart():
    code = request.args.get('code')
    data = {}
    if code:
        x, y = get_fund_data(code)
        data[code] = {'x': x, 'y': y}
        return render_template('fund/chart.html', data=data)
    else:
        funds = get_all_funds()
        data = get_chart_data(funds)
        return render_template('fund/chart.html', data=data)


@bp.route('/clear_cache')
@login_required
def clear_cache():
    cache.clear()
    flash('cache cleared')
    return redirect(url_for('index'))


def get_chart_data(funds):
    data = cache.get('data')
    if data is None:
        data = {}
        for fund in funds:
            x, y = get_fund_data(fund['code'])
            data[fund['code']] = {'x': x, 'y': y}
        cache.set('data', data, 2*60*60)
    return data


def get_fund(id):
    fund = get_db().execute('SELECT id, code, is_monitor FROM fund WHERE id=?', (id,)
                            ).fetchone()
    if fund is None:
        abort(404)

    return fund


def get_all_funds():
    funds = get_db().execute(
        'SELECT id, code, is_monitor, datetime(add_time,"localtime") as add_time, datetime(update_time, "localtime") as update_time'
        ' FROM fund'
        ' ORDER BY  is_monitor desc, update_time desc').fetchall()

    return funds


def get_fund_data(code):
    url = 'http://fund.eastmoney.com/pingzhongdata/{}.js'.format(code)
    pattern = re.compile(r'var Data_netWorthTrend = (.*);/\*累计净值走势\*/')

    res = requests.get(url)
    if res.status_code != 200:
        return 0, 0
    content = re.findall(pattern, res.text)[0]
    data = eval(content)

    timestamp = [i.get('x') for i in data][-400:]
    y = [i.get('y') for i in data][-400:]
    x = [datetime.datetime.fromtimestamp(i/1000).strftime('%Y-%m-%d') for i in timestamp]

    return x, y



