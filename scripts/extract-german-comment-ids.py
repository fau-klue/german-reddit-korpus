#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
from glob import glob


def main(paths_in, path_out):

    ids = set()
    for p in paths_in:
        with gzip.open(p, "rt") as f:
            for line in f:
                ids.add(ujson.loads(line)['id'])

    with gzip.open(path_out, "wt") as f_out:
        for idx in ids:
            f_out.write(str(idx) + "\n")


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
