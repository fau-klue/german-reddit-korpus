#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
from glob import glob
from collections import defaultdict


def main(paths_in, path_out):
    threads = defaultdict(list)
    for p in paths_in:
        with gzip.open(p, "rt") as f_in:
            for line in f_in:
                row = ujson.loads(line)
                threads[row['link_id']].append(row)

    with gzip.open(path_out, "wt") as f_out:
        for link_id in threads.keys():
            f_out.write(ujson.dumps(threads[link_id]) + "\n")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('inputglob',
                        type=str,
                        help='glob to input files')
    parser.add_argument('path_out',
                        type=str,
                        help="path to save result to")
    args = parser.parse_args()

    paths_in = glob(args.inputglob)
    paths_in.sort()

    main(paths_in, args.path_out)
