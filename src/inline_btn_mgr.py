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
@File       : inline_btn_mgr.py

@Author     : hsn

@Date       : 2024/9/28 下午1:49
"""
import time
import uuid
from typing import Iterable

from pydantic import BaseModel
from pydantic import Field
from telebot.util import quick_markup
from tinydb import TinyDB

from src.db import DB
from .util import SingletonMeta


class InlineButton(BaseModel):
    name: str
    action: str
    data: dict = {}
    crt_time: int = Field(default_factory=time.time_ns)
    updated_time: int = Field(default_factory=time.time_ns)
    uuid: str = uuid.uuid4().hex


class InlineButtonMgr(metaclass=SingletonMeta):
    def __init__(self, db: TinyDB):
        self.db = db

    def add_button(self, button: InlineButton):
        return self.db.insert(button.dict())

    def create_markup(self, buttons: Iterable[InlineButton]):
        return quick_markup({button.name: {"callback_data": self.add_button(button)} for button in buttons})

    def get_button(self, doc_id: int):
        return InlineButton(**self.db.get(doc_id=doc_id))


ibm = InlineButtonMgr(DB()["inline_btn"])
