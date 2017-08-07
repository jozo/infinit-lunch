import abc
import re
from datetime import datetime

NO_PRICE = object()
TODAY = datetime.today().weekday()


class Menu:
    def __init__(self, rest_name: str) -> None:
        self.restaurant_name = rest_name
        self.foods = []
        self.prices = []

    def add_item(self, food: str, price=NO_PRICE):
        self.foods.append(food.strip())
        self.prices.append(price)

    def __str__(self):
        items = ['']


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

    def retrieve_menu(self, day=TODAY) -> Menu:
        pass

    def parse_menu(self, day):
        menu = Menu(self.name)
        all_days_menu = self._parse_all_days()
        selected_day_menu = self._parse_day(all_days_menu[day])
        for food in selected_day_menu:
            menu.add_item(food)
        return menu

    def _parse_all_days(self):
        return re.search(r'Pondelok:\n(.*)Utorok:\n(.*)Streda:\n(.*)Štvrtok:\n(.*)Piatok:\n(.*)^\s*$',
                         self.content,
                         re.DOTALL | re.MULTILINE).groups()

    def _parse_day(self, content):
        return re.findall(r'\w\s(.*) \(.*\)\s*', content)
