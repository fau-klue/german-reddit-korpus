#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Philipp Heinrich, 2022.

import argparse
import gzip
import html
import re
import os
from glob import glob

import ujson                    # pip3 install ujson
import fasttext                 # pip3 install fasttext

from utils import multi_proc, path2lines


def process_line(comment):

    body = comment['body']

    # weird hex-encoding:
    if re.search(r"&amp;#x", body):
        # TODO: should we also change these comments for all further steps?
        body = html.unescape(body)
        body = html.unescape(body)

    # sanitize text
    body = body.replace('\r', '').replace('\n', ' ')
    body = re.sub(r'\(?http[^ ]+\)?', '', body)

    # don't analyze deleted texts
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

    languages = LANGUAGES
    
    # identify compression
    compression = path_in.split(".")[-1]

    # set paths to output
    drive, tail = os.path.split(path_in)
    path_lang = os.path.join(DIR_OUT, tail.replace("." + compression, "-lang.tsv.gz"))

    # open files for each language
    files_languages = dict()
    for lang in languages:
        tail_lang = tail.replace("." + compression, f"-{lang}.tsv.gz")
        files_languages[lang] = gzip.open(os.path.join(DIR_OUT, tail_lang), "wt")

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
    with gzip.open(path_lang, "wt") as f_lang:

        # header
        f_lang.write(header_line)
        for lang in languages:
            files_languages[lang].write(header_line)

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

            for lang in languages:
                if analysis['language'] == f'__label__{lang}':
                    files_languages[lang].write(data_line)

    for lang in languages:
        files_languages[lang].close()


def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputglob',
                        type=str,
                        help='glob to input files',
                        default="local/raw/comments/*")
    parser.add_argument('--dir_out',
                        type=str,
                        help='where to save the results',
                        default="local/language-scores/comments/")
    parser.add_argument('--lang_model',
                        type=str,
                        help='path to language model used by fasttext [lid.176.bin]',
                        default="lid.176.bin")
    parser.add_argument('--nr_proc',
                        type=int,
                        help='how many processes to spawn [8]',
                        default=8)
    parser.add_argument('--lang',
                        type=str,
                        nargs='+',
                        default=['de'])
    args = parser.parse_args()

    # glob input paths
    paths_in = glob(args.inputglob)

    # output
    global DIR_OUT
    DIR_OUT = args.dir_out
    os.makedirs(DIR_OUT, exist_ok=True)

    # languages
    global LANGUAGES
    LANGUAGES = args.lang

    # load language model
    path_model = args.lang_model
    global MODEL
    MODEL = fasttext.load_model(path_model)

    # process files
    multi_proc(process_file, paths_in, nr_cpus=args.nr_proc)


if __name__ == "__main__":
    main()
