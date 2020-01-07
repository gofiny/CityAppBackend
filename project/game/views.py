from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db.models import Q
from .models import Person, MapObject
import json
import hashlib
import string
import random


def generate_string(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_token(vk_id):
    salt = "sFTtzfpkqdSuDxrwTQGLCFZlLofLYG"
    random_string = generate_string()
    finally_string = str(vk_id) + salt + random_string
    hash_string = hashlib.sha256(finally_string.encode('utf-8')).hexdigest()
    return hash_string


def get_status(request):
    return HttpResponse("ok, api is working!")


def get_data(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        status = False
        errors = [2, "not correct json"]
        return JsonResponse({"status": status, "errors": errors})
    return data


def get_token(vk_id):
    user = Person.objects.filter(vk_id=vk_id)
    if user:
        return user.first().token
    return None


def check_token(func):
    def wrapper(request):
        data = get_data(request)
        user_token = get_token(data.get("vk_id", None))
        taken_token = data.get("token", None)
        if user_token == taken_token:
            return func(request)
        status = False
        errors = [1, "token not correct"]
        return JsonResponse({"status": status, "errors": errors})
    return wrapper


def register_user(request):
    data = get_data(request)
    vk_id = data.get("vk_id", None)
    username = data.get("username", None)
    response = {"status": False}

    try:
        username_exist = Person.objects.filter(username__iexact=username)
        vkuser_exist = Person.objects.filter(vk_id=vk_id)

        if (not vk_id) or (not username):
            response["errors"] = [0, "more data required"]
        elif username_exist:
            response["errors"] = [3, "username already exist"]
        elif vkuser_exist:
            response["errors"] = [4, "user already registered"]
        else:
            token = generate_token(vk_id=vk_id)
            Person.objects.create(vk_id=vk_id, username=username, token=token)
            response["token"] = token
            response["status"] = True
    except (KeyError, ValueError):
        response["errors"] = [2, "not correct json"]

    return JsonResponse(response)


def get_map(request):
    data = get_data(request)
    response = {"status": True, "game_objects": None}
    try:
        x = data['coords'][0]
        y = data['coords'][1]
        width = data['scope'][0]
        height = data['scope'][1]

        x_coords = (x - (width // 2), x + (width // 2))
        y_coords = (y - (height // 2), y + (height // 2))

        all_objects = MapObject.objects.filter(Q(Q(Q(x__gte=x_coords[0]) & Q(x__lte=x_coords[1])) & Q(Q(y__gte=y_coords[0]) & Q(y__lte=y_coords[1]))))

        if all_objects:
            game_objects = []
            for map_object in all_objects:
                game_object = {
                    "name": map_object.game_object.name,
                    "health": map_object.game_object.health,
                    "type": map_object.game_object.object_type,
                    "coords": {
                        "x": map_object.x,
                        "y": map_object.y
                    }
                }
                game_objects.append(game_object)
            
            response["game_objects"] = game_objects
    except (KeyError, ValueError):
        response["status"] = False
        response["errors"] = [2, "not correct json"]
    
    return JsonResponse(response)
