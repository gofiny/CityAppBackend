import uuid
from time import time


if __name__ == "__main__":
    start = time()
    for _ in range(0, 10000):
        uuid.uuid4()
    print(time() - start)