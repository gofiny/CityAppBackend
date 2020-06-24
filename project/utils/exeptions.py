class MethodIsNotExist(Exception):
    pass

class ResNotEnough(Exception):
    pass


errors = {
    0: {"errors": [0, "method is not exist"]},
    1: {"errors": [1, "data is not correct"]}
}
