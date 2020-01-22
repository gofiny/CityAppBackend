from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db.models import Q
from .models import Player, MapObject, StaticObject, DynamicObject, GameObject
import json
import hashlib
import string
import random


def generate_string(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_token(user_id):
    salt = "sFTtzfpkqdSuDxrwTQGLCFZlLofLYG"
    random_string = generate_string()
    finally_string = str(user_id) + salt + random_string
    hash_string = hashlib.sha256(finally_string.encode('utf-8')).hexdigest()
    return hash_string


def get_status(request):
    return HttpResponse("ok, api is working!")


def get_data(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        status = False
        errors = [2, "json is not correct"]
        return JsonResponse({"status": status, "errors": errors})
    return data


def get_token(user_id):
    user = Player.objects.filter(user_id=user_id)
    if user:
        return user.first().token
    return None


def check_token(func):
    def wrapper(request):
        data = get_data(request)
        try:
            user_token = get_token(data["user_id"])
            taken_token = data["token"]
            if user_token == taken_token:
                return func(request)
            errors = [1, "token is not correct"]
        except (ValueError, KeyError):
            errors = [2, "json is not correct"]
        status = False
        return JsonResponse({"status": status, "errors": errors})
    return wrapper


def check_relay(pos):
    min_coord = (pos[0] - 20, pos[1] - 20)
    max_coord = (pos[0] + 20, pos[1] + 20)
    game_object = MapObject.objects.filter(
        Q(Q(Q(x__gte=min_coord[0]) & Q(x__lte=max_coord[0])) & Q(Q(y__gte=min_coord[1]) & Q(y__lte=max_coord[1])))
        ).exclude(game_object__name__icontains="gen_")
    if game_object:
        return False
    return True


def gen_random_pos(pos, min_c=20, max_c=70):
    x = random.choice([random.randint(pos[0] - max_c, pos[0] - min_c), random.randint(pos[0] + min_c, pos[0] + max_c)])
    y = random.choice([random.randint(pos[1] - max_c, pos[1] - min_c), random.randint(pos[1] + min_c, pos[1] + max_c)])
    return (x, y)


def get_free_pos():
    while True:
        random_obj = MapObject.get_random_object()
        if random_obj:
            new_pos = gen_random_pos((random_obj.x, random_obj.y))
            is_exist = MapObject.objects.filter(x=new_pos[0], y=new_pos[1])
            if is_exist:
                continue
            free_relay = check_relay(new_pos)
            if free_relay is False:
                continue
            return new_pos
        return (0, 0)


def create_spawn(owner):
    pos = get_free_pos()
    spawn = StaticObject.objects.get_or_create(name="spawn", health=1000)[0]
    MapObject.objects.create(x=pos[0], y=pos[1], owner=owner, game_object=spawn)
    return pos


def create_pawn(player, pawn_name, pos):
    pawn = DynamicObject.objects.get_or_create(name=pawn_name)[0]
    MapObject.objects.create(x=pos[0], y=pos[1], owner=player, game_object=pawn)


def register_user(request):
    data = get_data(request)
    response = {"status": False}
    try:
        user_id = data["user_id"]
        username = data["username"]
        metadata = data.get("meta_data")

        username_exist = Player.objects.filter(username__iexact=username)
        vkuser_exist = Player.objects.filter(user_id=user_id)

        if username_exist:
            response["errors"] = [3, "username already exist"]
        elif vkuser_exist:
            response["errors"] = [4, "user already registered"]
        else:
            token = generate_token(user_id=user_id)
            player = Player.objects.create(user_id=user_id, username=username, token=token, metadata=str(metadata))
            pos = create_spawn(owner=player)
            create_pawn(player=player, pawn_name="woodcutter", pos=pos)
            response["token"] = token
            response["status"] = True
    except (KeyError, ValueError):
        response["errors"] = [2, "json is not correct"]

    return JsonResponse(response)


def get_map(request):
    '''Возвращает объекты расположенные на карте'''
    data = get_data(request)
    response = {"status": True, "game_objects": None}
    try:
        x = data['coors']['x']
        y = data['coors']['y']
        width = data['scope']['width']
        height = data['scope']['height']

        x_coords = (x - (width // 2), x + (width // 2))
        y_coords = (y - (height // 2), y + (height // 2))

        all_objects = MapObject.objects.filter(Q(Q(Q(x__gte=x_coords[0]) & Q(x__lte=x_coords[1])) & Q(Q(y__gte=y_coords[0]) & Q(y__lte=y_coords[1]))))

        if all_objects:
            game_objects = []
            for map_object in all_objects:
                game_object = {
                    "name": map_object.game_object.name,
                    "uuid": map_object.game_object.uuid,
                    "owner": None if not hasattr(map_object.owner, "user_id") else map_object.owner.user_id,
                    "health": map_object.game_object.health,
                    "type": map_object.game_object.object_type,
                    "coors": {
                        "x": map_object.x,
                        "y": map_object.y
                    }
                }
                game_objects.append(game_object)
            
            response["game_objects"] = game_objects
            #response["count"] = len(all_objects)
    except (KeyError, ValueError):
        response["status"] = False
        response["errors"] = [2, "not correct json"]
    
    return JsonResponse(response)


def gen_objects(request):
    '''Генерирует случайные объекты-ресурсы на карте'''
    counter = 0
    while counter <= 15:
        random_obj = MapObject.get_random_object()
        pos = gen_random_pos(pos=(random_obj.x, random_obj.y), min_c=1)
        is_exist = MapObject.objects.filter(x=pos[0], y=pos[1])
        if is_exist:
            continue
        obj = StaticObject.get_random_gen_object()
        MapObject.objects.create(x=pos[0], y=pos[1], game_object=obj)
        counter += 1

    return HttpResponse(status=200)


@check_token
def get_profile(request):
    response = {"status": True}
    try:
        data = get_data(request)

        user_id = data["user_id"]
        player = Player.objects.get(user_id=user_id)
        spawn_obj = player.game_objects.filter(game_object__name="spawn").get()
        response["username"] = player.username
        response["meta_data"] = player.metadata
        response["spawn"] = {"x": spawn_obj.x, "y": spawn_obj.y}
        response["resources"] = ["Пока пусто"]
    except (KeyError, ValueError, Player.DoesNotExist):
        response["errors"] = ["2", "json is not correct"]
        response["status"] = False

    return JsonResponse(response)

    