=============
infinit-lunch
=============

Online: https://infinit-lunch.herokuapp.com

Simple script for scrapping lunch menus from restaurants around Infinit.sk

When secret_key is provided in url, menu is send to our Slack channel.

Cronjob runs every day at 10:00 thanks to https://cron-job.org

Deploy to heroku: just push to branch **master**


Development
===========

Project is based on `asyncio` and `aiohttp`.

Requirements are handled with `pip-tools`.
