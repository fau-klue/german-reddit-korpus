import gzip
import ujson

from utils_markdown import process_thread
from timeit import default_timer
from functools import wraps


def time_it(func):
    """
    decorator for printing the execution time of a function call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = default_timer()
        result = func(*args, **kwargs)
        end = default_timer()
        print("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return result
    return wrapper


@time_it
def test_1000(path_in):

    with gzip.open(path_in, "rt") as f:
        for i, line in enumerate(f):
            thread = ujson.loads(line)
            xml_str, meta = process_thread(thread)

            if i == 1000:
                break


if __name__ == '__main__':

    path_in = "../local/data/gerede-2015-08.ldjson.gz"
    test_1000(path_in)
