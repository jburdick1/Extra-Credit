import signal
import requests
from time import sleep

Profit_threshold= 5 # ($ per 1000 shares)

optimal_order_size = 5000

API_KEY = {'X-API-Key': 'YOUR_API_KEY_HERE'}
shutdown = False
total_speedbumps = 0
number_of_orders = 0



class ApiException(Exception):
    pass

def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True

def get_tick(session):
    resp = session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick']
    raise ApiException('The API key provided in this Python code must match that in the RIT client (please refer to the API hyperlink in the client toolbar and/or the RIT – User Guide – REST API Documentation.pdf)')

def ticker_bid_ask(session, ticker):
    payload = {'ticker': ticker}
    resp = session.get('http://localhost:9999/v1/securities/book', params=payload)
    if resp.ok:
        book = resp.json()
        return book['bids'][0]['price'], book['asks'][0]['price']
    raise ApiException('The API key provided in this Python code must match that in the RIT client (please refer to the API hyperlink in the client toolbar and/or the RIT – User Guide – REST API Documentation.pdf)')


def ticker_volume(session, ticker):
    payload = {'ticker': ticker}
    resp = session.get('http://localhost:9999/v1/securities/book', params=payload)
    if resp.ok:
        book = resp.json()
        return book['bids'][0]['quantity'], book['bids'][0]['quantity_filled'], book['asks'][0]['quantity'], book['asks'][0]['quantity_filled']
    raise ApiException('The API key provided in this Python code must match that in the RIT client (please refer to the API hyperlink in the client toolbar and/or the RIT – User Guide – REST API Documentation.pdf)')


def volume_decision():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)
        min_volume = 0
        while 1 < tick < 298 and not shutdown:
            crzy_m_bid, crzy_m_ask = ticker_bid_ask(s, 'CRZY_M')
            crzy_a_bid, crzy_a_ask = ticker_bid_ask(s, 'CRZY_A')
            crzy_m_bid_volume, crzy_m_bid_filled, crzy_m_ask_volume, crzy_m_ask_filled = ticker_volume(s, 'CRZY_M')
            crzy_a_bid_volume, crzy_a_bid_filled, crzy_a_ask_volume, crzy_a_ask_filled = ticker_volume(s, 'CRZY_A')

            if crzy_m_bid > crzy_a_ask:
                net_profit = ((crzy_m_bid - crzy_a_ask) * optimal_order_size) - (Profit_threshold * (optimal_order_size / 1000))
                if net_profit > 0:
                    min_volume = min((crzy_m_bid_volume-crzy_m_bid_filled),(crzy_a_ask_volume-crzy_a_ask_filled ))

            elif crzy_a_bid > crzy_m_ask:
                net_profit = ((crzy_a_bid - crzy_m_ask) * optimal_order_size) - (Profit_threshold * (optimal_order_size / 1000))
                if net_profit > 0:
                    min_volume = min((crzy_a_bid_volume-crzy_a_bid_filled),(crzy_m_ask_volume-crzy_m_ask_filled ))
            
            tick = get_tick(s)
        
        return min_volume

volume = volume_decision()
order_limit = volume / optimal_order_size

def speedbump(transaction_time):
    global total_speedbumps
    global number_of_orders
    order_speedbump = - transaction_time + 1/order_limit
    total_speedbumps = total_speedbumps + order_speedbump
    number_of_orders = number_of_orders + 1
    sleep(total_speedbumps/number_of_orders)



def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)
        while tick > 1 and tick < 298 and not shutdown:
            crzy_m_bid, crzy_m_ask = ticker_bid_ask(s, 'CRZY_M')
            crzy_a_bid, crzy_a_ask = ticker_bid_ask(s, 'CRZY_A')

            if crzy_m_bid > crzy_a_ask:
                net_profit =  ((crzy_m_bid-crzy_a_ask)*optimal_order_size)-(Profit_threshold*(optimal_order_size/1000))
                if net_profit > 0:
                    s.post('http://localhost:9999/v1/orders', params={'ticker': 'CRZY_A', 'type': 'MARKET', 'quantity': optimal_order_size, 'action': 'BUY'})
                    s.post('http://localhost:9999/v1/orders', params={'ticker': 'CRZY_M', 'type': 'MARKET', 'quantity': optimal_order_size, 'action': 'SELL'})
                    speedbump(0.01) # simulate a transaction time of 0.01 seconds
            if crzy_a_bid > crzy_m_ask:
                net_profit =  ((crzy_a_bid-crzy_m_ask)*optimal_order_size)-(Profit_threshold*(optimal_order_size/1000))
                if net_profit > 0:
                    s.post('http://localhost:9999/v1/orders', params={'ticker': 'CRZY_M', 'type': 'MARKET', 'quantity': optimal_order_size, 'action': 'BUY'})
                    s.post('http://localhost:9999/v1/orders', params={'ticker': 'CRZY_A', 'type': 'MARKET', 'quantity': optimal_order_size, 'action': 'SELL'})
                speedbump(0.01) # simulate a transaction time of 0.01 seconds

            tick = get_tick(s)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
