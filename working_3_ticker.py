import requests
import pandas as pd
import time
import numpy as np

global API_KEY
API_KEY = {'X-API-Key': "69LC227X"}


#Trading Parameters
global ORDER_THRESHOLD
ORDER_THRESHOLD = 75000

global MIN_SPREAD
MIN_SPREAD = 0.00

number_of_tickers_in_sim = 3

global MAX_VOLUME
MAX_VOLUME = 20000

global MAX_SIZE
MAX_SIZE = 1500

# global LOWER_BOUND
# LOWER_BOUND = 2000


def get_tick(session):
    #Return tick of current simulaion
    resp = session.get('http://localhost:9999/v1/case')
    data = resp.json()

    if resp.ok:
        data = resp.json()

        return data['tick'], data['status']

    else:
        return -1



def get_orderbook(session, ticker):
    #Return DataFrame of cleaned order book

    info = {"ticker": ticker, "limit": 100000}
    resp = session.get('http://localhost:9999/v1/securities/book', params = info)
    book = resp.json()
   
    clean_bid, clean_ask = sanitize_orderbook(pd.DataFrame(book['bids']), pd.DataFrame(book['asks'])) #Remove all spoofed and suffed orders
    return clean_bid, clean_ask


def get_moving_averages(session, ticker, periods):
    moving_averages = {}
    
    for period in periods:
        url = f'http://localhost:9999/v1/securities/history?ticker={ticker}&limit={period}'
        resp = session.get(url)
        
        if resp.ok:
            historical_data = resp.json()
            closing_prices = [data['close'] for data in historical_data]
            
            # Calculate the moving average
            moving_average = sum(closing_prices) / period
            moving_averages[f'{period}_day_avg'] = moving_average
    
    return moving_averages
    


def get_macd(session, ticker, periods):
    # Define the number of days for the MACD calculation
    ema_short = 12
    ema_long = 26
    signal_period = 9
    
    url = f'http://localhost:9999/v1/securities/history?ticker={ticker}&limit={ema_long+signal_period-1}'
    resp = session.get(url)

    if not resp.ok:
        raise ValueError(f'Failed to retrieve historical data for {ticker}.')

    # Parse the response JSON and create a DataFrame
    data = resp.json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate the short-term EMA and long-term EMA
    ema_short_values = df['close'].ewm(span=ema_short, adjust=False).mean()
    ema_long_values = df['close'].ewm(span=ema_long, adjust=False).mean()

    # Calculate the MACD line and signal line
    macd_line = ema_short_values - ema_long_values
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Create a dictionary to store the MACD and signal line values
    macd_dict = {
        'MACD': macd_line.values[-1],
        'signal': signal_line.values[-1],
    }

    return macd_dict




def get_rsi(session, ticker, periods):
    # Define the number of periods for the RSI calculation
    rsi_period = 14
    
    url = f'http://localhost:9999/v1/securities/history?ticker={ticker}&limit={rsi_period+periods[-1]-1}'
    resp = session.get(url)

    if not resp.ok:
        raise ValueError(f'Failed to retrieve historical data for {ticker}.')

    # Parse the response JSON and create a DataFrame
    data = resp.json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate the price changes
    deltas = np.diff(df['close'])

    # Calculate the seed values for average gain and average loss
    seed_up = deltas[:rsi_period+1]
    seed_down = -deltas[:rsi_period+1]
    up = seed_up[seed_up >= 0].sum() / rsi_period
    down = seed_down[seed_down >= 0].sum() / rsi_period

    # Calculate the relative strength and RSI values
    rs = up / down
    rsi_values = np.zeros_like(df['close'])
    rsi_values[:rsi_period] = 100. - 100. / (1. + rs)

    for i in range(rsi_period, len(df)):
        delta = deltas[i-1]

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(rsi_period-1) + upval) / rsi_period
        down = (down*(rsi_period-1) + downval) / rsi_period
        rs = up / down
        rsi_values[i] = 100. - 100. / (1. + rs)

    # Create a dictionary to store the RSI values
    rsi_dict = {}
    for period in periods:
        rsi_dict[f'RSI_{period}'] = rsi_values[-period]

    # Return the RSI values
    return rsi_dict


def sanitize_orderbook(bid, ask):
    #Cleans order book to remove manipultive orders
    for row in bid.iterrows():
        id_ = row[0]
        order = row[1]
       
        #Drop potential market mainpulating orders
        if order['quantity'] > ORDER_THRESHOLD:
            bid.drop(id_, inplace=True)
       

    for row in ask.iterrows():
        id_ = row[0]
        order = row[1]
       
        if order['quantity'] > ORDER_THRESHOLD:
            ask.drop(id_, inplace=True)
           
       
    return bid, ask





def get_market_data(session, ticker, trend_direction=None):
    # Package all relevant market data into an object for quick access
    bid_book, ask_book = get_orderbook(session, ticker)
    
    # Get best bid and ask prices
    best_bid = bid_book['price'][0]
    best_ask = ask_book['price'][0]

    # Get moving averages and MACD
    periods = [7, 14, 21]
    moving_averages = get_moving_averages(session, ticker, periods)
    macd = get_macd(session, ticker, periods)

    # Get RSI for different periods
    rsi_periods = [14, 21]
    rsi_values = get_rsi(session, ticker, rsi_periods)

    # Calculate the order price based on trend direction
    order_price = None
    if trend_direction == 'up':
        order_price = best_ask + 0.01
    elif trend_direction == 'down':
        order_price = best_bid - 0.01
    
    data = {
        'bid_book': bid_book, 
        'ask_book': ask_book, 
        'best_bid': best_bid, 
        'best_ask': best_ask,
        'moving_averages': moving_averages,
        'macd': macd,
        'rsi_values': rsi_values,
        'order_price': order_price
    }

    return data



def get_orders(session):
    # Define the tickers you will be trading
    tickers = ["AC", "RY", "CNR"]

    # Initialize the open_orders dictionary with the tickers and required structure
    open_orders = {
        ticker: {"BUY": [], "SELL": [], "order_data": {}}
        for ticker in tickers
    }

    # Return all open orders and data for user
    resp = session.get('http://localhost:9999/v1/orders?status=OPEN')
    orders = resp.json()

    # Process each order and update the dictionary
    for order in orders:
        ticker = order["ticker"]
        if ticker in tickers:
            if order["action"] == "BUY":
                open_orders[ticker]["BUY"].append(order["order_id"])
                open_orders[ticker]["order_data"][order["order_id"]] = {
                    "price": order["price"],
                    "quantity": order["quantity"],
                    "trader_id": order["trader_id"]
                }
            elif order["action"] == "SELL":
                open_orders[ticker]["SELL"].append(order["order_id"])
                open_orders[ticker]["order_data"][order["order_id"]] = {
                    "price": order["price"],
                    "quantity": order["quantity"],
                    "trader_id": order["trader_id"]
                }

    # Calculate and store total buy and sell orders for each ticker
    for ticker in tickers:
        buy_orders = len(open_orders[ticker]["BUY"])
        sell_orders = len(open_orders[ticker]["SELL"])
        open_orders[ticker]["order_data"]["total_buy_orders"] = buy_orders
        open_orders[ticker]["order_data"]["total_sell_orders"] = sell_orders
        open_orders[ticker]["order_data"]["net_orders"] = buy_orders - sell_orders
        open_orders[ticker]["order_data"]["gross_orders"] = buy_orders + sell_orders

    return open_orders

def get_position(session, ticker):
    resp = session.get('http://localhost:9999/v1/securities')
    securitieslist = resp.json()
    for x in securitieslist:
        if x['ticker'] == ticker:
            position = x['position']
    return position

def open_trade(session, ticker):
    # Initial trade execution function

    open_orders = get_orders(session)
    market_data = get_market_data(session, ticker)
    ticker_volume_alotment = {"CNR": 8000, "RY":10000, "AC": 5000}
    ticker_order_sizes = {"CNR": 1600, "RY":2000, "AC": 1000}

    position = get_position(session,ticker)
    

    # If we have open trades we should be using the reorder function
    if open_orders[ticker]['order_data']['gross_orders'] == 0:

        # Make sure bid-ask width is greater than our threshold
        if (market_data['best_ask'] - market_data['best_bid']) > MIN_SPREAD:

            

            # Check if there is a trend and determine the offset based on it
            rsi_values = get_rsi(session, ticker, [14])
            macd_values = get_macd(session, ticker, [12, 26, 9])

            rsi = rsi_values['RSI_14']
            macd = macd_values['MACD']
            signal = macd_values['signal']
            offset = 0

            # Adjust offset based on RSI and MACD signals
            if rsi < 20:
                offset = -0.01
            elif 20 <= rsi < 27:
                offset = 0
            elif 27 <= rsi < 55:
                offset = 0
            elif 55 <= rsi < 70:
                offset = 0.0
            elif rsi >= 70:
                offset = 0.01

            if macd > signal and rsi > 27:
                # Trend is up, adjust offset
                offset += 0.0
            elif macd < signal and rsi < 20:
                # Trend is down, adjust offset
                offset -= 0.01


            quantity = ticker_order_sizes[ticker]
            ticker_max_volume = ticker_volume_alotment[ticker]

            trade_count = int((ticker_max_volume - position)// quantity)
            

            # Submit orders with adjusted prices based on RSI and MACD signals
            for i in range(trade_count):
                if rsi < 27:
                    # Market is trending up, adjust buy order price and keep sell order price unchanged
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_bid'] + offset, 'quantity': quantity, 'action':'BUY'})
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_ask'], 'quantity': quantity, 'action':'SELL'})
                    time.sleep(0.5)
                else:
                    # Market is not trending up, keep buy order price unchanged and adjust sell order price
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_bid'], 'quantity': quantity, 'action':'BUY'})
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_ask'] + offset, 'quantity': quantity, 'action':'SELL'})
                    time.sleep(0.5)


def re_order(session, ticker):
    # Clears outstanding orders and resubmits them at the top of the book

    open_orders = get_orders(session)

    # Checks if one side has been filled
    if (len(open_orders[ticker]["BUY"]) == 0) and (len(open_orders[ticker]["SELL"]) != 0):

        # Loop through open sell orders
        for order_id in open_orders[ticker]["SELL"]:
            order = open_orders[ticker]["order_data"][order_id]

            # Deletes outstanding order and resubmits with the same volume
            res = session.delete("http://localhost:9999/v1/orders/{}".format(order_id))
            if res.ok:
                market_data = get_market_data(session, ticker)
                session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_ask'], 'quantity': order["quantity"], 'action': 'SELL'})

    # Exact same comments as above
    if (len(open_orders[ticker]["SELL"]) == 0) and (len(open_orders[ticker]["BUY"]) != 0):
        # Loop through open buy orders
        for order_id in open_orders[ticker]["BUY"]:
            order = open_orders[ticker]["order_data"][order_id]

            res = session.delete("http://localhost:9999/v1/orders/{}".format(order_id))
            if res.ok:
                market_data = get_market_data(session, ticker)
                session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_bid'], 'quantity': order["quantity"], 'action': 'BUY'})




def cancel_old(session):
    open_orders = get_orders(session)
    if get_tick(session) - open_orders["tick"] > 15:
        for order in open_orders["BUY"] + open_orders["SELL"]:
            id_ = order["order_id"]
            res = session.delete(
                "http://localhost:9999/v1/orders/{}".format(id_))


def megatrade(session):
    open_trade(session, ticker="AC")
    open_trade(session, ticker="CNR")
    open_trade(session, ticker="RY")
    

def mega_reorder(session):
    re_order(session,ticker="AC")
    re_order(session,ticker="CNR")
    re_order(session,ticker="RY")

def main():
    print("Running main() function")

    with requests.Session() as s:
        s.headers.update(API_KEY)

        tickers = ["AC", "RY", "CNR"]

        while True:
            if get_tick(s)[0] > 2 and get_tick(s)[0] < 296:

            
                # Prevents random errors from affecting algos functionality
                try:
                    megatrade(s)
                    time.sleep(2.5)
                    mega_reorder(s)
                    continue

                except:
                    continue

            # Puts algo to sleep between simulations
            if get_tick(s)[1] == "STOPPED":
                while get_tick(s)[1] == "STOPPED":
                    time.sleep(0.05)



main()