#!/usr/bin/python3
# -*- coding: utf-8 -*-

from utils import multi_proc
from glob import glob
import ujson
import gzip
import argparse


def main(path_in):

    # set path out
    path_out = path_in.replace(".ldjson.gz", "-thread-ids.tsv.gz")

    with gzip.open(path_out, "wt") as f_out, gzip.open(path_in, "rt") as f_in:
        f_out.write("\t".join(
            ["id", "created_utc", "subreddit_id", "parent_id", "link_id"]
        ) + "\n")

        for line in f_in:
            row = ujson.loads(line)
            f_out.write("\t".join([
                str(row['id']),
                str(row['created_utc']),
                str(row['subreddit_id']),
                str(row['parent_id']),
                str(row['link_id'])
            ]) + "\n")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("inputglob",
                        type=str,
                        help="glob to input files")
    parser.add_argument('--nr_proc',
                        type=int,
                        default=2,
                        help='how many processes to spawn')
    args = parser.parse_args()

    paths_in = glob(args.inputglob)
    multi_proc(main, paths_in, nr_cpus=args.nr_proc)
