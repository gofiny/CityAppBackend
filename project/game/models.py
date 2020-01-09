from django.db import models
from random import randint, shuffle


class Person(models.Model):
    '''Игрок'''
    username = models.CharField(max_length=25, unique=True)
    vk_id = models.IntegerField(unique=True)
    token = models.CharField(max_length=64)

    def __str__(self):
        return f"[{self.vk_id}] {self.username}"


class GameObject(models.Model):
    '''Игровой объект'''
    name = models.CharField(max_length=20)
    health = models.IntegerField(default=0)
    object_type = models.CharField(default=None, null=True, max_length=7)


class StaticObject(GameObject):
    '''Статический игровой объект'''

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.object_type = "static"
        super().save(*args, **kwargs)

    @classmethod
    def get_random_gen_object(self):
        all_obj = list(self.objects.filter(name__contains="gen_"))
        shuffle(all_obj)
        return all_obj[randint(0, len(all_obj) - 1)]


class DynamicObject(GameObject):
    '''Динамический игровой объект'''

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.object_type = "dynamic"
        super().save(*args, **kwargs)


class MapObject(models.Model):
    '''Игровой объект на карте'''
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    owner = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="game_objects", null=True, default=None, blank=True)
    game_object = models.ForeignKey(GameObject, on_delete=models.CASCADE, related_name="on_map")

    def __str__(self):
        return f"X: {self.x} Y: {self.y}"

    @classmethod
    def get_random_object(self):
        '''Возвращает рандомный объект на карте или None'''
        count = self.objects.all().count()
        if count > 0:
            return self.objects.all()[randint(0, count - 1)]
        return None
