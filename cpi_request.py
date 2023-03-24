import requests

api_key = 'EZ62YSL0CTUD8S3O'

def get_last_12_months_cpi(api_key):
    url = f"https://www.alphavantage.co/query?function=CPI&apikey={api_key}"
    response = requests.get(url)
    response_json = response.json()
    cpi_data = response_json["data"]
    last_12_months_cpi = {}

    for i in range(12):
        month = cpi_data[i]["date"]
        cpi = cpi_data[i]["value"]
        last_12_months_cpi[month] = cpi

    return last_12_months_cpi

print(get_last_12_months_cpi(api_key))






