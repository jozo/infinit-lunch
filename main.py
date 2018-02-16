import os
import asyncio
from datetime import datetime

import aiohttp
from aiohttp import web

from restaurants import FormattedMenus, SafeRestaurant, BednarRestaurant, BreweriaRestaurant, DonQuijoteRestaurant, \
    DreamsRestaurant, GastrohouseRestaurant, JarosovaRestaurant, OtherRestaurant, KantinaRestaurant

# SLACK_HOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
from slack import Channel

SLACK_HOOK = os.environ.get('SLACK_HOOK', None)
SECRET_KEY = os.environ.get('SECRET_KEY', None)
DEBUG = bool(os.environ.get('DEBUG', False))


def is_work_day():
    return datetime.today().weekday() in range(0, 5)


def should_send_to_slack(secret_key):
    return SLACK_HOOK and secret_key == SECRET_KEY


async def retrieve_menus(session):
    futures = [
        # SafeRestaurant(JarosovaRestaurant(session)).retrieve_menu(),
        # SafeRestaurant(BednarRestaurant(session)).retrieve_menu(),
        SafeRestaurant(BreweriaRestaurant(session)).retrieve_menu(),
        SafeRestaurant(DonQuijoteRestaurant(session)).retrieve_menu(),
        # SafeRestaurant(DreamsRestaurant(session)).retrieve_menu(),
        SafeRestaurant(GastrohouseRestaurant(session)).retrieve_menu(),
        SafeRestaurant(KantinaRestaurant(session)).retrieve_menu(),
        SafeRestaurant(OtherRestaurant()).retrieve_menu(),
    ]

    menus = []
    for future in asyncio.as_completed(futures):
        menus.append(await future)

    return menus


async def index(request):
    if is_work_day():
        with aiohttp.ClientSession() as session:
            menus = FormattedMenus(await retrieve_menus(session))
            secret_key = request.match_info.get('secret_key')
            if should_send_to_slack(secret_key):
                await Channel(SLACK_HOOK, session).send(menus)
            return web.Response(text=str(menus))
    return web.Response(text='Come on Monday-Friday')


app = web.Application(debug=True)
app.router.add_get('/', index)
app.router.add_get('/{secret_key}', index)

if __name__ == '__main__':
    web.run_app(app, host='localhost', port=5000)
