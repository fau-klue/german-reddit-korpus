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

import enchant  # pip3 install pyenchant
import langid  # pip3 install langid
import ujson  # pip3 install ujson

from utils import multi_proc, path2lines

dict_en = enchant.Dict("en_US")
dict_de = enchant.Dict("de_DE")


# line-by-line filtering
def process_line(line):

    # load line
    parsed_json = ujson.loads(line.strip())

    # sanitize text
    sanitized_body = parsed_json['body'].replace('\r', '')
    sanitized_body = sanitized_body.replace('\n', ' ')
    sanitized_body = re.sub(r'\(?http[^ ]+\)?', '', sanitized_body)

    if len(sanitized_body) <= 10 or sanitized_body == '[deleted]':
        german = None

    else:
        german = False

        # first test: spell-checking
        tcount = 0
        errors_en = 0
        errors_de = 0
        for token in re.findall(r'\w+', sanitized_body, re.UNICODE):
            tcount += 1
            if dict_en.check(token) is False:
                errors_en += 1
            if dict_de.check(token) is False:
                errors_de += 1

        if tcount != 0 and ((errors_en/tcount) > 0.3) and ((errors_de/tcount) < 0.7):

            # second test: language classification
            langid_response = langid.classify(sanitized_body)
            if langid_response[0] == 'de':
                german = True

    return {
        'idx': parsed_json['id'],
        'txt': sanitized_body,
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
            from pprint import pprint
            pprint(line)
            result = process_line(line)
            f_meta.write("\t".join(
                [result['idx'], result['subreddit'], str(result['german'])]
            ) + "\n")
            if result['german']:
                f_german.write(result['line'])


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
