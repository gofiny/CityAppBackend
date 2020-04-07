'''Кастомные исключения'''


class UserRegistered(Exception):
    """If user already registered"""


class UserAlreadyExist(Exception):
    '''Вызывается когда пользователь не найден в базе'''


class ObjectNotExist(Exception):
    '''Вызывается если пользователь или объект спауна не найден в базе'''
