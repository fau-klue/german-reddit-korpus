#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Philipp Heinrich, 2022.

import gzip
from argparse import ArgumentParser
from glob import glob
from pandas import read_csv
from utils import multi_proc

# TODO include in extract-german-comments.py

def collect_thread_ids(paths_in, path_out):

    thread_ids = set()

    for p in paths_in:
        print(p)
        d = read_csv(p, sep="\t",
                     names=[
                         'comment_id',
                         'created_utc',
                         'link_id',         # thread
                         'parent_id',       # actual parent (submission or comment)
                         'subreddit',
                         'subreddit_id',
                         'language',
                         'confidence',
                         'length'])
        
        d = d.dropna()          # unclassified stuff
        thread_ids = thread_ids.union(set(d['link_id']))
        print(len(thread_ids))

    with gzip.open(path_out, "wt") as f_out:
        f_out.write("\n".join(sorted(thread_ids)) + "\n")


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--glob_in", type=str, default="/cip/corpora/Web/Reddit/raw/comments/*lang-de.tsv.gz")
    parser.add_argument("--path_out", type=str, default="/cip/corpora/Web/Reddit/raw/german-thread-ids.txt.gz")
    args = parser.parse_args()

    paths_in = sorted(glob(args.glob_in))

    collect_thread_ids(paths_in, args.path_out)
