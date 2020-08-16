import abc
import logging
import os
import re
from datetime import datetime, date, timedelta

from bs4 import BeautifulSoup, element

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

logger = logging.getLogger(__name__)


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
        except NotImplementedError:
            menu = Menu(self.restaurant.name)
            menu.add_item('Check menu yourself on {}'.format(self.restaurant.url))
            return menu
        except:
            from main import sentry_client
            sentry_client.captureException()
            logger.exception('Error scraping %s', self.restaurant.name)

            menu = Menu(self.restaurant.name)
            menu.add_item('Problem with scraping. Check menu yourself on {}'.format(self.restaurant.url))
            return menu


class StandardRetrieveMenuMixin:
    async def retrieve_menu(self, day=TODAY) -> Menu:
        async with self.aio_session.get(self.url) as resp:
            self.content = BeautifulSoup(await resp.text(), 'html.parser')
        return self.parse_menu(day)


class SMERestaurantMixin:
    def parse_menu(self, day):
        menu = Menu(self.name)
        for item in self.content.find(class_='dnesne_menu').find_all(class_='jedlo_polozka'):
            menu.add_item(item.get_text(strip=True))
        return menu


class DonQuijoteRestaurant(SMERestaurantMixin, StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Don Quijote (5.5€)'
        self.url = 'https://restauracie.sme.sk/restauracia/don-quijote_7436-nove-mesto_2653/denne-menu'


class KantinaRestaurant(SMERestaurantMixin, StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Kantína (4.8€ / 4€ bez polievky)'
        self.url = 'https://restauracie.sme.sk/restauracia/kantina-vsetko-okolo-jedla_10102-bratislava_2983/denne-menu'


class PlzenskaBranaRestaurant(StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Plzenská brána (5.70)'
        self.url = 'https://menucka.sk/denne-menu/bratislava/plzenska-brana'

    def parse_menu(self, day):
        menu = Menu(self.name)
        container = self.content.find(id='restaurant-actual-menu-id-2024')
        if not container:
            menu.add_item('Problem with scraping. Check menu yourself on {}'.format(self.url))
            return menu
        for item in container.find_all(class_='col-xs-10'):
            text = item.get_text(strip=True)
            if text:
                menu.add_item(text)
        return menu


class DreamsRestaurant(StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Dream\'s'
        self.url = 'http://www.dreams-res.sk/menu/daily_menu_sk.php'

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


class MenuUJelena(SMERestaurantMixin, StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Menu u Jeleňa'
        self.url = 'https://restauracie.sme.sk/restauracia/menu-u-jelena_9787-nove-mesto_2653/denne-menu'


class GastrohouseRestaurant(StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Gastrohouse a.k.a. vývarovňa Slimák (4.2€)'
        self.url = 'http://gastrohouse.sk/'

    def parse_menu(self, day):
        menu = Menu(self.name)
        daily_menu = self.content.select_one('section.denne-menu').find_all('section')
        today_menu = [section for section in daily_menu
                      if section.find('h2').text.rstrip().lower().startswith(DAY_NAMES[day])]
        if not today_menu:
            raise ValueError('Can not find menu')

        for li in today_menu[0].find_all('li'):
            # price = float(li.find_all('div')[-1].text.strip()[:-2].replace(',', '.'))
            menu.add_item(li.find('h3').text.strip())

        return menu


class TOTORestaurant(StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'TOTO (4.9€ / 4.2€ bez polievky / 6.2€ extra menu / 7.4€ business menu)'
        self.url = 'http://www.totorestaurant.sk/'

    def parse_menu(self, day):
        menu = Menu(self.name)
        date_div = self.content.select('div.date')[day]

        for sibling in date_div.next_siblings:
            if isinstance(sibling, element.NavigableString):
                continue
            if sibling.name in ['h2', 'div']:
                break
            text = sibling.text.strip()
            if text:
                menu.add_item(text)

        return menu


class AvalonRestaurant(SMERestaurantMixin, StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Avalon'
        self.url = 'https://restauracie.sme.sk/restauracia/avalon-restauracia_174-ruzinov_2980/denne-menu'


class CasaInkaRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Casa Inka (5.5€ / 6€ špecialita)'
        self.url = 'http://www.casa-inka.sk/index.php?page=jedalny&kategoria=menu'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        raise NotImplementedError


class BezzinkaRestaurant(SMERestaurantMixin, StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Bezzinka (4.5€)'
        self.url = 'https://restauracie.sme.sk/restauracia/bezzinka_265-ruzinov_2980/denne-menu'


class OlivaRestaurant(Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'Oliva'
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        self.url = f'https://www.hotel-premium.sk/files/hotel/downloads/{monday:%y%m%d}_Dobre_obedy.pdf'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        raise NotImplementedError


class CityCantinaRosumRestaurant(StandardRetrieveMenuMixin, Restaurant):
    def __init__(self, session) -> None:
        super().__init__()
        self.aio_session = session
        self.content = None
        self.name = 'City Cantina Rosum'
        self.url = 'https://restauracie.sme.sk/restauracia/city-cantina-rosum_8439-ruzinov_2980/denne-menu'

    def parse_menu(self, day):
        # Remove useless strings in the beginning and end.
        rows = self.content.find(class_='dnesne_menu').find_all(class_='jedlo_polozka')[1:-1]
        items = []
        for row in rows:
            item = row.get_text(strip=True).capitalize()
            if item.startswith('€()'):
                items.pop()  # Dish is empty. Remove its heading.
            elif items and not 'Alergény' in items[-1]:
                # Concatenate items describing same dish to single line.
                items[-1] = items[-1] + ' ' + item
            else:
                items.append(item)  # Start of new dish.

        menu = Menu(self.name)
        for item in items:
            menu.add_item(item)

        return menu


class OtherRestaurant(Restaurant):
    def __init__(self) -> None:
        super().__init__()
        self.content = None
        self.name = 'Iné'
        self.url = None

    async def retrieve_menu(self, day=TODAY) -> Menu:
        menu = Menu(self.name)
        menu.add_item(':car: Bistro.sk')
        menu.add_item(':ramen: Mango')
        menu.add_item(':hamburger: Bigger')
        menu.add_item(':male-cook: Chefstreet')
        menu.add_item(':watermelon: Freshmarket')
        menu.add_item(':middle_finger: Hladovka')
        return menu
