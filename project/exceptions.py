'''Кастомные исключения'''


class UserAlreadyExist(Exception):
    '''Вызывается когда пользователь не найден в базе'''


class UserOrSpawnNotExist(Exception):
    '''Вызывается если пользователь или объект спауна не найден в базе'''


class DeadEnd(Exception):
    '''Если система просчета пути попала в тупик'''
