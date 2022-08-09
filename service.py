import requests
import logging
import datetime

# OZON init
API_KEY = "dc4a490e-949a-4a11-b5d4-1e8381ab9602"
CLIENT_ID = "402856"

# SIMA LAND init
SIMA_LAND_MIN = 3

# # logging.basicConfig(filename='bot.log')
# logging.info(str(datetime.datetime.now()))


# SIMA_LAND_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NTk3MTg1NDksImlhdCI6MTY1OTExMzc0OSwianRpIjoyNzA3MjQxLCJuYmYiOjE2NTkxMTM3NDl9.g7JlVOzc4QB3Tv5mBoVo8AN0kjygCfrGmRdqhWRiHsM '
#

def get_ozon_items(API_KEY, CLIENT_ID):
    ozon_products_ids = []
    res = requests.post('https://api-seller.ozon.ru/v3/product/info/stocks',
                        headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID},
                        json={
                            "filter": {
                                "visibility": "VISIBLE"
                            },
                            "last_id": "",
                            "limit": 1000
                        })
    for i in res.json().get('result')['items']:
        ozon_products_ids.append(int(i.get('offer_id')))
    return ozon_products_ids


def get_sima_land_items(ozon_products_ids, SIMA_LAND_TOKEN, API_KEY, CLIENT_ID):
    stocks = []
    res = requests.post('https://api-seller.ozon.ru/v1/warehouse/list',
                             headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID})
    warehouse_id = res.json()['result'][0].get('warehouse_id')

    for i in ozon_products_ids:
        if len(stocks) == 50 or len(ozon_products_ids[ozon_products_ids.index(i):]) < 50:
            update_ozon_items(stocks, API_KEY, CLIENT_ID)
            stocks = []
        print(i)
        logging.info(f'Получение товара с артикулом {i}')
        try:
            response = requests.get(
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
                stocks.append({'offer_id': str(response.json()['sid']), 'stock': 0,  "warehouse_id": warehouse_id})
            else:
                stocks.append({'offer_id': str(response.json()['sid']), 'stock': response.json()['balance'],  "warehouse_id": warehouse_id})
        except Exception as e:
            print(e)
    return stocks


def update_ozon_items(stocks, API_KEY, CLIENT_ID):
    # todo это для фбо складов
    # response = requests.post('https://api-seller.ozon.ru/v1/warehouse/list',
    #                          headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID})
    # warehouse_id = response.json()['result'][0].get('warehouse_id')
    if stocks:
        logging.info(f'Загрузка товаров с артикулом {stocks}')
        print(f'Загрузка товара {stocks}')
        # stocks.append({"offer_id": str(i['sid']), "stock": i['stock'], "warehouse_id": warehouse_id})
        # todo сделать запросы через внутреннее апи if len(stocks) % 50 == 0 or len(sima_land) < 50:

        res = requests.post('https://api-seller.ozon.ru/v2/products/stocks',
                            headers={'Api-Key': API_KEY, 'Client-Id': CLIENT_ID},
                            json={
                                "stocks": stocks
                            })
        for item in res.json()['result']:
            if not item['updated']:
                print("Товар не обновлен")
    else:
        return 'Товары не требуют обновления или слишком низкий SIMA_MIN'


def main(API_KEY, CLIENT_ID, SIMA_LAND_TOKEN):
    get_sima_land_items(get_ozon_items(API_KEY, CLIENT_ID), SIMA_LAND_TOKEN, API_KEY, CLIENT_ID)
