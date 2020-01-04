from django.db import models


class Model(models.Model):
    '''Базовая модель, с кастомной id'''
    id = models.IntegerField(unique=True, primary_key=True)

    def __str__(self):
        return str(self.id)


class Person(Model):
    '''Игрок'''
    username = models.CharField(max_length=25, unique=True)
    vk_id = models.IntegerField(unique=True)

    def __str__(self):
        return f"[{self.vk_id}] {self.username}"


class GameObject(Model):
    '''Игровой объект'''
    name = models.CharField(max_length=20)
    health = models.IntegerField(default=0)


class StaticObject(GameObject):
    '''Статический игровой объект'''
    object_type = models.CharField(default="static", max_length=7)

    def __str__(self):
        return f"{self.name}"


class DynamicObject(GameObject):
    '''Динамический игровой объект'''
    object_type = models.CharField(default="dynamic", max_length=7)

    def __str__(self):
        return f"{self.name}"


class MapObject(Model):
    '''Игровой объект на карте'''
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    game_object = models.ForeignKey(GameObject, on_delete=models.CASCADE, related_name="on_map")

    def __str__(self):
        return f"X: {self.x} Y: {self.y}"
