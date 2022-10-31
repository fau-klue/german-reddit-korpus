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

# COMMENT

# 'author': 'mklink',
# 'author_flair_css_class': None,
# 'author_flair_text': None,
# 'body': 'Pollmer wie immer: lebensprall und komisch. Siehe auch: «Diäten machen dick. Und krank» http://www.weltwoche.ch/artikel/?AssetID=9161&amp;CategoryID=62\r\n',
# 'controversiality': 0,
# 'created_utc': 1140455406,
# 'distinguished': None,
# 'edited': False,
# 'gilded': 0,
# 'id': 'c22xm',
# 'link_id': 't3_22xj',
# 'parent_id': 't3_22xj',
# 'retrieved_on': 1473821440,
# 'score': 3,
# 'stickied': False,
# 'subreddit': 'de',
# 'subreddit_id': 't5_22i0',
# 'ups': 3

# SUBMISSION

# 'archived': True,
# 'author': 'mklink',
# 'author_flair_background_color': None,
# 'author_flair_css_class': None,
# 'author_flair_richtext': [],
# 'author_flair_text': None,
# 'author_flair_text_color': None,
# 'author_flair_type': 'text',
# 'brand_safe': True,
# 'can_gild': True,
# 'contest_mode': False,
# 'created_utc': 1140456029,
# 'distinguished': None,
# 'domain': 'medizin.de',
# 'edited': False,
# 'gilded': 0,
# 'hidden': False,
# 'hide_score': False,
# 'id': '22xw',
# 'is_crosspostable': True,
# 'is_reddit_media_domain': False,
# 'is_self': False,
# 'is_video': False,
# 'link_flair_css_class': None,
# 'link_flair_richtext': [],
# 'link_flair_text': None,
# 'link_flair_text_color': 'dark',
# 'link_flair_type': 'text',
# 'locked': False,
# 'media': None,
# 'media_embed': {},
# 'no_follow': True,
# 'num_comments': 1,
# 'num_crossposts': 0,
# 'over_18': False,
# 'parent_whitelist_status': 'all_ads',
# 'permalink': '/r/de/comments/22xw/thema_vogelgrippe_adaptiert_sich_influenza_h5n1/',
# 'rte_mode': 'markdown',
# 'score': 7,
# 'secure_media': None,
# 'secure_media_embed': {},
# 'selftext': '',
# 'send_replies': True,
# 'spoiler': False,
# 'stickied': False,
# 'subreddit': 'de',
# 'subreddit_id': 't5_22i0',
# 'subreddit_name_prefixed': 'r/de',
# 'subreddit_type': 'public',
# 'suggested_sort': None,
# 'thumbnail': 'default',
# 'thumbnail_height': None,
# 'thumbnail_width': None,
# 'title': 'Thema Vogelgrippe: Adaptiert sich Influenza H5N1 an den Menschen?',
# 'url': 'http://www.medizin.de/gesundheit/deutsch/2391.htm',
# 'whitelist_status': 'all_ads'


def process_line(line):

    # comments have link_ids
    post = ujson.loads(line.strip())
    if 'link_id' in post.keys():
        id = post['id']
        link_id = post['link_id']
        parent_id = post['parent_id']
        body = post['body']
    else:
        id = post['id']
        link_id = ''
        parent_id = ''
        body = post['title']
        if 'selftext' in post.keys() and post['selftext'] != '':
            body = body + "\n" + post['selftext']

    subreddit = post.get('subreddit', "")  # some submissions don't have a subreddit
    subreddit_id = post.get('subreddit_id', "")  # some submissions don't have a subreddit
    is_promoted = str(post.get('promoted', ""))  # apparently all the promoted stuff
    created_utc = str(post['created_utc'])

    # sanitise text
    if re.search(r"&amp;#x", body):   # fix weird hex-encoding
        # TODO: should we also change these comments for all further steps?
        body = html.unescape(body)
        body = html.unescape(body)
    body = body.replace('\r', '').replace('\n', ' ')
    body = re.sub(r'\(?http[^ ]+\)?', '', body)

    # don't classify deleted texts
    if body == '[deleted]' or body == '[removed]':
        label = ""
        confidence = ""
        length = ""

    # language classification
    else:
        result = MODEL.predict(body)
        label = result[0][0]
        confidence = str(result[1][0])
        length = str(len(body))

    data_line = "\t".join([
        link_id,
        id,
        parent_id,
        created_utc,
        subreddit,
        subreddit_id,
        is_promoted,
        length,
        label,
        confidence
    ]) + "\n"

    return label, data_line


def process_file(path_in):

    languages = LANGUAGES

    # identify compression
    compression = path_in.split(".")[-1]

    # set paths to output
    drive, tail = os.path.split(path_in)
    drive_scores = os.path.join(DIR_OUT, "languages", "all", "scores")
    os.makedirs(drive_scores, exist_ok=True)
    path_scores = os.path.join(drive_scores, tail.replace("." + compression, ".tsv.gz"))

    header_line = "\t".join([
        'link_id',         # thread
        'id',              # comment or submission id
        'parent_id',       # actual parent (submission or comment, None of submission)
        'created_utc',
        'subreddit',
        'subreddit_id',
        'is_promoted',
        'length',
        'language',
        'confidence'
    ]) + "\n"

    # open files for each language
    files_languages = dict()
    for lang in languages:
        tail_lang = tail.replace("." + compression, ".tsv.gz")
        drive_lang = os.path.join(DIR_OUT, "languages", lang, "scores")
        os.makedirs(drive_lang, exist_ok=True)
        files_languages[lang] = gzip.open(os.path.join(drive_lang, tail_lang), "wt")

    # loop through lines
    with gzip.open(path_scores, "wt") as f_lang:

        # header
        f_lang.write(header_line)
        for lang in languages:
            files_languages[lang].write(header_line)

        # classify
        for line in path2lines(path_in):

            label, data_line = process_line(line)
            f_lang.write(data_line)

            for lang in languages:
                if label == f'__label__{lang}':
                    files_languages[lang].write(data_line)

    for lang in languages:
        files_languages[lang].close()


def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputglob',
                        type=str,
                        help='glob to input files [local/raw/*/R*]',
                        default="local/raw/*/R*")
    parser.add_argument('--dir_out',
                        type=str,
                        help='where to save the results [local/]',
                        default="local/")
    parser.add_argument('--lang_model',
                        type=str,
                        help='path to language model used by fasttext [local/lid.176.bin]',
                        default="local/lid.176.bin")
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
    paths_in = sorted(glob(args.inputglob))

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
