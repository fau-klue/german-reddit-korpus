import fasttext
import gzip
import re
import ujson
# from utils import spell_check
# import langid
from pandas import read_csv
from functools import wraps
from timeit import default_timer


print("loading")
MODEL = fasttext.load_model("/home/ausgerechnet/corpora/models/lid.176.bin")


def time_it(func):
    """
    decorator for printing the execution time of a function call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = default_timer()
        result = func(*args, **kwargs)
        end = default_timer()
        name = func.__name__
        print("%s took %s seconds" % (name, round(end - start, 2)))
        return result
    return wrapper


def preprocess(text):

    text = text.split("<comment>")
    text = [t.strip() for t in text]
    return text


# def lang_old(text):

#     german = False
#     # first test: spell-checking
#     potentially_german = spell_check(text)

#     # second test: language classification
#     if potentially_german:
#         langid_response = langid.classify(text)
#         if langid_response[0] == 'de':
#             german = True

#     return german


def lang_new(text, model):

    result = model.predict(text)
    return result[0][0] == "__label__de"


# def lang_detect_old(texts):
#     results = list()
#     for text in texts:
#         results.append(lang_old(text))
#     return sum(results) / len(results)


def lang_detect_new(texts):
    results = list()
    for text in texts:
        results.append(lang_new(text, MODEL))
    return sum(results) / len(results)


def test_old_ones(path_in="../local/data/threads-lang-sample-annotated.tsv.gz",
                  path_out="../local/test-lang-ident-results-2.tsv"):

    texts = read_csv(
        "/home/ausgerechnet/repositories/german-reddit-korpus/local/data/threads-lang-sample-annotated.tsv.gz",
        sep="\t"
    )

    print("preprocessing")
    texts['texts'] = texts['comments'].apply(preprocess)

    # print("old pipeline")
    # texts['lang_old'] = texts['texts'].apply(lang_detect_old)

    print("new pipeline")
    texts['lang_new'] = texts['texts'].apply(lang_detect_new)

    texts.to_csv(path_out, sep="\t")


def process_line(comment):

    # sanitize text
    body = comment['body'].replace('\r', '').replace('\n', ' ')
    body = re.sub(r'\(?http[^ ]+\)?', '', body)

    # don't analyze very short or deleted texts
    if body == '[deleted]' or body == '[removed]':
        lang = ""
        confidence = ""
        length = ""

    # analysis
    else:
        result = MODEL.predict(body)
        lang = result[0][0]
        confidence = str(result[1][0])
        length = str(len(body))

    return {
        'language': lang,
        'confidence': confidence,
        'length': length
    }


def test_korean(path_in="../local/data/gerede-2015-07.ldjson.gz",
                path_out="../local/data/korean-thread.json"):

    with gzip.open(path_in, "rt") as f:
        for line in f:
            thread = ujson.loads(line)
            if thread[0]['id'] == '3d3yvm':
                res = process_line(thread[1])
                with open(path_out, "wt") as f_out:
                    f_out.write(line)


if __name__ == '__main__':
    # test_old_ones()
    test_korean()
