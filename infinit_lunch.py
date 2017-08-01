import os
import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask
import time

# SLACK_HOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
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
def scrap_jarosova(soup, day):
    table = soup.find('table')
    date_rows = table.select('tbody tr')[1::10]
    dates = [i.select('span')[0].text for i in date_rows]
    day_index = dates.index(datetime.today().strftime('%d.%m.%Y'))
    els = table.select('tbody tr')[10 * day_index:10 * day_index + 9]
    return [i.select('span')[2].text if idx == 1 else i.select('span')[3].text for idx, i in enumerate(els)]


@check_for_errors
def scrap_gastrohouse(soup, day):
    els = soup.select('.td-main-page-wrap')[0].select('ul')[-1].select('li')
    return [i.text for i in els]


def scrap_don_quijote():
    try:
        r = requests.get('https://graph.facebook.com/oauth/access_token?grant_type=client_credentials'
                         '&client_id={}&client_secret={}'.format(FB_APP_ID, FB_APP_SECRET))
        j = json.loads(r.text)      # access token
        r = requests.get('https://graph.facebook.com/1540992416123114/feed', params=j)
        j = json.loads(r.text)
        data = j['data'][0]['message'].split('\n')[5:-3]
        day = datetime.today().weekday()
        day_in_cycle = 0
        results = []
        skip = False
        for line in data:
            if line.strip() == '':
                day_in_cycle += 1
                skip = True     # next line is the name of the day
            elif skip:
                skip = False    # skip line
            elif day == day_in_cycle:
                results.append(line)
        return results
    except Exception:
        return ['Unknown error']


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


@app.route('/', defaults={'secret_key': 'wrong key :('})
@app.route('/<secret_key>')
def hello(secret_key):
    if datetime.today().weekday() in range(0, 5):
        t1 = time.time()
        msg = create_message([
            {'restaurant': 'Dream\'s', 'menu': scrap_dreams('http://www.dreams-res.sk/menu/daily_menu_sk.php')},
            {'restaurant': 'Breweria', 'menu': scrap_breweria('http://breweria.sk/slimak/menu/denne-menu/')},
            {'restaurant': 'Bednar', 'menu': scrap_bednar('http://bednarrestaurant.sk/new/wordpress/?page_id=62')},
            {'restaurant': 'Jedalen Jarosova', 'menu': scrap_jarosova('http://vasestravovanie.sk/jedalny-listok-jar/')},
            {'restaurant': 'Gastrohouse (vyvarovna Slimak)', 'menu': scrap_gastrohouse('http://gastrohouse.sk')},
            {'restaurant': 'Don Quijote', 'menu': scrap_don_quijote()},
            {'restaurant': 'Ine (hlasuj pomocou emoji)', 'menu': get_other_restaurants()},
        ])
        t2 = time.time()
        print('Time:', t2-t1)
        send_to_slack(msg, secret_key)
        return '<pre>{}</pre>'.format('\n'.join(msg))
    else:
        return 'Come on Monday-Friday'


if __name__ == '__main__':
    app.run(debug=DEBUG)
