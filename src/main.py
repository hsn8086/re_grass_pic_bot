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
@File       : main.py

@Author     : hsn

@Date       : 2024/9/26 下午7:16
"""
import asyncio
import shutil
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import Callable

import schedule
from loguru import logger
from telebot.async_telebot import AsyncTeleBot
from tinydb import Query

from src.config import Config
from src.db import DB
from src.telegram.post_mgr import PostManager
from src.telegram.routes.admin import set_admin, remove_admin
from src.telegram.routes.group import set_group_permission, set_group_permissions, get_group_permissions, \
    set_group_permissions_finish
from src.telegram.routes.post import post, post_img, finish, cancel, set_post_description, post_review_callback
from src.telegram.routes.rss import add_rss_source
from src.telegram.routes.start import start
from src.schedules import get_rss

def handle_builder(bot: AsyncTeleBot):
    def _add_handler(handler_type: Callable, handler: Callable, **kwargs):
        # @bot.message_handler(**kwargs)
        @handler_type(**kwargs)
        async def _handler(*args, **_kwargs):
            await handler(bot, *args, **_kwargs)

    return _add_handler




@logger.catch
async def main():
    logger.add("logs/{time}.log", rotation="1 week")
    logger.info("Starting bot...")
    parser = ArgumentParser(prog="Grass Pic Bot",
                            description="A bot that posts grass pictures to Twitter.",
                            epilog="Made by hsn8086.")
    parser.add_argument("-c", "--config", help="The path to the config file.", type=str, default="config.toml")
    if (p := Path("temp")).exists():
        shutil.rmtree(p)
    config_path = Path(parser.parse_args().config)
    if config_path.exists():
        config = Config(config_path).config
    else:
        raise FileNotFoundError(f"Config file {config_path} not found.")
    for uname in config.get("telegram").get("admin"):
        if DB()["admin"].count(Query().username == uname) == 0:
            DB()['admin'].insert({
                "username": uname,
                "created_at": time.time_ns(),
                "updated_at": time.time_ns(),
            })
    cookies = config.get("twitter").get("cookies")
    token = config.get("telegram").get("token")
    bot = AsyncTeleBot(token=token)

    add_handler = handle_builder(bot)

    add_handler(bot.message_handler, start, commands=["start"])

    add_handler(bot.message_handler, post, commands=["post"])
    add_handler(bot.message_handler, finish, commands=["post_finish"])
    add_handler(bot.message_handler, cancel, commands=["post_cancel"])
    add_handler(bot.message_handler, post_img, func=lambda message: True, content_types=['photo'])
    add_handler(bot.message_handler, set_post_description,
                func=lambda message: message.from_user.id in PostManager().tasks, content_types=['text'])
    add_handler(bot.callback_query_handler, post_review_callback,
                func=lambda call: (DB()["inline_btn"].get(doc_id=int(call.data)))["action"] == "post_review")

    add_handler(bot.message_handler, set_admin, commands=["set_admin"])
    add_handler(bot.message_handler, remove_admin, commands=["remove_admin"])

    add_handler(bot.message_handler, set_group_permissions, commands=["set_group_permissions"])
    add_handler(bot.message_handler, set_group_permission, commands=["set_group_permission"])
    add_handler(bot.message_handler, set_group_permissions_finish, commands=["set_group_permissions_finish"])
    add_handler(bot.message_handler, get_group_permissions, commands=["get_group_permissions"])

    add_handler(bot.message_handler, add_rss_source, commands=["add_rss_source"])
    #await get_rss(bot)
    schedule.every(30).minutes.do(lambda: asyncio.create_task(get_rss(bot)))

    async def schedule_runner():
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

    try:
        logger.info("Bot started.")
        asyncio.create_task(schedule_runner())
        print(2)
        await bot.infinity_polling()

    finally:
        await bot.close()
        logger.info("Bot closed.")
        return
