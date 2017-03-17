import os
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask


# SLACK_HOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
SLACK_HOOK = os.environ.get('SLACK_HOOK', None)

app = Flask(__name__)


def scrap_dreams():
    r = requests.get('http://www.dreams-res.sk/menu/daily_menu_sk.php')
    if r.ok:
        soup = BeautifulSoup(r.content, 'html.parser')
        elements = soup.find_all('td', id='jedlo')
        return [el.text for el in elements]
    return []


def scrap_breweria():
    r = requests.get('http://breweria.sk/slimak/menu/denne-menu/')
    if r.ok:
        soup = BeautifulSoup(r.content, 'html.parser')
        day = datetime.today().weekday()
        elements = soup.select('.tabs__pane')[day].select('.desc__content')
        return [el.text for el in elements if len(el.text) > 1]
    return []


def scrap_bednar():
    r = requests.get('http://bednarrestaurant.sk/new/wordpress/?page_id=62')
    if r.ok:
        day = datetime.today().weekday()
        soup = BeautifulSoup(r.content, 'html.parser')
        e = [i for i in soup.select('.post-body p') if i.text.strip()]
        return [i.text for i in e[day].select('span') if i.text.strip()]
    return []


def scrap_jarosova():
    r = requests.get('http://vasestravovanie.sk/jedalny-listok-jar/')
    if r.ok:
        day = datetime.today().weekday()
        soup = BeautifulSoup(r.content, 'html.parser')
        a = soup.select('table tbody tr')[9*day:9*day+9]
        return [i.select('span')[2].text for i in a[0:3]] + [i.select('span')[1].text for i in a[3:]]
    return []


def send_to_slack(items):
    message = '*MENU {}*\n'.format(datetime.today())
    for item in items:
        message += '\n\n*{}*\n'.format(item['restaurant'])
        message += '\n'.join(item['menu'])
    if SLACK_HOOK:
        requests.post(SLACK_HOOK, data=json.dumps({'text': message}))


@app.route("/")
def hello():
    if datetime.today().weekday() in range(0, 5):
        send_to_slack([
            {'restaurant': 'Dream\'s', 'menu': scrap_dreams()},
            {'restaurant': 'Breweria', 'menu': scrap_breweria()},
            {'restaurant': 'Bednar', 'menu': scrap_bednar()},
            {'restaurant': 'Jedalen Jarosova', 'menu': scrap_jarosova()},
        ])
        return 'Done '
    else:
        return 'Come on Monday-Friday' + SLACK_HOOK

if __name__ == '__main__':
    app.run()
