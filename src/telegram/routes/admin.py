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
@File       : admin.py

@Author     : hsn

@Date       : 2024/9/26 下午8:42
"""
import time

from loguru import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from ...config import Config
from ...db import DB


@logger.catch
async def set_admin(bot: AsyncTeleBot, message: Message):
    from_user = message.from_user.username
    if from_user not in Config().config["telegram"]["admin"]:
        await bot.reply_to(message, "You are not admin")
        return
    if not message.reply_to_message:
        await bot.reply_to(message, "Reply to a message")
        return
    uname = message.reply_to_message.from_user.username
    DB()["admin"].insert({
        "username": uname,
        "created_at": time.time_ns(),
        "updated_at": time.time_ns(),
    })


async def remove_admin(bot: AsyncTeleBot, message: Message):
    from_user = message.from_user.username
    if from_user not in Config().config["telegram"]["admin"]:
        await bot.reply_to(message, "You are not admin")
        return
    if not message.reply_to_message:
        await bot.reply_to(message, "Reply to a message")
        return
    uname = message.reply_to_message.from_user.username
    DB()["admin"].delete({"username": uname})
