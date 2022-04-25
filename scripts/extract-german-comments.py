#!/usr/bin/python3
# -*- coding: utf-8 -*-

# based on a script available from https://github.com/adbar/german-reddit
# original copyright Adrien Barbaresi, 2015.
# MIT license

# modifications by Philipp Heinrich, 2022.

import argparse
import gzip
import re
from glob import glob

import langid                   # pip3 install langid
import ujson                    # pip3 install ujson

from utils import multi_proc, path2lines, spell_check


# line-by-line filtering
def process_line(line):

    # load line
    parsed_json = ujson.loads(line.strip())

    # sanitize text
    sanitized_body = parsed_json['body'].replace('\r', '')
    sanitized_body = sanitized_body.replace('\n', ' ')
    sanitized_body = re.sub(r'\(?http[^ ]+\)?', '', sanitized_body)

    # don't categorize very short or deleted texts
    if len(sanitized_body) <= 10 or sanitized_body == '[deleted]':
        german = None

    else:
        german = False

        # first test: spell-checking
        potentially_german = spell_check(sanitized_body)

        # second test: language classification
        if potentially_german:
            langid_response = langid.classify(sanitized_body)
            if langid_response[0] == 'de':
                german = True

    return {
        'idx': parsed_json['id'],
        # 'txt': sanitized_body,
        'line': line,
        'subreddit': parsed_json['subreddit'],
        'german': german
    }


def process_file(path_in):

    # identify compression
    compression = path_in.split(".")[-1]

    # set paths out
    path_german = path_in.replace("." + compression, "-de.ldjson.gz")
    path_meta = path_in.replace("." + compression, "-lang.tsv.gz")

    # do the actual processing
    with gzip.open(path_german, "wt") as f_german, gzip.open(path_meta, "wt") as f_meta:
        for line in path2lines(path_in):
            result = process_line(line)
            f_meta.write("\t".join(
                [result['idx'], result['subreddit'], str(result['german'])]
            ) + "\n")
            if result['german']:
                f_german.write(result['line'] + "\n")


def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('inputglob',
                        type=str,
                        help='glob to input files')
    parser.add_argument('--nr_proc',
                        type=int,
                        default=2,
                        help='how many processes to spawn')
    args = parser.parse_args()

    # set paths
    paths_in = glob(args.inputglob)

    # process files
    multi_proc(process_file, paths_in, nr_cpus=args.nr_proc)


if __name__ == "__main__":
    main()
