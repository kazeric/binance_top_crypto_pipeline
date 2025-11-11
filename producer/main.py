# imports 
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import pandas as pd
from sqlalchemy import create_engine
from cassandra_setup import setup_cassandra
# basic config
load_dotenv()

conn = os.getenv("CONN")

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s | %(levelname)s | %(name)s| %(message)s',
  handlers=[
        logging.FileHandler(f"loading_logs_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
  ]  
)

# kline etl
def fetch_klines_24hrs(symbol:str) -> list:
    try:
        logging.info(f'Starting to load klines ...')
        response = requests.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=300")
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logging.info(f"there was a problem loading klines{e}")


def transform_load_klines_data(data:list, symbol:str, ranking:int)-> None:
    # put it into a data frame 
    logging.info('Loading into the data frame')
    df = pd.DataFrame(data, columns=['k_open_time', 'open', 'high', 'low', 'close', 'volume', 'k_close_time', 'quote_asset_volume', 'number_of_trades', 'tb_base_volume', 'tb_quote_volume', 'ignore'])

    
    # add the necessary columns 
    logging.info("Adding the additional columns")
    df["symbol"] = symbol
    df['ranking'] = ranking
    df['time_collected'] = datetime.now()

    # removing uneccesary columns
    logging.info("dropping unncecessary columns")
    df= df.drop('ignore', axis=1)

    # type issues 
    logging.info("changing the numeric columns to numeric datatypes")

    num_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume', 'tb_base_volume', 'tb_quote_volume']

    df[num_cols]= df[num_cols].apply(pd.to_numeric, axis=1)
    
    logging.info("Changing the time column to the time convention ")
    time_cols = ["k_open_time","k_close_time", 'time_collected']


    df[time_cols] = (
        df[time_cols]
        .apply(lambda col: pd.to_datetime(col, unit='ms', utc=True))
        .apply(lambda x: x.dt.to_pydatetime()) 
        )
    
    logging.info("loading the data")


    engine = create_engine(conn)

    df.to_sql("kline_data", engine, if_exists="append", index=False)


# orderbook etl
def fetch_OB(symbol:str) -> list:
    try:
        logging.info(f'Starting to load order book data ...')
        response = requests.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=300")
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logging.info(f"there was a problem loading order book data{e}")


def transform_load_OB_data(data:dict, symbol:str, ranking:int)-> None:
    # put it into a data frame 
    logging.info('Loading into the data frame')
    df_bids = pd.DataFrame(data["bids"], columns = ['price', 'quantity'] )
    df_bids["side"] = 'bids'

    df_asks = pd.DataFrame(data["asks"], columns = ['price', 'quantity'])
    df_asks["side"] = 'asks'
    

    df= pd.concat([df_asks, df_bids], ignore_index=True)
    
    # add the necessary columns 
    logging.info("Adding the additional columns")
    df["symbol"] = symbol
    df['ranking'] = ranking
    df['time_collected'] = datetime.now()
    
    # type issues 
    logging.info("changing the numeric columns to numeric datatypes")

    num_cols = ['price', 'quantity']

    df[num_cols]= df[num_cols].apply(pd.to_numeric, axis=1)
    
    logging.info("loading the data")


    engine = create_engine(conn)

    df.to_sql("order_book", engine, if_exists="append", index=False)

# recent trades etl
def fetch_recent_trades(symbol:str) -> list:
    try:
        logging.info(f'Starting to load order recent trades ...')
        response = requests.get(f"https://api.binance.com/api/v3/trades?symbol={symbol}&limit=300")
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logging.info(f"there was a problem loading recent trades data{e}")



def transform_load_recent_trades(data:dict, symbol:str, ranking:int)-> None:
    # put it into a data frame 
    logging.info('Loading into the data frame')
    df = pd.DataFrame(data)

    # rename the columns to snake case
    df  = df.rename(columns={"quoteQty":"quote_qty", "isBuyerMaker": "is_buyer_maker", "isBestMatch":"is_best_match"})
    
    # add the necessary columns 
    logging.info("Adding the additional columns")
    df["symbol"] = symbol
    df['ranking'] = ranking
    df['time_collected'] = datetime.now()

  

    # type issues 
    logging.info("changing the numeric columns to numeric datatypes")

    num_cols = ['price', 'qty', 'quote_qty']

    df[num_cols]= df[num_cols].apply(pd.to_numeric, axis=1)
    
    logging.info("Changing the time column to the time convention ")
    time_cols = ["time", 'time_collected']


    df[time_cols] = (
        df[time_cols]
        .apply(lambda col: pd.to_datetime(col, unit='ms', utc=True))
        .apply(lambda x: x.dt.to_pydatetime()) 
        )
    
    logging.info("loading the data")

    engine = create_engine(conn)

    df.to_sql("recent_trades", engine, if_exists="append", index=False)


# stats to watch ETL
def fetch_top5_24hr() -> tuple[list, list]:
    try:
        logging.info(f'Starting to load top 5  data ...')
        response = requests.get(f"https://api.binance.com/api/v3/ticker/24hr")
        response.raise_for_status()
        data = response.json()
        # Filter based on the usdt tethered cryptos  
        usdt_pairs = [
            item for item in data
            if item['symbol'].endswith('USDT') and float(item['quoteVolume']) > 1000000 and float(item['askQty']) > 0.0
            ]
        # sort the data
        sorted_data = sorted(
            usdt_pairs,
            key = lambda x: float(x["priceChangePercent"]),
            reverse=True
        )

        top_5 = [x['symbol'] for x in sorted_data[:5]]

        # push this to the other tasks with xcoms 
        return sorted_data[:5] , top_5
    except Exception as e:
        logging.info(f"there was a problem loading top 5 data{e}")

def transform_load_top5_24hr(data:list) -> None:
    # put it into a data frame 
    logging.info('Loading into the data frame')
    df = pd.DataFrame(data)
    
    df = df.rename(columns={'priceChange':'price_change', 'priceChangePercent':'price_change_percent', 'weightedAvgPrice':'weighted_avg_price', 'prevClosePrice':'prev_close_price', 'lastPrice':'last_price', 'lastQty': 'last_qty','bidPrice':'bid_price', 'bidQty':'bid_qty', 'askPrice':'ask_price','askQty':'ask_qty', 'openPrice':'open_price', 'highPrice':'high_price','lowPrice':'low_price', 'quoteVolume':'quote_volume', "openTime":"open_time","closeTime":"close_time", "firstId":"first_id", "lastId":"last_id"})
    # add the necessary columns 
    logging.info("Adding the additional columns")
    df['time_collected'] = datetime.now()


    # type issues 
    logging.info("changing the numeric columns to numeric datatypes")

    num_cols = ['price_change', 'price_change_percent', 'weighted_avg_price', 'prev_close_price', 'last_price', 'last_qty','bid_price', 'bid_qty', 'ask_price','ask_qty', 'open_price', 'high_price','low_price', 'volume', 'quote_volume']

    df[num_cols]= df[num_cols].apply(pd.to_numeric, axis=1)
    
    logging.info("Changing the time column to the time convention ")
    time_cols = ["open_time","close_time",'time_collected']


    df[time_cols] = (
        df[time_cols]
        .apply(lambda col: pd.to_datetime(col, unit='ms', utc=True))
        .apply(lambda x: x.dt.to_pydatetime()) 
        )
    logging.info("loading the data")

    engine = create_engine(conn)

    df.to_sql("top_24hr", engine, if_exists="append", index=False)



if __name__ == "__main__":
    # Simple entry point; extend to run specific ETL tasks as needed
    logging.info("Running cassandra set up ")
    
    setup_cassandra()

    logging.info("Running main etl pipeline ")
    data , top_5 = fetch_top5_24hr()
    transform_load_top5_24hr(data)

    
    for i , item in enumerate(top_5):
        logging.info(f"Starting the klines etl {i+1} for {item}")
        kline_data = fetch_klines_24hrs(item)
        transform_load_klines_data(kline_data, item, i+1)

        logging.info(f"Starting etl for order book {i+1} for {item}")
        OB_data = fetch_OB(item)
        transform_load_OB_data(OB_data, item, i+1)

        logging.info(f"Starting etl for recent trades {i+1} for {item}")
        RT_data = fetch_recent_trades(item)
        transform_load_recent_trades(RT_data, item, i+1)

    
    