


import pandas as pd

#from ib_insync import *

#from  configuration.stock_data_class import * 
from  configuration.timeframe_class import * 
from  configuration.ibtrader_functions import *
from  configuration.ibtrader_settings import * 
from  configuration.ibtrader_stocks import * 
import matplotlib.dates as mpl_dates
import pandas_ta as ta

# DATOS 
# SYMBOL
# SUPPORT
# RESISTANCE
# LAST_PRICE
# SMA           ¿200?
# PERIOD DAILY WEEKLY O MONTHLY
# DIV_TYPE  BAJISTA O ALCISTA 
# DIV_DATE1
# DIV_DATE2
# DIV_MACD    (S/N)
# DIV_INDICATOR  RSI (S/N)
# MACD_VALUE    (S/N)
# RSI_VALUE    (S/N)

# LO SUBIMOS A S3 SI ESTA EN UNA INSTANCIA DE AMAZON Y TIENE LA INSTANCIA EL ROLE ASOCIADO PARA AUTENTICAR CONTRA S3 CON SU IAM ROLE, NADA DE USUARIOS 

from flask import Blueprint

support_resistance_blueprint = Blueprint('support_resistance', __name__,)


@support_resistance_blueprint.route('/')
def index():
  
    # solo si hay divergencias 
    dfIBTrader =  pd.DataFrame(columns=['SYMBOL','SUPPORT','SUPPORT_DATE','RESISTANCE','RESISTANCE_DATE','LAST_PRICE','PRICE_IN_RANGE', 'SMA','PERIOD','DIV_MAC_TYPE','DIV_RSI_TYPE',
    'DIV_MACD_DATE1', 'DIV_MACD_DATE2','DIV_RSI_DATE1', 'DIV_RSI_DATE2', 'MACD_VALUE','RSI_VALUE','LINK'])

    #https://es.tradingview.com/chart?symbol=NYSE%3AV

    # https://compraraccionesdebolsa.com/formacion/tecnico/indicadores/divergencias-ocultas/
    for contract in ib_trader_contracts: 

        for period in IBTraderTimeFrame.list():   
            # WEEKLY   
            #         
            file_data = getFile(contract.symbol,period)           
            dfDataTimeFrame = getData(file_data)        
            dfOriginalDataTimeFrame = dfDataTimeFrame.copy()
            print (contract.symbol + "-" + period)
            #class StockDataFields(Enum):
            #HIGH  = StockDataFields.HIGH
            #LOW  = StockDataFields.LOW
            #VOLUME = "volume"
            #DATE = StockDataFields.DATE

            last_resistance_value  = 0
            last_resistance_date  = 0
            last_support_value  = 0
            last_support_date  =  0

            resistance_levels, support_levels = getSupportResistances(dfDataTimeFrame)
            if len(resistance_levels)>0:
                last_resistance_value  = dfDataTimeFrame.iloc[resistance_levels[-1][0]][StockDataFields.HIGH.value]
                last_resistance_date  = dfDataTimeFrame.iloc[resistance_levels[-1][0]][StockDataFields.DATE.value]
            if len(support_levels)>0:
                last_support_value  = dfDataTimeFrame.iloc[support_levels[-1][0]][StockDataFields.HIGH.value]
                last_support_date  = dfDataTimeFrame.iloc[support_levels[-1][0]][StockDataFields.DATE.value]

            last_price   = dfOriginalDataTimeFrame[StockDataFields.CLOSE.value].iat[-1]          
            DIV_macd_type = ""   
            DIV_macd_date1 = ""
            DIV_macd_date2 = ""
            DIV_rsi_type = ""   
            DIV_rsi_date1 = ""
            DIV_rsi_date2 = ""
            bDIV_macd = False
            bDIV_rsi  = False
            sma = 0 
            macd_value = 0
            rsi_value = 0
            last_price_between_supp_resist = 0
            if last_price > last_support_value and last_price  < last_resistance_value:
                last_price_between_supp_resist = 1

            peak_levels_macd  =  []
            valley_levels_macd = []
            dfsma  = pd.DataFrame()
            dfmacd = pd.DataFrame()
            dfrsi  = pd.DataFrame()
            try:
                dfsma  =  dfDataTimeFrame.ta.sma(length=50, append=True) # 200 periodos en mensual es complicado que haya info, ponemos 50
                dfmacd =  dfDataTimeFrame.ta.macd(fast=12, slow=26, signal=9, min_periods=None, append=True)
                dfrsi  =  dfDataTimeFrame.ta.rsi(length=14, append=True)
                sma = dfsma[dfsma.size-1]            
                # For example, MACD(fast=12, slow=26, signal=9) will return a DataFrame with columns: ['MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9'].
                macd_value = dfmacd.MACD_12_26_9.iat[-1]  # AQUI SACAMOS EL MACD , DIVERGENCIA POR HISTOGRAMA

                rsi_value = dfrsi[dfrsi.size-1]

                peak_levels_macd,valley_levels_macd = getIndicatorPeaksValleys(dfmacd,"MACD_12_26_9")  #  MACDH_12_26_9
            except IndexError as error2:
                print(error2)
                print("'Error calculating indicators for  " + contract.symbol + "-" + period)      
                continue          
            except AssertionError as error:
                print(error)
                print("'Error calculating indicators for  " + contract.symbol + "-" + period)                    
                continue

            # MACD 
            dfDivergenceUpperMACD = getIndexUpperDivergence(dfOriginalDataTimeFrame,support_levels,valley_levels_macd)
            dfDivergenceLowerMACD = getIndexLowerDivergence(dfOriginalDataTimeFrame,resistance_levels,peak_levels_macd)

            if not dfDivergenceUpperMACD.empty:

                    bDIV_macd = True    
                    DIV_macd_type = "UPPER"
                    # NOS QUEDAMOS CON LA ULTIMA DIVERGENCIA        
                    DIV_macd_date1 = dfDivergenceUpperMACD.DIVERG_DATE1.iat[-1].strftime('%d-%m-%Y')
                    DIV_macd_date2 = dfDivergenceUpperMACD.DIVERG_DATE2.iat[-1].strftime('%d-%m-%Y') 

            if not dfDivergenceLowerMACD.empty:

                    DIV_macd_type = "LOWER"
                    bDIV_macd = True                   
                    DIV_macd_date1 = dfDivergenceLowerMACD.DIVERG_DATE1.iat[-1].strftime('%d-%m-%Y')   
                    DIV_macd_date2 = dfDivergenceLowerMACD.DIVERG_DATE2.iat[-1].strftime('%d-%m-%Y')   
            # RSI 
            # RSI series 
            dfRSI = pd.DataFrame(dfrsi,columns=['RSI_14'])
        
            peak_levels_rsi,valley_levels_rsi = getIndicatorPeaksValleys(dfRSI,"RSI_14")    
            dfDivergenceUpperRSI = getIndexUpperDivergence(dfOriginalDataTimeFrame,support_levels,valley_levels_rsi)
            dfDivergenceLowerRSI = getIndexLowerDivergence(dfOriginalDataTimeFrame,resistance_levels,peak_levels_rsi)

            if not dfDivergenceUpperRSI.empty:
                bDIV_rsi =  True
                DIV_rsi_type = "UPPER"           
                DIV_rsi_date1 = dfDivergenceUpperRSI.DIVERG_DATE1.iat[-1].strftime('%d-%m-%Y')   
                DIV_rsi_date2 = dfDivergenceUpperRSI.DIVERG_DATE2.iat[-1].strftime('%d-%m-%Y')               
            if not dfDivergenceLowerRSI.empty:
                bDIV_rsi =  True
                DIV_rsi_type = "LOWER"            
                DIV_rsi_date1 = dfDivergenceLowerRSI.DIVERG_DATE1.iat[-1].strftime('%d-%m-%Y')   
                DIV_rsi_date2 = dfDivergenceLowerRSI.DIVERG_DATE2.iat[-1].strftime('%d-%m-%Y')               

            if bDIV_macd or bDIV_rsi:
            # solo si hay divergencias 
            #dfIBTrader =  pd.DataFrame(columns=['SYMBOL','SUPPORT','RESISTANCE','LAST_PRICE', 'SMA','PERIOD','DIV_MAC_TYPE','DIV_RSI_TYPE',
            #'DIV_MACD_DATE1', 'DIV_MACD_DATE2','DIV_RSI_DATE1', 'DIV_RSI_DATE2', 'MACD_VALUE','RSI_VALUE'])

                link = "https://es.tradingview.com/chart?symbol=" # NASDAQ-CTXS/
                link += contract.exchange + "-" + contract.symbol

                dfIBTrader = dfIBTrader.append({'SYMBOL': contract.symbol, 'SUPPORT': last_support_value, 'SUPPORT_DATE': last_support_date,
                    'RESISTANCE' : last_resistance_value, 'RESISTANCE_DATE' : last_resistance_date , 'LAST_PRICE': last_price, 'PRICE_IN_RANGE' : last_price_between_supp_resist,
                    'SMA' : sma,'PERIOD' :period,'DIV_MAC_TYPE' :DIV_macd_type,'DIV_RSI_TYPE' :DIV_rsi_type
                    ,'DIV_MACD_DATE1' :DIV_macd_date1,'DIV_MACD_DATE2' :DIV_macd_date2,
                    'DIV_RSI_DATE1' :DIV_rsi_date1,'DIV_RSI_DATE2' :DIV_rsi_date2,
                    'MACD_VALUE' :macd_value
                    ,'RSI_VALUE' :rsi_value,'LINK' :link}, ignore_index=True)

        dfIBTrader.to_csv(SETTINGS_REALPATH_STOCK_DATA + "/IBTRADER_SIGNALS.csv")    

    # LO SUBIMOS A S3 SI ESTA EN UNA INSTANCIA DE AMAZON Y TIENE LA INSTANCIA EL ROLE ASOCIADO PARA AUTENTICAR CONTRA S3 CON SU IAM ROLE, NADA DE USUARIOS 
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    signals_file = "IBTRADER_SIGNALS.csv"
    print ("Verifying if bucket " + BUCKET_NAME  + " exists")
    if len(response)==0:
        bucket_created = create_bucket(BUCKET_NAME)
        print ("Bucket " + BUCKET_NAME  + " created ")
    with open(SETTINGS_REALPATH_STOCK_DATA + "/" + signals_file, "rb") as f:
            s3.upload_fileobj(f, BUCKET_NAME, signals_file)
            print ("CSV IBTRADER_SIGNALS uploaded successfully ")   

    #url = "https://s3.{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'], BUCKET_NAME, quote_plus("IBTRADER_SIGNALS.csv")
    #print(url)
    location = s3.get_bucket_location(Bucket=BUCKET_NAME)['LocationConstraint']
    url = "https://s3.amazonaws.com/%s/%s" % (BUCKET_NAME, signals_file)
    print (url)
    return 'it works!'

    

