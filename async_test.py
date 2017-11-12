import asyncio

import aiohttp
from aiohttp import web

from restaurants import FormattedMenus, SafeRestaurant, BednarRestaurant, BreweriaRestaurant, DonQuijoteRestaurant, DreamsRestaurant, \
    GastrohouseRestaurant, JarosovaRestaurant, OtherRestaurant


async def retrieve_menus():
    with aiohttp.ClientSession() as session:
        futures = [
            SafeRestaurant(JarosovaRestaurant(session)).retrieve_menu(),
            SafeRestaurant(BednarRestaurant(session)).retrieve_menu(),
            SafeRestaurant(BreweriaRestaurant(session)).retrieve_menu(),
            SafeRestaurant(DonQuijoteRestaurant(session)).retrieve_menu(),
            SafeRestaurant(DreamsRestaurant(session)).retrieve_menu(),
            SafeRestaurant(GastrohouseRestaurant(session)).retrieve_menu(),
            SafeRestaurant(OtherRestaurant()).retrieve_menu(),
        ]

        menus = []
        for future in asyncio.as_completed(futures):
            menus.append(await future)

        return menus


async def index(request):
    menus = FormattedMenus(await retrieve_menus())
    return web.Response(text=str(menus))


app = web.Application(debug=True)
app.router.add_get('/', index)


if __name__ == '__main__':
    web.run_app(app, host='localhost', port=5001)
