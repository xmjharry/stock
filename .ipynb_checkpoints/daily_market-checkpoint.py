import random
from faker import Factory
import argparse
from sqlalchemy import create_engine, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import Column, String, Integer, Text, Date, DECIMAL
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os
import tushare as ts
from dateutil.parser import parse
import decimal
import time
import pandas as pd
import numpy as np
import sys
from tqdm import tqdm
from collections.abc import Iterable
import logger
import inspect
import ifttt

engine = create_engine('mysql+pymysql://root:Xuki574325507@localhost:3306/stock?charset=utf8')
Base = declarative_base()
TOKEN = '04beaad46e3ff10b1970c6c3c8d729e87cf7d92ecb86f2c9d1574b4a'
ts.set_token(TOKEN)
pro = ts.pro_api()
log = logger.Logger('./log/stock', level='info')


class DailyIndex(Base):
    """每日指标"""
    __tablename__ = f'{datetime.datetime.today().year}_daily_index'

    id = Column(Integer, primary_key=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    close = Column(DECIMAL(50, 10))
    turnover_rate = Column(DECIMAL(50, 10))
    turnover_rate_f = Column(DECIMAL(50, 10))
    volume_ratio = Column(DECIMAL(50, 10))
    pe = Column(DECIMAL(50, 10))
    pe_ttm = Column(DECIMAL(50, 10))
    pb = Column(DECIMAL(50, 10))
    ps = Column(DECIMAL(50, 10))
    ps_ttm = Column(DECIMAL(50, 10))
    total_share = Column(DECIMAL(50, 10))
    float_share = Column(DECIMAL(50, 10))
    free_share = Column(DECIMAL(50, 10))
    total_mv = Column(DECIMAL(50, 10))
    circ_mv = Column(DECIMAL(50, 10))

    def __repr__(self):
        return '%s(%s,%s,%s)' % (self.__class__.__name__, self.trade_date, self.ts_code, self.close)


def get_daily_index_data(trade_start_date: str, trade_end_date: str, max_times: int = 3) -> Iterable:
    trade_start_date = parse(trade_start_date).date()
    trade_end_date = parse(trade_end_date).date()
    trade_date = trade_start_date

    pbar = tqdm(total=(trade_end_date - trade_start_date).days + 1)

    while True:
        times = 1
        if trade_date > trade_end_date:
            yield None
            break
        while True:
            try:
                if times > max_times:
                    log.logger.info(f'方法：{inspect.stack()[0][3]}，获取{trade_date.strftime("%Y-%m-%d")}数据失败')
                    data = pd.DataFrame()
                    break
                data = pro.query('daily_basic', trade_date=trade_date.strftime('%Y%m%d'))
                log.logger.info(f'方法：{inspect.stack()[0][3]}，获取{trade_date.strftime("%Y-%m-%d")}数据成功')
            except Exception as e:
                print(e)
                log.logger.info(f'方法：{inspect.stack()[0][3]}，获取{trade_date.strftime("%Y-%m-%d")}数据{times}次失败，e={e}')
                times = times + 1
            else:
                break
        rows, _ = data.shape
        if rows > 0:
            for row in range(0, rows):
                item_data = {}
                for key, value in data.iloc[row].items():
                    if not hasattr(DailyIndex,key):
                        continue
                    if pd.isnull(value):
                        value = '0'
                    if key == 'trade_date':
                        item_data[key] = parse(value).date()
                    elif key == 'ts_code':
                        item_data[key] = value
                    else:
                        item_data[key] = decimal.Decimal(str(value))
                yield DailyIndex(**item_data)
            yield None
            log.logger.info(f'方法：{inspect.stack()[0][3]}，插入{trade_date.strftime("%Y-%m-%d")}数据成功')
        else:
            log.logger.info(f'{trade_date.strftime("%Y-%m-%d")}数据为空')
        trade_date = trade_date + datetime.timedelta(1)
        pbar.update(1)
        yield None
    pbar.close()


class DailyQuotation(Base):
    """每日行情"""
    __tablename__ = f'{datetime.datetime.today().year}_daily_quotation'

    id = Column(Integer, primary_key=True)
    ts_code = Column(String(20), nullable=False, index=True, comment='股票代码')
    trade_date = Column(Date, nullable=False, index=True, comment='交易日期')
    open = Column(DECIMAL(50, 10), comment='开盘价')
    high = Column(DECIMAL(50, 10), comment='最高价')
    low = Column(DECIMAL(50, 10), comment='最低价')
    close = Column(DECIMAL(50, 10), comment='收盘价')
    pre_close = Column(DECIMAL(50, 10), comment='昨收价')
    change = Column(DECIMAL(50, 10), comment='涨跌额')
    pct_chg = Column(DECIMAL(50, 10), comment='涨跌幅（未复权，如果是复权请用 通用行情接口）')
    vol = Column(DECIMAL(50, 10), comment='成交量（手）')
    amount = Column(DECIMAL(50, 10), comment='成交额（千元）')

    def __repr__(self):
        return '%s(%s,%s,%s)' % (self.__class__.__name__, self.trade_date, self.ts_code, self.close)


def get_daily_quotation_data(trade_start_date: str, trade_end_date: str, max_times: int = 3) -> Iterable:
    trade_start_date = parse(trade_start_date).date()
    trade_end_date = parse(trade_end_date).date()
    trade_date = trade_start_date

    pbar = tqdm(total=(trade_end_date - trade_start_date).days + 1)
    while True:
        times = 1
        if trade_date > trade_end_date:
            yield None
            break
        while True:
            try:
                if times > max_times:
                    ifttt.send(f'获取{trade_date.strftime("%Y-%m-%d")}数据失败。')
                    log.logger.info(f'方法：{inspect.stack()[0][3]}，获取{trade_date.strftime("%Y-%m-%d")}数据失败')
                    data = pd.DataFrame()
                    break
                data = pro.query('daily', trade_date=trade_date.strftime('%Y%m%d'))
                log.logger.info(f'方法：{inspect.stack()[0][3]}，获取{trade_date.strftime("%Y-%m-%d")}数据成功')
            except Exception as e:
                print(e)
                log.logger.info(f'方法：{inspect.stack()[0][3]}，获取{trade_date.strftime("%Y-%m-%d")}数据{times}次失败，e={e}')
                times = times + 1
            else:
                break
        rows, _ = data.shape
        if rows > 0:
            for row in range(0, rows):
                item_data = {}
                for key, value in data.iloc[row].items():
                    if not hasattr(DailyQuotation,key):
                        continue
                    if pd.isnull(value):
                        value = '0'
                    if key == 'trade_date':
                        item_data[key] = parse(value).date()
                    elif key == 'ts_code':
                        item_data[key] = value
                    else:
                        item_data[key] = decimal.Decimal(str(value))
                yield DailyQuotation(**item_data)
            yield None
            log.logger.info(f'方法：{inspect.stack()[0][3]}，插入{trade_date.strftime("%Y-%m-%d")}数据成功')
        else:
            log.logger.info(f'{trade_date.strftime("%Y-%m-%d")}数据为空')
        trade_date = trade_date + datetime.timedelta(1)
        pbar.update(1)
        yield None
    pbar.close()


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    parser = argparse.ArgumentParser()
    parser.add_argument('--trade_start_date', help='开始时间eg:20191010', default=datetime.date.today().strftime('%Y%m%d'))
    parser.add_argument('--trade_end_date', help='结束时间eg:20191012', default=datetime.date.today().strftime('%Y%m%d'))
    args = parser.parse_args()
    _trade_start_date = args.trade_start_date
    _trade_end_date = args.trade_end_date

    for item in get_daily_index_data(_trade_start_date, _trade_end_date):
        if item is None:
            session.commit()
        else:
            session.add(item)

    for item in get_daily_quotation_data(_trade_start_date, _trade_end_date):
        if item is None:
            session.commit()
        else:
            session.add(item)

    session.close()
    ifttt.send(f'开始时间：{parse(_trade_start_date).strftime("%Y-%m-%d")}，结束时间：{parse(_trade_end_date).strftime("%Y-%m-%d")}，数据插入成功。')
