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
@File       : rss.py

@Author     : hsn

@Date       : 2024/9/28 下午3:59
"""
import time

from pydantic import BaseModel
from pydantic import Field
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from tinydb import Query

from src.db import DB


class RSS(BaseModel):
    rss_url: str
    url_regex: str
    created_at: int = Field(default_factory=time.time_ns)
    updated_at: int = Field(default_factory=time.time_ns)


async def add_rss_source(bot: AsyncTeleBot, message: Message):
    # check if user is admin
    from_user = message.from_user.username
    if not DB()["admin"].contains(Query().username == from_user):
        await bot.reply_to(message, "You are not admin")
        return
    message_text = message.text
    args = message_text.split(" ")[1:]
    if len(args) != 2:
        await bot.reply_to(message, "Invalid args")
        return
    rss_url, url_regex = args
    db_rss = DB()["rss"]
    if db_rss.search(Query().rss_url == rss_url):
        await bot.reply_to(message, "RSS already exists")
        return
    db_rss.insert(RSS(rss_url=rss_url, url_regex=url_regex).dict())
    await bot.reply_to(message, "RSS added")
