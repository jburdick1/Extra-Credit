def open_trade(session, ticker):
    # Inital trade execution function

    open_orders = get_orders(session)
    market_data = get_market_data(session, ticker)

    print(f"market_data: {market_data}")
    print(f"MIN_SPREAD: {MIN_SPREAD}")

    # If we have open trades we should be using the reorder function
    if open_orders['order_data']['gross_orders'] == 0:

        # Make sure bid-ask width is greater than our threshold
        if (market_data['best_ask'] - market_data['best_bid']) > MIN_SPREAD:

            print(f"rsi_values: {market_data['rsi_values']}")
            print(f"macd_values: {market_data['macd']}")

            # Check if there is a trend and determine the offset based on it
            rsi_values = get_rsi(session, ticker, [14])
            macd_values = get_macd(session, ticker, [12, 26, 9])

            rsi = rsi_values['RSI_14']
            macd = macd_values['MACD']
            signal = macd_values['signal']
            offset = 0

            if rsi < 20:
                offset = -0.02
            elif 20 <= rsi < 27:
                offset = -0.01
            elif 27 <= rsi < 45:
                offset = 0
            elif 45 <= rsi < 60:
                offset = 0.01
            elif rsi >= 60:
                offset = 0.02

            if macd > signal:
                # Trend is up, adjust offset
                offset += 0.01
            elif macd < signal:
                # Trend is down, adjust offset
                offset -= 0.01

            # Calculate maximum orders to submit
            trade_count = int(MAX_VOLUME / MAX_SIZE)

            # Submit orders with adjusted prices
            for i in range(trade_count):
                if rsi < 27:
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_bid'] + offset, 'quantity': MAX_SIZE, 'action':'BUY'})
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_ask'] , 'quantity': MAX_SIZE, 'action':'SELL'})
                    time.sleep(0.5)
                else:
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_bid'] , 'quantity': MAX_SIZE, 'action':'BUY'})
                    session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 'type': 'LIMIT', 'price': market_data['best_ask'] + offset, 'quantity': MAX_SIZE, 'action':'SELL'})
                    time.sleep(0.5)
