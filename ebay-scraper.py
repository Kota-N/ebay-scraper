import requests
from bs4 import BeautifulSoup

import sqlite3
from datetime import date, datetime
import time

from re import sub
from decimal import Decimal
import asyncio


def insert_date():
    db = sqlite3.connect('/var/www/html/ebay_price_tracker/db.sqlite')
    cursor = db.cursor()
    cursor.execute("INSERT INTO dates(date) VALUES('" + str(date.today()) + "')")
    db.commit()
    db.close()

def insert_prices(insert_map):
    db = sqlite3.connect('/var/www/html/ebay_price_tracker/db.sqlite')
    cursor = db.cursor()

    for key, value in insert_map.items():
        cursor.execute("INSERT INTO prices(price, product_id, scraped_date) SELECT '" + value + "' AS price, products.id, dates.date FROM products, dates WHERE products.id=" + str(key) + " AND dates.date='" + str(date.today()) + "'")
    
    db.commit()
    db.close()

def scrape_products():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:84.0) Gecko/20100101 Firefox/84.0'}
    db = sqlite3.connect('/var/www/html/ebay_price_tracker/db.sqlite')
    cursor = db.cursor()

    insert_map = {}

    try:
        for row in cursor.execute('SELECT * FROM products'):
            res = requests.get(row[2], headers=headers)
            soup = BeautifulSoup(res.content, 'html.parser')

            price_list = [x.text for x in soup.find_all('span', {'class': 's-item__price'})]
            lowest_price = Decimal(sub(r'[^\d.]', '', price_list[0]))

             # Take the first three of price_list, and get the lowest price of them.
            for i in list(range(3)):
                lowest_price = min(lowest_price, Decimal(sub(r'[^\d.]', '', price_list[i])))
                
            lowest_price_formatted = '${:,.2f}'.format(lowest_price)
            insert_map[row[0]] = lowest_price_formatted

    except requests.ConnectionError:
        db.close()
        print('connection error: ' + str(datetime.now()))
        return True
    except requests.exceptions.MissingSchema as err:
        print(err)
        pass
    
       
    
    db.close()
    # print('insert_map: ' + insert_map)
    insert_prices(insert_map)

    return False


def ebay_scraper():
    while True:
        hour = 60 * 60
        scrape_interval = 60

        insert_date()
        connection_error = scrape_products()
        error_time_offest = 0

        while connection_error:
            delay_time = hour * 2
            error_time_offest += delay_time
            time.sleep(delay_time)

            connection_error = scrape_products()
                    

        print('Scraped: ' + str(datetime.now()))

        if scrape_interval - error_time_offest > 0:
            time.sleep(scrape_interval - error_time_offest)

ebay_scraper()

