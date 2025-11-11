from cassandra.cluster import Cluster
from dotenv import load_dotenv
import logging
from datetime import datetime

def setup_cassandra() -> None:

    logging.basicConfig(
        level=logging.INFO,
        format= '%(asctime)s|%(levelname)s|%(name)s|%(message)s',
        handlers = [
            logging.FileHandler(f"cassandra_setup{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )

    load_dotenv()

    logging.info('Creating the connection ...')
    # connecting to cassandra 
    cluster = Cluster(['cassandra'])
    session = cluster.connect()

    logging.info('Connected ...')
    logging.info('Creating the keyspace cap_stock ...')
    # create the key space 
    create_keyspace_query = """
    CREATE KEYSPACE IF NOT EXISTS cap_stock WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor' : 1 };
    """
    session.execute(create_keyspace_query)

    use_keyspace_query= """
    USE cap_stock;
    """
    session.execute(use_keyspace_query)

    logging.info('using the created keyspace ...')

    logging.info('Creating the tables')

    create_kline_query = """
    CREATE TABLE IF NOT EXISTS cap_stock.kline_data (
    symbol              text,
    k_open_time         timestamp,
    k_close_time        timestamp,
    open                double,
    high                double,
    low                 double,
    close               double,
    volume              double,
    quote_asset_volume  double,
    number_of_trades    int,
    tb_base_volume      double,
    tb_quote_volume     double,
    ranking             int,
    time_collected      timestamp,
    PRIMARY KEY ((symbol), k_open_time)
    ) WITH CLUSTERING ORDER BY (k_open_time DESC)
    AND compaction = {
        'class': 'TimeWindowCompactionStrategy',
        'compaction_window_unit': 'DAYS',
        'compaction_window_size': '1'
    };
    
    """
    create_OB_query =   """
    CREATE TABLE IF NOT EXISTS cap_stock.order_book (
    symbol          text,
    side            text,       -- 'bids' or 'asks'
    ranking         int,        -- rank of the crypto in top performers
    price           double,
    quantity        double,
    time_collected  timestamp,  -- when this snapshot was taken
    PRIMARY KEY ((symbol, side, time_collected), price)
    ) WITH CLUSTERING ORDER BY (price DESC);

    """

    create_recent_trades_query = """
    CREATE TABLE IF NOT EXISTS cap_stock.recent_trades(
    symbol          text,
    trade_time      timestamp,  
    trade_id        bigint,      
    price           double,
    qty             double,
    quote_qty       double,
    is_buyer_maker  boolean,
    is_best_match   boolean,
    ranking         int,
    time_collected  timestamp,  
    PRIMARY KEY ((symbol), trade_time, trade_id)
    ) WITH CLUSTERING ORDER BY (trade_time DESC, trade_id DESC)
    AND compaction = {
        'class': 'TimeWindowCompactionStrategy',
        'compaction_window_unit': 'HOURS',
        'compaction_window_size': '1'
    };
    """

    create_top_24hrs = """
    CREATE TABLE IF NOT EXISTS cap_stock.top_24hr (
    symbol                 text,
    time_collected         timestamp,    

    price_change           double,
    price_change_percent   double,
    weighted_avg_price     double,
    prev_close_price       double,
    last_price             double,
    last_qty               double,
    bid_price              double,
    bid_qty                double,
    ask_price              double,
    ask_qty                double,
    open_price             double,
    high_price             double,
    low_price              double,
    volume                 double,
    quote_volume           double,

    open_time              timestamp,    
    close_time             timestamp,    
    first_id               bigint,
    last_id                bigint,

    PRIMARY KEY ((symbol), time_collected)
    ) WITH CLUSTERING ORDER BY (time_collected DESC)
    AND compaction = {
        'class': 'TimeWindowCompactionStrategy',
        'compaction_window_unit': 'HOURS',
        'compaction_window_size': '1'
    };
    """
    session.execute(create_top_24hrs)
    session.execute(create_recent_trades_query)
    session.execute(create_OB_query)
    session.execute(create_kline_query)

    