
--- these are cql queries for the dashboard
--- Winners at the moment 
SELECT  symbol,
       price_change_percent,
       volume
FROM cap_stock.top_24hr 
WHERE time_collected >= ${__from}
  AND time_collected <= ${__to}
ALLOW FILTERING;

--- Price change percentage
SELECT price_change_percent
FROM cap_stock.top_24hr
WHERE symbol = '$symbol'
  AND time_collected >= ${__from};

--- Recent Trades snapshot
SELECT 
  symbol,
  MAX(price) as highest_price,
  COUNT(*) as trade_count,
  SUM(qty) as total_volume
FROM cap_stock.recent_trades 
WHERE symbol = '$symbol'
AND trade_time >= ${__from}

--- Klines
SELECT symbol,
  k_open_time AS time,
  open,
  high,
  low,
  close,
  volume
FROM cap_stock.kline_data
WHERE symbol = '$symbol'
  AND k_open_time >= ${__from}
  AND k_open_time <= ${__to}

--- Most recent asks and bids 
--- Query A
SELECT side, price, quantity as quantity_t1
FROM cap_stock.order_book
WHERE symbol = '$symbol'
  AND side = 'bids'
  AND time_collected >= ${__from}
  AND quantity<1000000
LIMIT 100
ALLOW FILTERING;
--- Query B
SELECT side, price, quantity as quantity_t2
FROM cap_stock.order_book
WHERE symbol = '$symbol'
  AND side = 'asks'
  AND time_collected >= ${__from}
  AND quantity<1000000
LIMIT 100
ALLOW FILTERING;

---Most recentVolume Analysis
SELECT symbol, trade_time, SUM(qty) as volume 
FROM cap_stock.recent_trades 
WHERE symbol = '$symbol' 
AND trade_time >= $__timeFrom 
GROUP BY trade_time
ORDER BY trade_time ASC;