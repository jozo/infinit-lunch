import os
import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask

# SLACK_HOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
SLACK_HOOK = os.environ.get('SLACK_HOOK', None)
SECRET_KEY = os.environ.get('SECRET_KEY', None)

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
def scrap_jarosova(soup, day):
    els = soup.select('table tbody tr')[9 * day:9 * day + 9]
    return [i.select('span')[2].text for i in els[0:3]] + [i.select('span')[1].text for i in els[3:]]


def send_to_slack(message, secret_key):
    if SLACK_HOOK and secret_key == SECRET_KEY:
        requests.post(SLACK_HOOK, data=json.dumps({'text': message}))


def create_message(items):
    message = '*MENU {}*\n'.format(datetime.today())
    for item in items:
        message += '\n\n*{}*\n'.format(item['restaurant'])
        message += '\n'.join(item['menu'])
    return message


@app.route('/', defaults={'secret_key': 'wrong key :('})
@app.route('/<secret_key>')
def hello(secret_key):
    if datetime.today().weekday() in range(0, 5):
        msg = create_message([
            {'restaurant': 'Dream\'s', 'menu': scrap_dreams('http://www.dreams-res.sk/menu/daily_menu_sk.php')},
            {'restaurant': 'Breweria', 'menu': scrap_breweria('http://breweria.sk/slimak/menu/denne-menu/')},
            {'restaurant': 'Bednar', 'menu': scrap_bednar('http://bednarrestaurant.sk/new/wordpress/?page_id=62')},
            {'restaurant': 'Jedalen Jarosova', 'menu': scrap_jarosova('http://vasestravovanie.sk/jedalny-listok-jar/')},
        ])
        send_to_slack(msg, secret_key)
        return '<pre>{}</pre>'.format(msg)
    else:
        return 'Come on Monday-Friday'


if __name__ == '__main__':
    app.run()
