#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Philipp Heinrich, 2022.

import argparse
import gzip
import re
from glob import glob

import ujson                    # pip3 install ujson
import fasttext                 # pip3 install fasttext

from utils import multi_proc, path2lines


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


def process_file(path_in):

    # identify compression
    compression = path_in.split(".")[-1]

    # set path to output
    path_lang = path_in.replace("." + compression, "-lang.tsv.gz")
    path_lang_de = path_in.replace("." + compression, "-lang-de.tsv.gz")

    header_line = "\t".join([
        'comment_id',
        'created_utc',
        'link_id',         # thread
        'parent_id',       # actual parent (submission or comment)
        'subreddit',
        'subreddit_id',
        'language',
        'confidence',
        'length'
    ]) + "\n"

    # do the actual processing
    with gzip.open(path_lang, "wt") as f_lang, gzip.open(path_lang_de, "wt") as f_lang_de:

        # header
        f_lang.write(header_line)
        f_lang_de.write(header_line)

        for line in path2lines(path_in):

            comment = ujson.loads(line.strip())
            analysis = process_line(comment)

            data_line = "\t".join([
                comment['id'],
                str(comment['created_utc']),
                comment['link_id'],
                comment['parent_id'],
                comment['subreddit'],
                comment['subreddit_id'],
                analysis['language'],
                analysis['confidence'],
                analysis['length']
            ]) + "\n"

            f_lang.write(data_line)

            if comment['language'] == '__label__de':
                f_lang_de.write(data_line)


def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('inputglob',
                        type=str,
                        help='glob to input files')
    parser.add_argument('--lang_model',
                        type=str,
                        help='path to language model used by fasttext [lid.176.bin]',
                        default="lid.176.bin")
    parser.add_argument('--nr_proc',
                        type=int,
                        help='how many processes to spawn [2]',
                        default=2)
    args = parser.parse_args()

    # glob input paths
    paths_in = glob(args.inputglob)

    # load language model
    path_model = args.lang_model
    global MODEL
    MODEL = fasttext.load_model(path_model)

    # process files
    multi_proc(process_file, paths_in, nr_cpus=args.nr_proc)


if __name__ == "__main__":
    main()
