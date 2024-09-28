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
@File       : post.py

@Author     : hsn

@Date       : 2024/9/26 下午7:34
"""
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Literal

from loguru import logger
from pydantic import BaseModel
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery
from tinydb import Query

from src.db import DB
from src.inline_btn_mgr import InlineButton
from src.telegram.post_mgr import PostManager


async def post(bot: AsyncTeleBot, message: Message):
    mgr = PostManager()
    mgr.start_post_task(message.from_user.id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("/post_finish")
    markup.add("/post_cancel")
    await bot.reply_to(message, "Please send me the image you want to post.", reply_markup=markup)
    return


async def post_img(bot: AsyncTeleBot, message: Message):
    # if DB()["admin"].get(Query().username == message.from_user.username):
    #     await bot.reply_to(message, "You are not admin.")
    #     return
    mgr = PostManager()
    if message.from_user.id not in mgr.tasks:
        return
    if mgr.add_img(message.from_user.id, message.photo[-1].file_id):
        await bot.reply_to(message, "got it.")
    else:
        await bot.reply_to(message, "You have already uploaded 4 images.")
    return


async def set_post_description(bot: AsyncTeleBot, message: Message):
    mgr = PostManager()
    if message.from_user.id not in mgr.tasks:
        return
    mgr.add_description(message.from_user.id, message.text)
    await bot.reply_to(message, "Description set.")
    return


def geb_review_btn(post_id):
    return InlineButton(name="Approve", action="post_review", data={"post_uuid": post_id, "status": "approve"}), \
        InlineButton(name="Reject", action="post_review", data={"post_uuid": post_id, "status": "reject"})


class ReviewMsg(BaseModel):
    group_id: int
    message_id: int
    type: Literal["img", "review_info", "meta"]


from ...inline_btn_mgr import ibm
from pydantic import Field
import telebot.asyncio_helper


class ReviewThread(BaseModel):
    description: str
    poster: str
    images: list[str]
    review_count: dict[int, dict[str, list[str]]] = {}
    post_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    msgs: list[ReviewMsg] = []
    btns: list[InlineButton] = []

    async def display(self, bot: AsyncTeleBot, group_id: int):
        try:
            for i in self.images:
                message = await bot.send_photo(group_id, i)
                self.msgs.append(ReviewMsg(group_id=group_id, message_id=message.message_id, type="img"))
            message = await bot.send_message(group_id, f"0% | Approve: 0\n0% | Reject: 0")
            self.msgs.append(ReviewMsg(group_id=group_id, message_id=message.message_id, type="review_info"))
            message = await bot.send_message(
                chat_id=group_id,
                text=f"Description: {self.description}\nPoster: @{self.poster}\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                reply_markup=ibm.create_markup(geb_review_btn(self.post_id)))
            self.msgs.append(ReviewMsg(group_id=group_id, message_id=message.message_id, type="meta"))
        except telebot.asyncio_helper.ApiTelegramException:
            await self.delete(bot)

    async def change_review_info(self, bot: AsyncTeleBot, group_id: int, uname: str,
                                 status: Literal["approve", "reject"], *, threshold: float | None = None):
        if group_id not in self.review_count:
            self.review_count[group_id] = {"approve": [], "reject": []}
        if status == "approve":
            if self.review_count[group_id]["reject"]:
                self.review_count[group_id]["reject"].remove(uname)
            if uname not in self.review_count[group_id]["approve"]:
                self.review_count[group_id]["approve"].append(uname)
            else:
                return
        else:
            if self.review_count[group_id]["approve"]:
                self.review_count[group_id]["approve"].remove(uname)
            if uname not in self.review_count[group_id]["reject"]:
                self.review_count[group_id]["reject"].append(uname)
            else:
                return

        for i, m in enumerate(self.msgs):
            if m.group_id == group_id and m.type == "review_info":
                count_of_approve = len(self.review_count[group_id]["approve"])
                count_of_reject = len(self.review_count[group_id]["reject"])
                member_count = (await bot.get_chat_member_count(group_id)) - 1
                at_text = "" if threshold is None else f"/{threshold * 100}%"
                rt_text = "" if threshold is None else f"/{(1 - threshold) * 100}%"
                await bot.edit_message_text(
                    f"{count_of_approve / member_count * 100}%{at_text} | Approve: {count_of_approve}\n"
                    f"{count_of_reject / member_count * 100}%{rt_text} | Reject: {count_of_reject}\n"
                    f"Update time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    group_id, m.message_id)

        # if repl_msg:
        #     print(1)
        #     self.msgs[repl_id] = ReviewMsg(group_id=group_id, message_id=repl_msg.message_id, type="review_info")

    async def delete(self, bot: AsyncTeleBot):
        del_dict = {}
        for i in self.msgs:
            if i.group_id not in del_dict:
                del_dict[i.group_id] = []
            del_dict[i.group_id].append(i.message_id)
        for k, v in del_dict.items():
            await bot.delete_messages(k, v)
        self.msgs.clear()
        return


@logger.catch
async def finish(bot: AsyncTeleBot, message: Message):
    mgr = PostManager()
    if not mgr.check_user_task(message.from_user.id):
        await bot.reply_to(message, "You have no post task.")
        return
    await bot.reply_to(message, "Post task finished.", reply_markup=ReplyKeyboardRemove())
    # get all group has permission to receive post
    groups = []
    for i in DB()["group"].search(Query().permission.review == True):
        groups.append(i["id"])
    task = mgr.pop_task(message.from_user.id)

    db_review_thread = DB()["review_thread"]
    rt = ReviewThread(description=task["description"], images=task["images"], poster=message.from_user.username)
    for group in groups:
        await rt.display(bot, group)
    db_review_thread.insert(rt.dict())


#
# @logger.catch
# async def finish2(bot: AsyncTeleBot, message: Message):
#     mgr = PostManager()
#     if mgr.check_user_task(message.from_user.id):
#         await bot.reply_to(message, "Post task finished.", reply_markup=ReplyKeyboardRemove())
#         # get all group has permission to receive post
#         groups = []
#         for i in DB()["group"].search(Query().permission.review == True):
#             groups.append(i["id"])
#
#         task = mgr.pop_task(message.from_user.id)
#         now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#         post_id = uuid.uuid4().hex
#         db_post = DB()["post_review_msg"]
#         db_inline_btn = DB()["inline_btn"]
#         pre_insert = []
#         for group in groups:
#             for img in task["images"]:
#                 pre_insert.append((group, (await bot.send_photo(group, img)).id, "img"))
#             approve_btn, reject_btn = geb_review_btn(post_id)
#             approve_btn_id = db_inline_btn.insert(approve_btn)
#             reject_btn_id = db_inline_btn.insert(reject_btn)
#             markup = quick_markup({
#                 'Approve': {"callback_data": str(approve_btn_id)},
#                 'Reject': {"callback_data": str(reject_btn_id)},
#             })
#             mid = (await bot.send_message(group, "0% | Approve: 0\n0% | Reject: 0")).id
#             pre_insert.append((group, mid, "review_info"))
#             mid = (
#                 await bot.send_message(
#                     chat_id=group,
#                     text=f"""
# \bDescription: {task['description']}
# Poster: @{message.from_user.username}
# Time: {now_time}""",
#                     reply_markup=markup)
#             ).id
#             pre_insert.append((group, mid, "meta"))
#
#         for i in pre_insert:
#             db_post.insert({
#                 "group": i[0],
#                 "message_id": i[1],
#                 "message_type": i[2],
#                 "post_uuid": post_id,
#             })
#         de_review = DB()["post_review"]
#         de_review.insert({
#             "post_uuid": post_id,
#             "status": "pending",
#             "created_at": time.time_ns(),
#             "updated_at": time.time_ns(),
#             "images": task["images"],
#             "description": task["description"],
#             "review_count": {},
#         })
#         return
#     else:
#         await bot.reply_to(message, "You have no post task.")
#         return


async def cancel(bot: AsyncTeleBot, message: Message):
    mgr = PostManager()
    if mgr.check_user_task(message.from_user.id):
        mgr.cancel_post_task(message.from_user.id)
        await bot.reply_to(message, "Post task cancelled.", reply_markup=ReplyKeyboardRemove())
        return
    else:
        await bot.reply_to(message, "You have no post task.")
        return


# @logger.catch
# async def post_review_callback(bot: AsyncTeleBot, call: CallbackQuery):
#     data = ibm.get_button(int(call.data)).data
#     db = DB()["post_review_msg"]
#     db_review = DB()["post_review"]
#     review_data = db_review.get(Query().post_uuid == data["post_uuid"])
#     review_count = review_data["review_count"]
#     if call.message.chat.id not in review_count:
#         review_count[call.message.chat.id] = {"approve": [], "reject": []}
#     if data["status"] == "approve":
#         if review_count[call.message.chat.id]["reject"]:
#             review_count[call.message.chat.id]["reject"].remove(call.from_user.username)
#         review_count[call.message.chat.id]["approve"].append(call.from_user.username)
#     else:
#         if review_count[call.message.chat.id]["approve"]:
#             review_count[call.message.chat.id]["approve"].remove(call.from_user.username)
#         review_count[call.message.chat.id]["reject"].append(call.from_user.username)
#     rt_raw = DB()["review_thread"].get(Query().post_id == data["post_uuid"])
#     db_review.update({"review_count": review_count}, Query().post_uuid == data["post_uuid"])
#     threshold = DB()["group"].get(Query().id == call.message.chat.id)["permission"]["review_pass_percent"]["value"]
#     count_of_approve = len(review_count[call.message.chat.id]["approve"])
#     count_of_reject = len(review_count[call.message.chat.id]["reject"])
#     member_count = await bot.get_chat_member_count(call.message.chat.id)
#     await bot.edit_message_text(
#         f"{count_of_approve / member_count * 100}%/{threshold * 100}% | Approve: {count_of_approve}\n"
#         f"{count_of_reject / member_count * 100}%{(1 - threshold) * 100}%  | Reject: {count_of_reject}",
#         call.message.chat.id, mid)
#     if count_of_approve / member_count >= threshold or count_of_reject / member_count > 1 - threshold:
#         del_dict = {}
#         for i in db.search(Query().post_uuid == data["post_uuid"]):
#             group_id = i["group"]
#             message_id = i["message_id"]
#             if group_id not in del_dict:
#                 del_dict[group_id] = []
#             del_dict[group_id].append(message_id)
#         for group_id in del_dict:
#             await bot.delete_messages(group_id, del_dict[group_id])
#         db.remove(Query().post_uuid == data["post_uuid"])
#     await bot.answer_callback_query(call.id, "Done.")
#     # post
#     # get img
#     tmp_dir = Path("temp")
#     tmp_dir.mkdir(exist_ok=True)
#     file_paths = []
#     for i in review_data["images"]:
#         f_path = (await bot.get_file(i)).file_path
#         ba = await bot.download_file(f_path)
#         image = Image.open(BytesIO(ba))
#         image.thumbnail((1024, 1024))
#         fp = tmp_dir / (uuid.uuid4().hex + ".jpg")
#         image.save(fp, quality=80)
#         file_paths.append(fp)
#     from ...twi import account
#     account.tweet(review_data["description"], media=[{"media": i} for i in file_paths])
#     return
import httpx


@logger.catch
async def post_review_callback(bot: AsyncTeleBot, call: CallbackQuery):
    # get button data
    button_data = ibm.get_button(int(call.data)).data
    post_uuid = button_data["post_uuid"]
    # init db
    db_review = DB()["review_thread"]
    # get review thread
    rt = ReviewThread(**db_review.get(Query().post_id == post_uuid))
    # get threshold of group
    threshold = DB()["group"].get(Query().id == call.message.chat.id)["permission"]["review_pass_percent"]["value"]

    await rt.change_review_info(bot, call.message.chat.id, call.from_user.username, button_data["status"],
                                threshold=threshold)
    await bot.answer_callback_query(call.id, "Done.")
    db_review.update(rt.dict(), Query().post_id == post_uuid)

    # check if post should be deleted
    member_count = (await bot.get_chat_member_count(call.message.chat.id)) - 1
    count_of_approve = len(rt.review_count[call.message.chat.id]["approve"])
    count_of_reject = len(rt.review_count[call.message.chat.id]["reject"])

    from PIL import Image
    if count_of_approve / member_count >= threshold:
        # post
        tmp_dir = Path("temp")
        tmp_dir.mkdir(exist_ok=True)
        file_paths = []
        for i in rt.images:
            if not i.startswith("http"):
                f_path = (await bot.get_file(i)).file_path
                ba = await bot.download_file(f_path)
            else:
                c = httpx.Client(headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})
                resp=c.get(i)
                if resp.status_code!=200:
                    break
                ba = resp.read()
            image = Image.open(BytesIO(ba))
            image.thumbnail((1024, 1024))
            fp = tmp_dir / (uuid.uuid4().hex + ".jpg")
            image.save(fp, quality=80)
            file_paths.append(fp)
        else:
            from ...twi import account
            account.tweet(rt.description, media=[{"media": i} for i in file_paths])


    if count_of_approve / member_count >= threshold or count_of_reject / member_count > 1 - threshold:
        await rt.delete(bot)
        db_review.remove(Query().post_id == post_uuid)
