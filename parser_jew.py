import collections
import csv
from bs4 import BeautifulSoup
import logging
import os
import sys
import time
import numpy as np
from urllib.request import Request, urlopen, urlretrieve
from urllib.error import HTTPError

# Логи
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('rm')

# Коллекция данных
ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'id_global',
        'metal',
        'stone',
        'price',
        'url',
        'local_url',
    )
)

# заголовки данных в csv
HEADERS = (
    'id_global',
    'metal',
    'stone',
    'price',
    'url',
    'local_url',
)

# helper


class Client:

    id_global_v = 1

    def __init__(self):
        self.result = []

    def get_response(self, url, retries = 3):
        # Данные реквеста(решил заполнить все нужные строки, чтобы не получить очередной бан на сайте)
        req = Request('https://jeweller-karat.ru/')
        req.add_header('Accept', 'image/webp,*/*')
        req.add_header('Accept-Language', 'en-GB,en;q=0.5')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Host', 'jeweller-karat.ru')
        req.add_header('Referer', 'https://jeweller-karat.ru/')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0')
        try:
            req.full_url = url
            responce = urlopen(req)
            return responce
        except HTTPError as err:
            print(err.code)
            if retries:
                pass
        except Exception as err:
            print(err)
            if retries:
                pass

        # from 5 to 30 seconds
        time.sleep((30-5)*np.random.random()+5)
        # try again
        self.save_result_if_dead()
        self.result = []
        # self.build_session()
        return self.get_response(url, retries - 1)

    def load_image(self, imgurl, imgpath):
        try:
            urlretrieve(imgurl, imgpath)
        except HTTPError as err:
            print(err)
            pass
        except Exception as err:
            print(err)
            pass

    # Функа для загрузки страницы
    def load_page(self, page: int=None):
        url = 'https://jeweller-karat.ru/catalog/sergi/?PAGEN_2=' + str(page)
        res = self.get_response(url)
        # res.apparent_encoding = 'utf-8'
        # print(res.text)
        return res.read()

        # Парсим страницу и находим нужные нам блоки
    def parse_page(self, text: str):
        soup = BeautifulSoup(text, 'lxml')
        container = soup.select('div.catalog_item.col.mb-3')
        # logger.info('%s', container) # debug
        for block in container:
            self.parse_block(block=block)

    # Парсим собсна нужные нам классы
    def parse_block(self, block):
        url_block = block.select_one('a.card.h-100.text-center')
        if not url_block:
            logger.error('no url block')
            return
        url = 'https://jeweller-karat.ru' + url_block.get('href')

        # Переход на страницу ювелирки
        page_soup = self.load_page_block(url)
        inpage_soup = BeautifulSoup(page_soup, 'lxml')

        for page_img in range(1, 3):
            id_photo = page_img
            metal = 'Нет металла'
            stone = 'Без камня'
            characteristic_block = inpage_soup.select_one('dl.row')
            if not characteristic_block:
                logger.error('no characteristic block')
                return

            character_list = characteristic_block.contents

            for item in character_list:
                if isinstance(item, str):
                    character_list.remove(item)
                    continue

            for index, item in enumerate(character_list):
                if 'Металл' in item.text:
                    metal = self.clrtext(character_list[index + 1].text)

                if 'Вставка' in item.text:
                    stone = self.clrtext(character_list[index + 1].text)

            price_block = inpage_soup.select_one('span.val')
            price = self.clrtext(price_block.text)

            img_url_block = inpage_soup.select_one('ul.slides')
            img_pool = img_url_block.find_all('img')
            if not img_pool:
                logger.error('no images')
                pass
            else:
                img_url_norm = 'https://jeweller-karat.ru' + img_pool[page_img-1].attrs.get('src')

            somepath = 'data\\' + str(Client.id_global_v)

            if not os.path.exists(somepath):
                os.makedirs(somepath)

            local_url = somepath + '\\' + str(id_photo) + '.jpg'
            logger.info('Скачиваю ' + str(Client.id_global_v) + '_' + str(page_img) + ' жевели')
            self.load_image(img_url_norm, local_url)

            local_url = '\\' + local_url

            # Присваиваем спаршенные значения
            self.result.append(ParseResult(
                id_global=Client.id_global_v,
                metal=metal,
                stone=stone,
                price=price,
                url=url,
                local_url=local_url,
                ))
        Client.id_global_v += 1

    def save_result_if_dead(self):
        path = os.path.dirname(os.path.realpath(sys.argv[0])) + '/jewelry.csv'
        logger.info('Сохраняем...')
        with open(path, 'a', encoding="utf-32", newline='') as outfile:
            writer = csv.writer(outfile)
            for item in self.result:
                writer.writerow(item)

    @staticmethod
    def create_csv():
        path = os.path.dirname(os.path.realpath(sys.argv[0])) + '/jewelry.csv'
        with open(path, 'w', encoding="utf-32", newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(HEADERS)

    @staticmethod
    def clrtext(txt):
        return txt.replace('\n', '').strip()

    def savepoint(self):
        self.save_result_if_dead()
        self.result = []

    def load_page_block(self, url):
        res = self.get_response(url)
        return res.read()

    # logger можно убрать, просто использовал для дебага
    def run(self):
        self.create_csv()
        if not os.path.exists(os.path.dirname(os.path.realpath(sys.argv[0])) + '\\' + 'data'):
            os.makedirs('data')
        for page in range(1, 101):
            text = self.load_page(page)
            self.parse_page(text=text)
            logger.info('%s, Страниц запаршено', page)
            # if page % 10 == 0:
            #   self.savepoint()

        self.save_result_if_dead()

    # logger.debug('%s, test text', text)


if __name__ == '__main__':
    parser = Client()
    parser.run()
