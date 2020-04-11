'''Кастомные исключения'''


class UserRegistered(Exception):
    """If user already registered"""


class UserAlreadyExist(Exception):
    '''Вызывается когда пользователь не найден в базе'''


class ObjectNotExist(Exception):
    '''Вызывается если пользователь или объект спауна не найден в базе'''


class NotValidTask(Exception):
    """If not correct data for to add task to pawn"""


class PawnLimit(Exception):
    """If pawn has limit tasks count"""
