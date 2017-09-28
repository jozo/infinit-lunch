import json
import os
import re
import abc
from datetime import datetime

import requests
from bs4 import BeautifulSoup

FB_APP_ID = os.environ.get('FB_APP_ID', None)
FB_APP_SECRET = os.environ.get('FB_APP_SECRET', None)
NO_PRICE = object()
TODAY = datetime.today().weekday()
DAY_NAMES = [
    'pondelok',
    'utorok',
    'streda',
    'štvrtok',
    'piatok',
    'sobota',
    'nedeľa',
]


class Menu:
    def __init__(self, rest_name: str) -> None:
        self.restaurant_name = rest_name
        self.foods = []
        self.prices = []

    def add_item(self, food: str, price=NO_PRICE):
        self.foods.append(food.strip())
        self.prices.append(price)

    def __str__(self):
        items = ['*{}*'.format(self.restaurant_name)]
        items += ['{}. {}{}'.format(i, food, self.format_price(price))
                  for i, (food, price) in enumerate(zip(self.foods, self.prices), start=1)]
        return '\n'.join(items)

    def format_price(self, price):
        return ' ({}€)'.format(price) if price is not NO_PRICE else ''


class FormattedMenus:
    def __init__(self, menus: list, today=datetime.today()) -> None:
        self.menus = menus
        self.today = today
        self.formatted = None

    def __len__(self) -> int:
        return len(self.menus)

    def __getitem__(self, key):
        if not self.formatted:
            self.format_menus()
        return self.formatted[key]

    def __str__(self):
        if not self.formatted:
            self.format_menus()
        return '\n\n'.join(self.formatted)

    def format_menus(self):
        self.formatted = [self.add_header(self.menus[0])]
        self.formatted += [str(m) for m in self.menus[1:]]

    def add_header(self, menu):
        return "*Obedy v {} {}*\n\n{}".format(DAY_NAMES[self.today.weekday()],
                                              self.today.strftime('%d.%m.%Y'),
                                              menu)


class Restaurant(abc.ABC):
    """
    Provide menu items for a day in specific restaurant
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = 'Restaurant'

    def __repr__(self) -> str:
        return 'Restaurant ({})'.format(self.name)

    @abc.abstractmethod
    def retrieve_menu(self, day=TODAY) -> Menu:
        pass


class SafeRestaurant(Restaurant):
    """
    Catch all exceptions so the application will not broke
    """

    def __init__(self, restaurant) -> None:
        super().__init__()
        self.restaurant = restaurant

    def retrieve_menu(self, day=TODAY) -> Menu:
        try:
            return self.restaurant.retrieve_menu()
        except Exception:
            from infinit_lunch import sentry
            sentry.captureException()

            menu = Menu(self.restaurant.name)
            menu.add_item('Problem with scraping. Check menu yourself on {}'.format(self.restaurant.url))
            return menu


class BednarRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Bednar (3.9€)'
        self.url = 'http://bednarrestaurant.sk/new/wordpress/?page_id=62'

    def retrieve_menu(self, day=TODAY) -> Menu:
        r = requests.get(self.url)
        self.content = BeautifulSoup(r.content, 'html.parser')
        return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        try:
            groups = re.search(r'PONDELOK(.*)UTOROK(.*)STREDA(.*)ŠTVRTOK(.*)PIATOK(.*)BEDNAR',
                               self.content.text,
                               re.DOTALL
                               ).groups()
            for food in groups[day].split('\n'):
                if food.strip():
                    food = re.findall(r'\s*-\s*(.*)', food.strip())[0]
                    menu.add_item(food)
        except (IndexError, AttributeError) as ex:
            menu.add_item('Problem with parsing - {}'.format(ex))
        return menu


class BreweriaRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Breweria'
        self.url = 'http://breweria.sk/slimak/menu/denne-menu/'

    def retrieve_menu(self, day=TODAY) -> Menu:
        r = requests.get(self.url)
        self.content = BeautifulSoup(r.content, 'html.parser')
        return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        try:
            day_elements = self.content.select('.tabs__pane')[day].select('p')
            menu.add_item(self.clean_food_name(day_elements[0].text))
            for price, food in zip(day_elements[1::2], day_elements[2::2]):
                menu.add_item(self.clean_food_name(food.text), self.clean_price(price.text))
        except IndexError as ex:
            menu.add_item('Problem with parsing - {}'.format(ex))
        return menu

    def clean_food_name(self, name):
        return re.findall(r'\s*[lg]+\.\s+(.*)', name)[0]

    def clean_price(self, price):
        return float(re.findall(r'(\d,\d{2})', price)[0].replace(',', '.'))


class DonQuijoteRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Don Quijote (4.9€ / 4.4€ bez polievky)'
        self.url = 'https://www.facebook.com/Don-Quijote-1540992416123114/'

    def retrieve_menu(self, day=TODAY) -> Menu:
        token_json = self.get_access_token()
        posts = self.get_last_messages(token_json)
        self.content = posts['data'][0]['message']
        return self.parse_menu(day)

    def get_last_messages(self, token_json):
        r = requests.get('https://graph.facebook.com/1540992416123114/feed', params=token_json)
        token_json = json.loads(r.text)
        return token_json

    def get_access_token(self):
        r = requests.get('https://graph.facebook.com/oauth/access_token?grant_type=client_credentials'
                         '&client_id={}&client_secret={}'.format(FB_APP_ID, FB_APP_SECRET))
        return json.loads(r.text)  # access token

    def parse_menu(self, day):
        menu = Menu(self.name)
        all_days_menu = self._parse_all_days()
        selected_day_menu = self._parse_day(all_days_menu[day])
        for food in selected_day_menu:
            menu.add_item(food)
        return menu

    def _parse_all_days(self):
        res = re.search(r'Pondelok:\s*\n(.*)Utorok:\s*\n(.*)Streda:\s*\n(.*)Štvrtok:\s*\n(.*)Piatok:\s*\n(.*)^\s*$',
                         self.content,
                         re.DOTALL | re.MULTILINE)
        if res:
            return res.groups()
        return ['https://www.facebook.com/Don-Quijote-1540992416123114/ (cekni si to sam)' for i in range(7)]

    def _parse_day(self, content):
        return re.findall(r'\w\s(.*) \(.*\)\s*', content)


class DreamsRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Dream\'s'
        self.url = 'http://www.dreams-res.sk/menu/daily_menu_sk.php'

    def retrieve_menu(self, day=TODAY) -> Menu:
        r = requests.get(self.url)
        self.content = BeautifulSoup(r.content, 'html.parser')
        return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        foods = self.content.find_all('td', id='jedlo')
        prices = self.content.find_all('td', id='cena')
        for food, price in zip(foods, prices):
            try:
                food = re.findall(r'(.*)\s+(?:\S)', food.text)[0]
                price = price.text.strip().replace(',', '.')
                if price:
                    menu.add_item(food, float(price[:-2]))
                else:
                    menu.add_item(food)
            except IndexError as ex:
                menu.add_item('Problem with parsing - {} - {}'.format(ex, food.text))
        return menu


class GastrohouseRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Gastrohouse a.k.a. vývarovňa Slimák (3.8€)'
        self.url = 'http://gastrohouse.sk/'

    def retrieve_menu(self, day=TODAY) -> Menu:
        r = requests.get(self.url)
        self.content = BeautifulSoup(r.content, 'html.parser')
        return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        blocks = self.content.select('.td-main-page-wrap')[0].select('ul')
        menu_block = blocks[-2] if len(blocks) == 7 else blocks[-1]     # if there is menu for 2 days, there is 7 blocks
        for food in menu_block.select('li'):                            # if there is menu for 1 day, there is only 6 blocks
            menu.add_item(food.text)
        return menu


class JarosovaRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Jedáleň Jarošová (3.79€)'
        self.url = 'http://vasestravovanie.sk/jedalny-listok-sav/'

    def retrieve_menu(self, day=TODAY) -> Menu:
        r = requests.get(self.url)
        self.content = BeautifulSoup(r.content, 'html.parser')
        return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        try:
            table = self.content.find('table')
            date_rows = table.select('tbody tr')[1::10]
            dates = [i.select('span')[0].text for i in date_rows]
            day_index = dates.index(datetime.today().strftime('%d.%m.%Y'))
            els = table.select('tbody tr')[10 * day_index:10 * day_index + 9]
            for idx, i in enumerate(els):
                menu.add_item(i.select('span')[2].text if idx == 1 else i.select('span')[3].text)
        except ValueError as ex:
            menu.add_item(str(ex))
        return menu


class OtherRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Iné (hlasuj pomocou emoji)'
        self.url = None

    def retrieve_menu(self, day=TODAY) -> Menu:
        menu = Menu(self.name)
        menu.add_item('Panda (5.8€) :panda_face:')
        menu.add_item('Cigipanda :man::skin-tone-5:')
        menu.add_item('Punjabi Dhaba :man_with_turban:')
        menu.add_item('Casa Inka :dancer:')
        menu.add_item('Freshmarket :watermelon:')
        menu.add_item('Kantína :fork_and_knife:')
        menu.add_item('Kebab Miletička :taco:')
        menu.add_item('Hladovka :middle_finger:')
        return menu
