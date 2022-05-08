#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
import ujson
import argparse
from pandas import read_csv
from glob import glob
from utils import path2lines, multi_proc


def extract_threads(path_in):
    """ uses global link_ids and global field """

    path_out = path_in.split(".")[0] + "-lang-de.ldjson.gz"
    with gzip.open(path_out, "wt") as f_out:
        for line in path2lines(path_in):
            try:
                row = ujson.loads(line)
            except ujson.JSONDecodeError:
                print(row)
            if row[field] in link_ids:
                line = line.rstrip() + "\n"
                f_out.write(line)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path_link_ids',
                        type=str,
                        help='path to file containing link_ids (threads) to extract')
    parser.add_argument('glob_raw',
                        type=str,
                        help='glob to raw comment files')
    parser.add_argument('--submissions',
                        action='store_true',
                        default=False,
                        help='extract from submissions instead of comments? [False]')
    parser.add_argument('--nr_proc',
                        type=int,
                        default=10,
                        help='how many processes to spawn [10]')
    args = parser.parse_args()

    print("getting relevant link-ids")
    global link_ids
    with gzip.open(args.path_link_ids, "rt") as f:
        link_ids = f.read().strip().split("\n")
    if args.submissions:
        link_ids = [idx.split("_")[-1] for idx in link_ids]
    link_ids = set(link_ids)
    global field
    field = 'id' if args.submissions else 'link_id'

    print("looping through raw files")
    paths_raw = sorted(glob(args.glob_raw))
    paths_raw = [p for p in paths_raw if len(p.split("/")[-1].split(".")[0]) == 10]
    multi_proc(extract_threads, paths_raw, args.nr_proc)
