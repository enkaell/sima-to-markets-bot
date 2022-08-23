import requests
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass, field
import datetime

# OZON init
API_KEY = str()
CLIENT_ID = str()

# SIMA LAND init
SIMA_LAND_MIN = 3


# # logging.basicConfig(filename='bot.log')
# logging.info(str(datetime.datetime.now()))


# SIMA_LAND_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NTk3MTg1NDksImlhdCI6MTY1OTExMzc0OSwianRpIjoyNzA3MjQxLCJuYmYiOjE2NTkxMTM3NDl9.g7JlVOzc4QB3Tv5mBoVo8AN0kjygCfrGmRdqhWRiHsM '
#
@dataclass
class Result:
    items_selling: int = 0
    items_waiting: int = 0


def main(SIMA_LAND_TOKEN, API_KEY, CLIENT_ID):
    ozon_products_ids, last_id = get_ozon_items(API_KEY, CLIENT_ID)
    while len(ozon_products_ids) > 1:
        get_sima_land_items(ozon_products_ids, SIMA_LAND_TOKEN, API_KEY, CLIENT_ID)
        ozon_products_ids, last_id = get_ozon_items(API_KEY, CLIENT_ID, last_id)
    print(
        f"Ended in {datetime.datetime.now()},в продаже: {Result.items_selling}, которых нет на Сима-Ленде: {Result.items_waiting}")


def get_ozon_items(API_KEY, CLIENT_ID, last_id=''):
    ozon_products_ids = []
    res = requests.post('https://api-seller.ozon.ru/v3/product/info/stocks',
                        headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID},
                        json={
                            "filter": {
                                "visibility": "VISIBLE"
                            },
                            "last_id": f"{last_id}",
                            "limit": 1000
                        })
    for i in res.json().get('result')['items']:
        try:
            ozon_products_ids.append(int(i.get('offer_id')))
        except ValueError as e:
            print(i, ' ', e)
            pass
    last_id = res.json().get('result')['last_id']
    return ozon_products_ids, last_id


def get_sima_land_items(ozon_products_ids, SIMA_LAND_TOKEN, API_KEY, CLIENT_ID):
    stocks = []
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    res = requests.post('https://api-seller.ozon.ru/v1/warehouse/list',
                        headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID})
    warehouse_id = res.json()['result'][0].get('warehouse_id')

    for i in ozon_products_ids:
        if len(stocks) == 50:
            update_ozon_items(stocks, API_KEY, CLIENT_ID)
            stocks = []
        try:
            response = session.get(
                f'https://www.sima-land.ru/api/v5/item/{i}?view=brief&by_sid=true',
                headers={
                    'accept': 'application/json',
                    'X-Api-Key': SIMA_LAND_TOKEN,
                    'Authorization': SIMA_LAND_TOKEN,
                },

                params={
                    'view': 'brief',
                    'by_sid': 'true',
                }
            )
            if int(response.json()['balance']) < SIMA_LAND_MIN:
                stocks.append({'offer_id': str(response.json()['sid']), 'stock': 0, "warehouse_id": warehouse_id})
                Result.items_waiting += 1
            else:
                stocks.append({'offer_id': str(response.json()['sid']), 'stock': response.json()['balance'],
                               "warehouse_id": warehouse_id})
        except Exception as e:
            print(i, response.json().get('message'))
    return stocks


def update_ozon_items(stocks, API_KEY, CLIENT_ID):
    # todo это для фбо складов
    # response = requests.post('https://api-seller.ozon.ru/v1/warehouse/list',
    #                          headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID})
    # warehouse_id = response.json()['result'][0].get('warehouse_id')
    session = requests.Session()
    retry = Retry(connect=2, backoff_factor=10)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    if stocks:
        logging.info(f'Загрузка товаров с артикулом {stocks}')
        # stocks.append({"offer_id": str(i['sid']), "stock": i['stock'], "warehouse_id": warehouse_id})
        # todo сделать запросы через внутреннее апи if len(stocks) % 50 == 0 or len(sima_land) < 50:

        res = session.post('https://api-seller.ozon.ru/v2/products/stocks',
                           headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID},
                           json={
                               "stocks": stocks
                           })
        try:
            res.json()['result']
        except Exception as e:
            print(e, time.time())
        for item in res.json()['result']:
            if not item['updated']:
                time.sleep(10)
                print(f"Товар {item['offer_id']} не обновлен")
            else:
                Result.items_selling += 1
    else:
        return 'Товары не требуют обновления или слишком низкий SIMA_MIN'
