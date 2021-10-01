#!/usr/bin/env python3

import asyncio
import os
from datetime import datetime

import aiohttp
from aiohttp import web
from raven import Client

from restaurants import (
    AvalonRestaurant,
    CasaInkaRestaurant,
    CityCantinaRosumRestaurant,
    FormattedMenus,
    MonastikRestaurant,
    OlivaRestaurant,
    OtherRestaurant,
    SafeRestaurant,
    TOTOCantinaRestaurant,
    TOTORestaurant,
    TOTOPizzaAndGrillRestaurant,
)
from slack import Channel

# SLACK_HOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
SLACK_HOOK = os.environ.get("SLACK_HOOK", None)
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", None)
SECRET_KEY = os.environ.get("SECRET_KEY", None)
DEBUG = bool(os.environ.get("DEBUG", False))


def is_work_day():
    return datetime.today().weekday() in range(0, 5)


def should_send_to_slack(secret_key):
    return SLACK_HOOK and secret_key == SECRET_KEY


async def retrieve_menus(session):
    futures = [
        SafeRestaurant(TOTORestaurant(session)).retrieve_menu(),
        SafeRestaurant(TOTOCantinaRestaurant(session)).retrieve_menu(),
        SafeRestaurant(AvalonRestaurant(session)).retrieve_menu(),
        SafeRestaurant(OlivaRestaurant(session)).retrieve_menu(),
        SafeRestaurant(CasaInkaRestaurant(session)).retrieve_menu(),
        SafeRestaurant(MonastikRestaurant(session)).retrieve_menu(),
        SafeRestaurant(CityCantinaRosumRestaurant(session)).retrieve_menu(),
        SafeRestaurant(TOTOPizzaAndGrillRestaurant(session)).retrieve_menu(),
    ]

    # Add list of other restaurants first, will be in header.
    menus = [await SafeRestaurant(OtherRestaurant()).retrieve_menu()]
    for future in asyncio.as_completed(futures):
        menus.append(await future)

    return menus


async def index(request):
    if is_work_day():
        async with aiohttp.ClientSession() as session:
            menus = FormattedMenus(await retrieve_menus(session))
            secret_key = request.match_info.get("secret_key")
            if should_send_to_slack(secret_key):
                await Channel(SLACK_HOOK, session).send(menus)
            return web.Response(text=str(menus))
    return web.Response(text="Come on Monday-Friday")


sentry_client = Client()  # credentials is taken from environment variable SENTRY_DSN

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/{secret_key}", index)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=5000)
