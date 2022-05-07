#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
import ujson
import argparse
from pandas import read_csv
from glob import glob
from utils import path2lines, multi_proc


def extract_threads(path_in):
    """ uses global link_ids """
    path_out = path_in.split(".")[0] + "-de.ldjson.gz"
    with gzip.open(path_out, "wt") as f_out:
        for line in path2lines(path_in):
            row = ujson.loads(line)
            if row['link_id'] in link_ids:
                f_out.write(line)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--path_link_ids',
                        type=str,
                        help='path to file containing link_ids of potentialls German threads',
                        default='/cip/corpora/Web/Reddit/raw/german-thread-ids.txt.gz')
    parser.add_argument('--glob_raw',
                        type=str,
                        help='glob to raw comment files',
                        default='/cip/corpora/Web/Reddit/raw/comments/RC_*')
    parser.add_argument('--nr_proc',
                        type=int,
                        default=10,
                        help='how many processes to spawn')
    args = parser.parse_args()

    print("getting relevant link-ids")
    global link_ids
    with gzip.open(args.path_link_ids, "rt") as f:
        link_ids = set(f.read().strip().split("\n"))

    print("looping through raw files")
    paths_raw = sorted(glob(args.glob_raw))
    paths_raw = [p for p in paths_raw if len(p.split("/")[-1].split(".")[0]) == 10]
    multi_proc(extract_threads, paths_raw, args.nr_proc)
