import json
import os
import re
import abc
from datetime import datetime

import requests

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


class DonQuijoteRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Don Quijote (4.9€ / 4.40€)'

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
        return re.search(r'Pondelok:\s*\n(.*)Utorok:\s*\n(.*)Streda:\s*\n(.*)Štvrtok:\s*\n(.*)Piatok:\s*\n(.*)^\s*$',
                         self.content,
                         re.DOTALL | re.MULTILINE).groups()

    def _parse_day(self, content):
        return re.findall(r'\w\s(.*) \(.*\)\s*', content)
