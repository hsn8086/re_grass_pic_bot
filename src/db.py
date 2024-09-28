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
@File       : db.py

@Author     : hsn

@Date       : 2024/9/26 下午8:49
"""
from os import PathLike
from pathlib import Path

from tinydb import TinyDB

from src.util import SingletonMeta


class DB(metaclass=SingletonMeta):
    def __init__(self, data_dir: PathLike | str = 'data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.collections = {p.stem: TinyDB(p) for p in self.data_dir.iterdir() if p.is_dir()}

    def add_collection(self, name: str):
        self.collections[name] = TinyDB(self.data_dir / f'{name}.json')

    def __getitem__(self, item) -> TinyDB:
        if item not in self.collections:
            self.add_collection(item)
        return self.collections[item]
