#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
import ujson
import argparse
import os
from pandas import read_csv
from glob import glob
from utils import path2lines, multi_proc


def extract_threads(path_in):
    """ uses global link_ids and global field """

    drive, tail = os.path.split(path_in)
    path_out = os.path.join(DIR_OUT, tail.split(".")[0] + "-de.ldjson.gz")

    with gzip.open(path_out, "wt") as f_out:
        for line in path2lines(path_in):

            # load line
            try:
                row = ujson.loads(line)
            except ujson.JSONDecodeError:
                print(row)

            # get id
            if tail.startswith("RC"):
                link_id = row['link_id'].split("_")[-1]  # comments: remove leading "t3_"
            elif tail.startswith("RS"):
                link_id = row['id']
            else:
                raise ValueError('only files starting with RS or RC can be processed')

            # write
            if link_id in link_ids:
                line = line.rstrip() + "\n"
                f_out.write(line)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--path_link_ids',
                        type=str,
                        help='path to file containing link_ids (threads) to extract',
                        default="local/languages/RC-de-per-thread-subreddit-filtered.tsv.gz")
    parser.add_argument('--glob_raw',
                        type=str,
                        help='glob to raw files',
                        default="local/raw/*/R*")
    parser.add_argument('--dir_out',
                        type=str,
                        help="where to save results",
                        default="local/languages/de/posts/")
    parser.add_argument('--cut_off',
                        default=0.1,
                        help="cut-off for confidence")
    parser.add_argument('--nr_proc',
                        type=int,
                        default=8,
                        help='how many processes to spawn [8]')
    args = parser.parse_args()

    global DIR_OUT
    DIR_OUT = args.dir_out
    os.makedirs(DIR_OUT, exist_ok=True)
    
    print("getting relevant link-ids")
    df = read_csv(args.path_link_ids, sep="\t", index_col=0)
    df = df.loc[df['confidence'] > args.cut_off]
    # ids are without leading "t3_"
    global link_ids
    link_ids = set([idx.split("_")[-1] for idx in df.index])

    print("looping through raw files")
    paths_raw = sorted(glob(args.glob_raw))
    # TODO improve sanity check
    paths_raw = [p for p in paths_raw if len(p.split("/")[-1].split(".")[0]) == 10]
    multi_proc(extract_threads, paths_raw, args.nr_proc)
