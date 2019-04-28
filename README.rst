=============
infinit-lunch
=============

Online: https://infinit-lunch.herokuapp.com

Simple script for scrapping lunch menus from restaurants around Infinit.sk

When secret_key is provided in url, menu is send to our Slack channel.

Cronjob is run every day at 10:00 thanks to https://cron-job.org

Deploy to heroku: just push to branch **master**


Development
===========

Project is based on `asyncio` and `aiohttp`. Minimal version of Python is 3.5.

Requirements are handled with `pipenv` and 'Pipfile'.
