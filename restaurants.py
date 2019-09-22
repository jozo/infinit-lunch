import json
import os
import re
import abc
from datetime import datetime, timedelta

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
DAY_NAMES2 = [              # vysklonovane nazvy
    'pondelok',
    'utorok',
    'stredu',
    'štvrtok',
    'piatok',
    'sobotu',
    'nedeľu',
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
        items += [
            '{}{}'.format(food, self.format_price(price))
            for food, price in zip(self.foods, self.prices)
        ]
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
        return "*Obedy v {} {}*\n\n{}".format(DAY_NAMES2[self.today.weekday()],
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
    Catch all exceptions so the application will not break
    """

    def __init__(self, restaurant) -> None:
        super().__init__()
        self.restaurant = restaurant

    async def retrieve_menu(self, day=TODAY) -> Menu:
        try:
            return await self.restaurant.retrieve_menu(day)
        except:
            from main import sentry_client
            sentry_client.captureException()

            menu = Menu(self.restaurant.name)
            menu.add_item('Problem with scraping. Check menu yourself on {}'.format(self.restaurant.url))
            return menu


class DonQuijoteRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Don Quijote (5.5€)'
        self.url = 'https://www.facebook.com/Don-Quijote-1540992416123114/'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        token_json = await self.get_access_token()
        token_for_url = '&'.join([f'{k}={v}' for k, v in token_json.items()])
        messages = await self.this_week_messages(token_for_url, day)
        menu_textual = self.find_textual_menu(messages, day)
        if menu_textual:
            return menu_textual
        return await self.find_image_menu(messages, token_for_url)

    async def get_access_token(self):
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=client_credentials' \
              '&client_id={}&client_secret={}'.format(FB_APP_ID, FB_APP_SECRET)
        async with self.aio_session.get(url) as resp:
            return json.loads(await resp.text())  # access token

    async def this_week_messages(self, token_for_url, day):
        last_saturday = datetime.now() - timedelta(days=(2 + day))
        url = 'https://graph.facebook.com/1540992416123114/feed?' \
              'fields=id,message,created_time,attachments{media,media_type}'
        async with self.aio_session.get(url + '&' + token_for_url) as resp:
            messages = json.loads(await resp.text())['data']
            return list(filter(
                lambda msg: datetime.strptime(msg['created_time'][:10], '%Y-%m-%d') > last_saturday,
                messages
            ))

    def find_textual_menu(self, messages, day):
        for msg in messages:
            if 'OBEDOVÉ MENU' in msg['message']:
                self.content = msg['message']
                return self.parse_menu(day)

    async def find_image_menu(self, messages, token_for_url):
        for msg in messages:
            if 'attachments' in msg and msg['attachments']['data'][0]['media_type'] == 'photo':
                menu = Menu(self.name)
                menu.add_item(msg['attachments']['data'][0]['media']['image']['src'])
                return menu
        raise ValueError('No menu found')

    def parse_menu(self, day):
        menu = Menu(self.name)
        lines = [line.strip() for line in self.content.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if line.strip().lower().startswith(DAY_NAMES[day]):
                for food in lines[index+1:index+4]:
                    menu.add_item(food)
                return menu


class KantinaRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Kantína (4.8€ / 4€ bez polievky)'
        self.url = 'https://restauracie.sme.sk/restauracia/kantina-vsetko-okolo-jedla_10102-bratislava_2983/denne-menu'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        async with self.aio_session.get(self.url) as resp:
            self.content = BeautifulSoup(await resp.text(), 'html.parser')
            return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        for item in self.content.find(class_='dnesne_menu').find_all(class_='jedlo_polozka'):
            menu.add_item(item.get_text(strip=True))
        return menu


class RentierRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Rentier (5.99€)'
        self.url = 'https://www.facebook.com/RentierRestauracia/'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        token_json = await self.get_access_token()
        token_for_url ='&'.join([f'{k}={v}' for k, v in token_json.items()])
        messages = await self.today_message(token_for_url)
        return await self.find_image_menu(messages, token_for_url)

    async def get_access_token(self):
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=client_credentials' \
              '&client_id={}&client_secret={}'.format(FB_APP_ID, FB_APP_SECRET)
        async with self.aio_session.get(url) as resp:
            return json.loads(await resp.text())  # access token

    async def today_message(self, token_for_url):
        url = 'https://graph.facebook.com/RentierRestauracia/feed?' \
              'fields=id,message,created_time,attachments{media,media_type}'
        async with self.aio_session.get(url + '&' + token_for_url) as resp:
            messages = json.loads(await resp.text())['data']
            return list(filter(
                lambda msg: datetime.strptime(msg['created_time'][:10], '%Y-%m-%d').date() == datetime.today().date(),
                messages
            ))

    async def find_image_menu(self, messages, token_for_url):
        for msg in messages:
            if 'attachments' in msg and msg['attachments']['data'][0]['media_type'] == 'photo':
                menu = Menu(self.name)
                menu.add_item(msg['attachments']['data'][0]['media']['image']['src'])
                return menu
        raise ValueError('No menu found')


class DreamsRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Dream\'s'
        self.url = 'http://www.dreams-res.sk/menu/daily_menu_sk.php'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        async with self.aio_session.get(self.url) as resp:
            self.content = BeautifulSoup(await resp.text(), 'html.parser')
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


class MenuUJelena(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Menu u Jeleňa'
        self.url = 'https://restauracie.sme.sk/restauracia/menu-u-jelena_9787-nove-mesto_2653/denne-menu'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        async with self.aio_session.get(self.url) as resp:
            self.content = BeautifulSoup(await resp.text(), 'html.parser')
            return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        for item in self.content.find(class_='dnesne_menu').find_all(class_='jedlo_polozka'):
            menu.add_item(item.get_text(strip=True))
        return menu


class GastrohouseRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Gastrohouse a.k.a. vývarovňa Slimák (4.2€)'
        self.url = 'http://gastrohouse.sk/'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        async with self.aio_session.get(self.url) as resp:
            self.content = BeautifulSoup(await resp.text(), 'html.parser')
            return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        daily_menu = self.content.select_one('section.denne-menu').find_all('section')
        today_menu = [section for section in daily_menu
                      if section.find('h2').text.rstrip().lower().endswith(DAY_NAMES[day])]
        if not today_menu:
            raise ValueError('Can not find menu')

        for li in today_menu[0].find_all('li'):
            # price = float(li.find_all('div')[-1].text.strip()[:-2].replace(',', '.'))
            menu.add_item(li.find('h3').text.strip())

        return menu


class OtherRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Iné'
        self.url = None

    async def retrieve_menu(self, day=TODAY) -> Menu:
        menu = Menu(self.name)
        menu.add_item('Bistro.sk :car:')
        menu.add_item('Casa Inka :dancer:')
        menu.add_item('Chlebíčkovo :baguette_bread:')
        menu.add_item('Cigipanda :man::skin-tone-5:')
        menu.add_item('Freshmarket :watermelon:')
        menu.add_item('Lotus Wok :ramen:')
        menu.add_item('PA&STE Salads :green_salad:')
        menu.add_item('Panda (6.3€) :panda_face:')
        menu.add_item('Punjabi Dhaba :man_with_turban:')
        menu.add_item('Strýko Burger :hamburger:')
        menu.add_item('Svadby a Kari :wedding:')
        menu.add_item('Hladovka :middle_finger:')
        return menu
