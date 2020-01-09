import random
import string
import hashlib
from time import time


def generate_string(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_token(vk_id):
    salt = "sFTtzfpkqdSuDxrwTQGLCFZlLofLYG"
    random_string = generate_string()
    finally_string = str(vk_id) + salt + random_string
    hash_string = hashlib.sha256(finally_string.encode('utf-8')).hexdigest()
    return hash_string


if __name__ == "__main__":
    start = time()
    for _ in range(0, 10000):
        generate_token(21142152)
    print(time() - start)