import requests
YOUR_API_KEY = 'EZ62YSL0CTUD8S3O'

import requests

# Replace YOUR_API_KEY with your actual API key
url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&outputsize=compact&apikey={YOUR_API_KEY}'

response = requests.get(url)
data = response.json()['Time Series (Daily)']

# Extract the daily closing prices from the data for the last 10 days
closing_prices = []
for date in sorted(data.keys(), reverse=True)[:5]:
    closing_prices.append(float(data[date]['4. close']))

# Calculate the 10-day moving average
period = 5
moving_average = sum(closing_prices) / period

# Print the moving average
print(f'Current 10-day moving average for IBM stock: {moving_average:.2f}')



