#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import ujson
import gzip
from glob import glob
from pandas import read_csv


def main(path_meta, paths_sub, path_out):

    df = read_csv(path_meta, sep="\t")
    df = df.loc[df.thread_score >= 0.1]
    rel_ids = set(df.submission_id)

    with gzip.open(path_out, "wt") as f_out:
        for p in paths_sub:
            with gzip.open(p, "rt") as f:
                for line in f:
                    sub = ujson.loads(line)
                    if sub['id'] in rel_ids:
                        f_out.write(line)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('inputglob',
                        type=str,
                        help='glob to raw submission files')
    parser.add_arugment('path_meta',
                        type=str,
                        help='path to threads-all-lang-scores.tsv.gz')
    parser.add_argument('path_out',
                        type=str,
                        help="path to save result to")
    args = parser.parse_args()

    paths_sub = glob(args.inputglob)
    paths_sub.sort()
    main(args.path_meta, paths_sub, args.path_out)
