import aiohttp
import asyncio
from aiohttp import web
from bs4 import BeautifulSoup

from restaurants import Menu, Restaurant, TODAY, FormattedMenus


class JarosovaRestaurant(Restaurant):
    def __init__(self, aio_session) -> None:
        super().__init__()
        self.aio_session = aio_session
        self.content = None
        self.name = 'Jedáleň Jarošová (3.79€)'
        self.url = 'http://vasestravovanie.sk/jedalny-listok-sav/'

    async def retrieve_menu(self, day=TODAY) -> Menu:
        async with self.aio_session.get(self.url) as resp:
            self.content = BeautifulSoup(await resp.text(), 'html.parser')
            return self.parse_menu(day)

    def parse_menu(self, day):
        menu = Menu(self.name)
        try:
            table = self.content.find('table')
            rows = [td for td in table.select('tbody tr td') if td.attrs.get('colspan') in ('5', '6')]
            day_size = len(rows) // 5
            idx = day_size * day
            for td in rows[idx:idx+day_size]:
                menu.add_item(td.text)
        except ValueError as ex:
            menu.add_item(str(ex))
        return menu


async def retrieve_menus():
    with aiohttp.ClientSession() as session:
        futures = [
            JarosovaRestaurant(session).retrieve_menu(day=3),
            JarosovaRestaurant(session).retrieve_menu(day=3),
            JarosovaRestaurant(session).retrieve_menu(day=3),
            JarosovaRestaurant(session).retrieve_menu(day=3),
            JarosovaRestaurant(session).retrieve_menu(day=3),
        ]

        menus = []
        for future in asyncio.as_completed(futures):
            menus.append(await future)

        return menus


async def index(request):
    menus = FormattedMenus(await retrieve_menus())
    return web.Response(text=str(menus))


def setup_routes(app):
    app.router.add_get('/', index)


if __name__ == '__main__':
    app = web.Application(debug=True)
    setup_routes(app)
    web.run_app(app, host='localhost', port=5001)
