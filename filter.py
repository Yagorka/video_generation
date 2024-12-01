from typing import List

from aiogram.filters import BaseFilter
from aiogram.types import Message
import datetime as dt

class IsAdmin(BaseFilter):
    def __init__(self, user_ids: int | List[int]) -> None:
        self.user_ids = user_ids

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.user_ids, int):
            return message.from_user.id == self.user_ids
        return message.from_user.id in self.user_ids

class IsDatetime(BaseFilter):
    def __init__(self, special_symbols_accept: List[str] = []) -> None:
        self.special_symbols_accept = special_symbols_accept

    async def __call__(self, message: Message) -> bool:
        if isinstance(message.text, str):
            try:
                date_norm_format = dt.datetime.strptime(message.text, '%d.%m.%Y')
            except:
                if message.text not in self.special_symbols_accept:
                    return False
        return True

class IsFIO(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        if isinstance(message.text, str):
            parts_names = [i.isalpha() for i in message.text.split()]
            if all(parts_names) and len(parts_names)>=1:
                return True
        return False

class Is_login_and_passsword(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        if isinstance(message.text, str):
            part_email, part_password = message.text.split()
            if len(part_email)>=3 and len(part_password)>=1:
                return True
        return False