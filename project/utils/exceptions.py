class MethodIsNotExist(Exception):
    pass

class ResNotEnough(Exception):
    pass

class UserExceptions(Exception):
    class GPIDAlreadyExist(Exception):
        pass

    class UsernameAlreadyExist(Exception):
        pass

errors = {
    0: {"errors": [0, "method is not exist"]},
    1: {"errors": [1, "data is not correct"]},
    2: {"errors": [2, "user with this gp_id already exist"]},
    3: {"errors": [3, "user with this username already exist"]},
}
