


from ib_insync import *
from  configuration.ibtrader_functions import *
from  configuration.ibtrader_settings import * 
from  configuration.ibtrader_stocks import * 
import os, time
from datetime import datetime, timedelta
import yfinance

from dateutil.relativedelta import relativedelta

from flask import Blueprint

historical_blueprint = Blueprint('historical', __name__,)


@historical_blueprint.route('/')
def index():

    #/* BY YEAR 
    #  BY MONTH 
    #   BY WEEK
    #   BY DAY 
    #   BY 5 MINUTES
    #   REALTIME 

    



    # 10 AÑOS MAXIMO 
    #years = 10
    #days_per_year = 365
    #now = datetime.datetime.now()
    #start = datetime.datetime.now() + relativedelta(years=-5)
    end =  datetime.now()


    for contract in ib_trader_contracts: 


        formatted_end = ""


        name = contract.symbol

        print (name)
        ticker = yfinance.Ticker(name)

        formatted_end   = end.strftime('%Y-%m-%d')

        formatted_start = end - relativedelta(years=20)


        #print (formatted_start)
        #print (formatted_end)
        df_d = ticker.history(interval="1d",start=formatted_start ,end  = formatted_end)
        df_w = ticker.history(interval="1wk",start=formatted_start ,end = formatted_end)
        df_m = ticker.history(interval="1mo",start=formatted_start ,end =  formatted_end)


        df_d.to_csv(SETTINGS_REALPATH_STOCK_DATA_DAY   + contract.symbol + '.csv') # + "_" + formatted_end + 
        df_m.to_csv(SETTINGS_REALPATH_STOCK_DATA_MONTH + contract.symbol   + '.csv') # + "_" + formatted_end + 
        df_w.to_csv(SETTINGS_REALPATH_STOCK_DATA_WEEK  + contract.symbol  + '.csv')

    return 'it works!'