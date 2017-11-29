from datetime import datetime
from unittest.mock import Mock, call
import pytest

from bs4 import BeautifulSoup

from restaurants import DonQuijoteRestaurant, Menu, FormattedMenus, SafeRestaurant, GastrohouseRestaurant
from slack import Channel


class TestDonQuijoteRestaurant:
    def setup(self):
        self.restaurant = DonQuijoteRestaurant(session=None)
        self.restaurant.content = DON_FB_MESSAGE

    def test_can_find_monday_menu(self):
        menu = self.restaurant.parse_menu(day=0)
        assert menu.foods == ['Letná minestrone',
                              'Medovo-horčicové kuracie prsia so špargľou a hruškami, bylinková ryža',
                              'Penne so špenátom a gorgonzolou']


# class TestChannel:
#     def test_send_provided_messages(self):
#         http = Mock()
#         url = 'http://url'
#         ch = Channel(url, http)
#         ch.send(['first message', 'second message'])
#
#         assert http.post.call_count == 2
#         assert http.post.call_args_list == [call(url, data='{"text": "first message"}'),
#                                             call(url, data='{"text": "second message"}')]


class TestMenu:
    def test_string_representation(self):
        m = Menu('Restaurant A')
        m.add_item('Food 1', 4.5)
        m.add_item('Food 2')

        assert str(m) == MENU_1


class TestFormattedMenus:
    def test_will_format_messages(self):
        menus = [
            Menu('Restaurant A'),
            Menu('Restaurant B'),
        ]
        menus[0].add_item('Food 1')
        menus[0].add_item('Food 2', 4.5)
        menus[1].add_item('Food 3')
        formatted_menus = FormattedMenus(menus, today=datetime(2017, 8, 10))

        assert len(formatted_menus) == 2
        assert str(formatted_menus[0]) == FORMATTED_MENU_1
        assert str(formatted_menus) == FORMATTED_MENU_2


# class TestSafeRestaurant:
#     def setup(self):
#         self.nested_restaurant = DonQuijoteRestaurant()
#         self.restaurant = SafeRestaurant(self.nested_restaurant)
#
#     def test_returns_menu_if_everything_ok(self):
#         self.nested_restaurant.retrieve_menu = lambda: ['Letná minestrone']
#         menu = self.restaurant.retrieve_menu()
#
#         assert menu == ['Letná minestrone']
#
#     def test_returns_url_for_restaurant_if_exception(self):
#         self.nested_restaurant.retrieve_menu = lambda: exec('raise(Exception())')
#         menu = self.restaurant.retrieve_menu()
#
#         assert menu.foods == ['Problem with scraping. Check menu yourself on '
#                               'https://www.facebook.com/Don-Quijote-1540992416123114/']


class TestGastrohouse:
    def test_correct_parse_monday(self):
        with open('tests/gastrohouse/2017-11-13.htm', 'r') as f:
            rest = GastrohouseRestaurant(session=None)
            rest.content = BeautifulSoup(f.read(), 'html.parser')
            menu = rest.parse_menu(0)
            assert menu.foods == [
                'Šošovicová polievka',
                'Hovädzie na bratislavský spôsob, knedľa',
                'Bravčový zahorácky závitokm, ryža',
                'Kuracie soté so zeleninou, ryža',
                'Zemiakový prívarok s fašírkou',
                'Ryžový nákyp s jablkami',
            ]

    def test_correct_parse_monday2(self):
        with open('tests/gastrohouse/2017-11-20.htm', 'r') as f:
            rest = GastrohouseRestaurant(session=None)
            rest.content = BeautifulSoup(f.read(), 'html.parser')
            menu = rest.parse_menu(0)
            assert menu.foods == [
                'Zeleninová polievka s haluškami',
                'Hovädzie Esterházy, knedľa',
                'Bravčové karé po srbsky, ryža',
                'Kurací gyros s tzatziki, hranolky',
                'Fazuľový prívarok s fašírkou, varené zemiaky',
                'Tvarohová žemlovka s jablkami',
            ]

    def test_correct_parse_tuesday(self):
        with open('tests/gastrohouse/2017-11-21.htm', 'r') as f:
            rest = GastrohouseRestaurant(session=None)
            rest.content = BeautifulSoup(f.read(), 'html.parser')
            with pytest.raises(ValueError):
                rest.parse_menu(1)

    def test_correct_parse_wednesday(self):
        with open('tests/gastrohouse/2017-11-22.htm', 'r') as f:
            rest = GastrohouseRestaurant(session=None)
            rest.content = BeautifulSoup(f.read(), 'html.parser')
            menu = rest.parse_menu(2)
            assert menu.foods == [
                'Zemiaková kulajda',
                'Hovädzie na tekvicovej omáčke, knedľa',
                'Bravčové mexické soté, ryža',
                'Kuracie vyprážané stehno, príloha podľa vlastného výberu',
                'Francúzske zemiaky',
                'Špenátové halušky so syrovou omáčkou',
            ]

    def test_correct_parse_thursday(self):
        with open('tests/gastrohouse/2017-11-23.htm', 'r') as f:
            rest = GastrohouseRestaurant(session=None)
            rest.content = BeautifulSoup(f.read(), 'html.parser')
            with pytest.raises(ValueError):
                rest.parse_menu(3)

    def test_correct_parse_friday(self):
        with open('tests/gastrohouse/2017-11-24.htm', 'r') as f:
            rest = GastrohouseRestaurant(session=None)
            rest.content = BeautifulSoup(f.read(), 'html.parser')
            menu = rest.parse_menu(4)
            assert menu.foods == [
                'Držková polievka',
                'Slepačia polievka',
                'Hovädzie na paradajkovej omáčke, knedľa',
                'Bravčová roláda, varené zemiaky',
                'Kuracie prsia na kari omáčke, ryža',
                'Bryndzové taštičky so slaninkou a smotanou',
                'Vyprážaný syr, opekané zemiaky',
            ]


MENU_1 = """*Restaurant A*
1. Food 1 (4.5€)
2. Food 2"""


FORMATTED_MENU_1 = """*Obedy v štvrtok 10.08.2017*

*Restaurant A*
1. Food 1
2. Food 2 (4.5€)"""

FORMATTED_MENU_2 = """*Obedy v štvrtok 10.08.2017*

*Restaurant A*
1. Food 1
2. Food 2 (4.5€)

*Restaurant B*
1. Food 3"""

DON_FB_MESSAGE = """Dobre ranko vsetkym priatelom a znamym prajeme:)

a....nove obedove menu na tento tyzden prinasame...;)

OBEDOVÉ MENU na 7.8.-11.8. (11:00 - 14:00)
Obedové menu s polievkou: 4.90€, bez polievky: 4.40€

Pondelok:
250ml Letná minestrone (9)
300/140g Medovo-horčicové kuracie prsia so špargľou a hruškami, bylinková ryža (7,10)
300g Penne so špenátom a gorgonzolou (1,3,7)

Utorok:
250ml Šošovicovo-paradajková polievka s baby špenátom (7)
300/140g Pečené hovädzie so šalátom, tzatziky, zeleninovým kuskusom a pita chlebom (1,3,7,10)
300g Zemiakový quiche s baklažánom, cuketou, paradajkami, zapečený s camembertom, listový šalát (1,3,7)

Streda:
250ml Cuketový krém s bazalkou (7)
300/100g Špenátové tagliatelle s lososom, smotanou a kôprom (1,3,7)
300g Šampiňónové rizoto s pečenou tekvicou a parmezánom (7)

Štvrtok:
250ml Špenátovo-šampiňónová polievka s tortellini (1,3,7)
300/140g Grilovaná panenka na pomarančoch a badiáne, tlačené zemiačky s cibuľkou (7,9,10)
300g Mrkvovo-cícerové karí s kokosovým mliekom a tofu, basmati ryža (6,7)

Piatok:
250ml Chladený hráškový krém s crème fraîche (7)
300/140g Grilované kuracie prsia s paradajkovou “bruschettou”, parmezánom a sušenou šunkou, risotto bianco (7,12)
300g Gnocchi s bylinkovým maslom, grilovanou zeleninou a balkánskym syrom (1,3,7)

Všetky naše jedlá MÔŽU OBSAHOVAŤ ktorýkoľvek z nižšie uvedených alergénov v stopových množstvách.
1. Obilniny obsahujúce lepok (t.j. pšenica, raž, jačmeň, ovos, špalda, kamut alebo ich hybridné odrody); 2. Kôrovce a výrobky z nich; 3. Vajcia a výrobky z nich; 4. Ryby a výrobky z nich; 5. Arašidy a výrobky z nich; 6. Sójové zrná a výrobky z nich; 7. Mlieko a výrobky z neho; 8. Orechy, ktorými sú mandle, lieskové orechy, vlašské orechy, kešu, pekanové orechy, para orechy, pistácie, makadamové orechy a queenslandské orechy a výrobky z nich; 9. Zeler a výrobky z neho; 10. Horčica a výrobky z nej; 11. Sezamové semená a výrobky z nich; 12. Oxid siričitý a siričitany v koncentráciách vyšších ako 10 mg/kg alebo 10 mg/l; 13. Vlčí bob a výrobky z neho; 14. Mäkkýše a výrobky z nich"""