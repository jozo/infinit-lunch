import os
import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask
import time
import restaurants

# SLACK_HOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
from slack import Channel

SLACK_HOOK = os.environ.get('SLACK_HOOK', None)
SECRET_KEY = os.environ.get('SECRET_KEY', None)
FB_APP_ID = os.environ.get('FB_APP_ID', None)
FB_APP_SECRET = os.environ.get('FB_APP_SECRET', None)
DEBUG = bool(os.environ.get('DEBUG', False))

app = Flask(__name__)


def check_for_errors(func):
    def func_wrapper(url):
        try:
            r = requests.get(url)
            if r.ok:
                soup = BeautifulSoup(r.content, 'html.parser')
                day = datetime.today().weekday()
                return func(soup, day)
        except IndexError:
            return ['Scrapping problem. Fix it: https://github.com/fadawar/infinit-lunch']
        except Exception:
            return ['Unknown error']
        return ['Problem with request']
    return func_wrapper


@check_for_errors
def scrap_dreams(soup, day):
    elements = soup.find_all('td', id='jedlo')
    return [el.text for el in elements]


@check_for_errors
def scrap_breweria(soup, day):
    elements = soup.select('.tabs__pane')[day].select('.desc__content')
    return [el.text for el in elements if len(el.text) > 1]


@check_for_errors
def scrap_bednar(soup, day):
    groups = re.search(r'PONDELOK(.*)UTOROK(.*)STREDA(.*)ŠTVRTOK(.*)PIATOK(.*)BEDNAR', soup.text, re.DOTALL).groups()
    return [i for i in groups[day].split('\n') if i]


@check_for_errors
def scrap_gastrohouse(soup, day):
    els = soup.select('.td-main-page-wrap')[0].select('ul')[-1].select('li')
    return [i.text for i in els]


def get_other_restaurants():
    return ['Panda :panda_face:\nCigipanda :man::skin-tone-5:\nPunjabi Dhaba :man_with_turban:\nCasa Inka :dancer:\n'
            'Freshmarket :watermelon:']


def send_to_slack(messages, secret_key):
    if SLACK_HOOK and secret_key == SECRET_KEY:
        for msg in messages:
            requests.post(SLACK_HOOK, data=json.dumps({'text': msg}))


def create_message(items):
    messages = ['*MENU {}*\n'.format(datetime.today())]
    for item in items:
        msg = '\n\n*{}*\n'.format(item['restaurant'])
        msg += '\n'.join(item['menu'])
        messages.append(msg)
    return messages


def is_work_day():
    return datetime.today().weekday() in range(0, 5)


def retrieve_menus():
    return [
        restaurants.DonQuijoteRestaurant().retrieve_menu(),
        restaurants.JarosovaRestaurant().retrieve_menu(),
    ]


def should_send_to_slack(secret_key):
    return SLACK_HOOK and secret_key == SECRET_KEY


@app.route('/', defaults={'secret_key': 'wrong key :('})
@app.route('/<secret_key>')
def hello(secret_key):
    if is_work_day():
        menus = restaurants.FormattedMenus(retrieve_menus())
        if should_send_to_slack(secret_key):
            Channel(SLACK_HOOK, requests).send(menus)

        # msg = create_message([
        #     {'restaurant': 'Dream\'s', 'menu': scrap_dreams('http://www.dreams-res.sk/menu/daily_menu_sk.php')},
        #     {'restaurant': 'Breweria', 'menu': scrap_breweria('http://breweria.sk/slimak/menu/denne-menu/')},
        #     {'restaurant': 'Bednar', 'menu': scrap_bednar('http://bednarrestaurant.sk/new/wordpress/?page_id=62')},
        #     {'restaurant': 'Jedalen Jarosova', 'menu': scrap_jarosova('http://vasestravovanie.sk/jedalny-listok-jar/')},
        #     {'restaurant': 'Gastrohouse (vyvarovna Slimak)', 'menu': scrap_gastrohouse('http://gastrohouse.sk')},
        #     {'restaurant': 'Don Quijote', 'menu': scrap_don_quijote()},
        #     {'restaurant': 'Ine (hlasuj pomocou emoji)', 'menu': get_other_restaurants()},
        # ])
        # send_to_slack(msg, secret_key)
        return '<pre>{}</pre>'.format(menus)
    else:
        return 'Come on Monday-Friday'


if __name__ == '__main__':
    app.run(debug=DEBUG)
