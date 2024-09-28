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
@File       : group.py

@Author     : hsn

@Date       : 2024/9/26 下午9:22
"""
import time
import typing

from loguru import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from tinydb import Query

from ...config import Config
from ...db import DB


@logger.catch
async def set_group_permissions(bot: AsyncTeleBot, message: Message):
    #check if the chat is group
    if message.chat.type not in ["group", "supergroup"]:
        await bot.reply_to(message, "This command is only for groups.")
        return

    default_permission: dict = Config().config["telegram"]["group"]["default-permission"]

    # check if the user is admin
    if DB()["admin"].count(Query().username == message.from_user.username) == 0:
        await bot.reply_to(message, "You are not admin.")
        return
    # try to get group permission
    group = Query()
    for i in DB()["group"].search(group.id == message.chat.id):
        group_permission:dict = i["permission"]
        default_permission.update(group_permission)
        group_permission = default_permission
        break
    else:
        # set default permission
        DB()["group"].insert({
            "id": message.chat.id,
            "permission": default_permission,
            "created_at": time.time_ns(),
            "updated_at": time.time_ns(),
        })
        group_permission = default_permission

    markup = ReplyKeyboardMarkup()
    for k, v in group_permission.items():
        markup.add(f"/set_group_permission {k}")
    markup.add("/set_group_permissions_finish")
    await bot.reply_to(message, "Setting group permission.", reply_markup=markup)
    return


async def set_group_permission(bot: AsyncTeleBot, message: Message):
    default_permission: dict = Config().config["telegram"]["group"]["default-permission"]
    if message.chat.type not in ["group", "supergroup"]:
        await bot.reply_to(message, "This command is only for groups.")
        return
    # check if the user is admin
    if DB()["admin"].count(Query().username == message.from_user.username) == 0:
        await bot.reply_to(message, "You are not admin.")
        return
    # try to get group permission
    group = Query()
    for i in DB()["group"].search(group.id == message.chat.id):
        group_permission = i["permission"]
        default_permission.update(group_permission)
        group_permission = default_permission
        break
    else:
        # set default permission
        DB()["group"].insert({
            "id": message.chat.id,
            "permission": default_permission,
            "created_at": time.time_ns(),
            "updated_at": time.time_ns(),
        })
        group_permission = default_permission
    if len(s := message.text.split(" ")) != 2:
        await bot.reply_to(message, "Invalid command.")
        return
    # update permission
    permission = s[1]
    if permission not in group_permission:
        await bot.reply_to(message, "Invalid permission.")
        return
    else:
        if isinstance(group_permission[permission], bool):
            group_permission[permission] = not group_permission[permission]
        elif isinstance(group_permission[permission], dict):
            match group_permission[permission]["type"]:
                case "bool":
                    group_permission[permission] = not group_permission[permission]
                case "literal":
                    if group_permission[permission]["value"] == group_permission[permission]["literal"][-1]:
                        group_permission[permission]["value"] = group_permission[permission]["literal"][0]
                    else:
                        group_permission[permission]["value"] = group_permission[permission]["literal"][
                            group_permission[permission]["literal"].index(group_permission[permission]["value"]) + 1]
        DB()["group"].update({"permission": group_permission, "updated_at": time.time_ns()}, Query().id == message.chat.id)
    display = group_permission[permission]
    if isinstance(display, dict):
        display = display["value"]
    await bot.reply_to(message, f"Permission {permission} set to {display}")
    return


async def get_group_permissions(bot: AsyncTeleBot, message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await bot.reply_to(message, "This command is only for groups.")
        return
    default_permission: dict = Config().config["telegram"]["group"]["default-permission"]
    # try to get group permission
    group = Query()
    for i in DB()["group"].search(group.id == message.chat.id):
        group_permission = i["permission"]
        break
    else:
        # set default permission
        DB()["group"].insert({
            "id": message.chat.id,
            "permission": default_permission,
            "created_at": time.time_ns(),
            "updated_at": time.time_ns(),
        })
        group_permission = default_permission
    oup = ""
    for k, v in group_permission.items():
        oup += f"{k}: {v}\n"
    await bot.reply_to(message, oup)


async def set_group_permissions_finish(bot: AsyncTeleBot, message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await bot.reply_to(message, "This command is only for groups.")
        return
    await bot.reply_to(message, "Group permission setting finished.", reply_markup=ReplyKeyboardRemove())
    return
