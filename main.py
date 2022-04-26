import aiohttp
from fake_useragent import UserAgent
from datetime import datetime
import csv
import asyncio
import json
import os

HEADERS = {'user-agent': UserAgent().random}
URL = 'https://www.ozon.ru/api/composer-api.bx/widget/json/v2'


# Download the image
async def save_photo(session, url, item_id, review_id, enum_image):
    if os.path.exists(f'images/{item_id}') is False:
        os.mkdir(f'images/{item_id}')
    if os.path.exists(f'images/{item_id}/{review_id}') is False:
        os.mkdir(f'images/{item_id}/{review_id}')
    async with session.get(url) as resp:
        if resp.status == 200:
            with open(f'images/{item_id}/{review_id}/{enum_image}.png', "wb") as f:
                f.write(await resp.read())
            return f'images/{item_id}/{review_id}/{enum_image}.png'


class Parsing:
    def __init__(self):
        self.timeout, self.save_images, self.async_data, self.proxie = None, None, None, None
        self.result = []

    # Load settings from config .json
    def load_config(self):
        with open("config.json", encoding='utf=8') as cfg:
            cfg_json = json.load(cfg)
            proxie = cfg_json['settings']['proxie']['http']
            if 'login:pass@ip:port' in proxie:
                self.proxie = None
                print('\nYou are not using a proxy. Requests are made from your IP.\n')
            else:
                self.proxie = proxie
            self.async_data = cfg_json['settings']['async_data']
            self.timeout = cfg_json['settings']['timeout']
            self.save_images = cfg_json['settings']['save_images']

    # Save result to CSV table
    def save_csv(self):
        now = datetime.now()
        name_of_file = f'result_{now.hour}.{now.minute}_{now.day}{now.month}{now.year}'
        with open(f'csv_result/{name_of_file}.csv', 'w',
                  newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(
                ['Item ID', 'Review ID', 'Date', 'Author', 'Score', 'Comment', 'Positive', 'Negative', 'Img'])
            for item in sorted(self.result):
                writer.writerow(item)
        print('\nParsing was completed and saved as ' + name_of_file + '.csv')

    # Main parsing
    async def pars_info(self, session, url):
        num_page = 1  # counter of reviews pages
        finish_all_pages = True
        while finish_all_pages:  # when while is False, then all reviews from the pages have been completed
            await asyncio.sleep(self.timeout)  # timeout post-method
            async with session.post(URL, proxy=self.proxie, headers=HEADERS, data=json.dumps(
                    {'asyncData': self.async_data,
                     'url': url.split('https://www.ozon.ru')[-1].split('?')[0] + '?page=' + str(num_page)})) as resp:
                wait_res = await resp.json()
                if wait_res['state']['reviews'] is not None:
                    item_id = wait_res['state']['itemId']
                    for review in wait_res['state']['reviews']:
                        review_id = review['id']
                        photos = []
                        if self.save_images == 1:  # setting from config
                            for en, photo in enumerate(review['content']['photos']):
                                photos.append(await save_photo(session, photo['url'], item_id, review_id, en))
                        photo_table = '' if len(photos) == 0 else ';'.join(photos)
                        # convert time from unix
                        time_table = datetime.utcfromtimestamp(review['createdAt']).strftime('%Y-%m-%d %H:%M:%S')
                        values = [item_id, review_id, time_table,
                                  review['author']['firstName'],
                                  review['content']['score'],
                                  review['content']['comment'],
                                  review['content']['positive'],
                                  review['content']['negative'], photo_table]
                        self.result.append(values)
                    now = datetime.now()
                    get_item_name = wait_res["state"]["products"][str(item_id)]["name"]
                    print(
                        f'[{now.hour}:{now.minute}:{now.second}] - {get_item_name} '
                        f'reviews on page {num_page} have been parsed.')
                    num_page += 1
                else:
                    # exit from while
                    finish_all_pages = False

    # Collecting all tasks
    async def get_data(self):
        with open('links.txt') as file:
            links = [row.strip() for row in file.readlines()]
            async with aiohttp.ClientSession() as session:
                tasks = [self.pars_info(session, url) for url in links]
                await asyncio.gather(*tasks)


if __name__ == '__main__':
    app = Parsing()
    app.load_config()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.get_data())
    app.save_csv()
