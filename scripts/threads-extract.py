#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
import ujson
import argparse
from pandas import read_csv
from glob import glob
from utils import path2lines, multi_proc


def pp(p):
    file_idx = p.split("/")[-1].split(".")[0]
    p_out = "../threads/" + file_idx + "-de-threads.ldjson.gz"
    with gzip.open(p_out, "wt") as f_out:
        for line in path2lines(p):
            row = ujson.loads(line)
            if row['link_id'] in relevant_links:
                f_out.write(line)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('inputglob',
                        type=str,
                        help='glob to input files (*-de-thread-ids.tsv.gz)')
    parser.add_argument('raw',
                        type=str,
                        help='glob to raw comments')
    parser.add_argument('--nr_proc',
                        type=int,
                        default=2,
                        help='how many processes to spawn')
    args = parser.parse_args()

    paths_ids = glob(args.inputglob)

    print("getting relevant link-ids")
    relevant_links = set()
    for p in paths_ids:
        df = read_csv(p, sep="\t", index_col=0)
        relevant_links = relevant_links.union(set(df.link_id))

    paths_raw = glob(args.raw)
    print("looping through all files")
    multi_proc(pp, paths_raw, args.nr_proc)
