#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#  Copyright (C) 2024. Suto-Commune
#  _
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  _
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  _
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
@File       : schedules.py

@Author     : hsn

@Date       : 2024/9/28 下午4:05
"""
import re

from feedparser import parse
from httpx import Client
from telebot.async_telebot import AsyncTeleBot
from tinydb import Query

from src.db import DB
from src.telegram.routes.post import ReviewThread
from src.telegram.routes.rss import RSS
from loguru import logger

def _parser(url):
    c = Client(headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})
    r = c.get(url,timeout=10)
    return parse(r)

@logger.catch
async def get_rss(bot: AsyncTeleBot):
    db_rss = DB()["rss"]
    db_rss_dedup = DB()["rss_dedup"]
    db_review_thread = DB()["review_thread"]
    print(1)
    for raw_rss in db_rss.all():
        rss = RSS(**raw_rss)
        # get rss data
        rss_data = _parser(rss.rss_url)
        # regex
        urls = re.findall(rss.url_regex, str(rss_data))
        # check if url is already in db
        for url in urls:
            if db_rss_dedup.contains(Query().url == url):
                continue
            db_rss_dedup.insert({"url": url})

            images = [url]
            rt = ReviewThread(description="", images=images, poster="RSS Scraper")
            groups = []
            for i in DB()["group"].search(Query().permission.review == True):
                groups.append(i["id"])
            for group in groups:
                await rt.display(bot, group)
            db_review_thread.insert(rt.dict())
