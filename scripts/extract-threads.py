#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
import ujson
import argparse
import os
from pandas import read_csv
from glob import glob
from collections import defaultdict
from utils import path2lines, multi_proc


def extract_threads(path_in):
    """ uses global link_ids """

    drive, tail = os.path.split(path_in)
    path_out = os.path.join(DIR_OUT, tail.split(".")[0] + ".ldjson.gz")

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


def sort_threads(paths_in, path_out):

    # NB: implementation doesn't make a distinction between submissions and comments
    # I hope that submissions are created consistently before comments

    print("collecting threads")
    # threads = {link_id: [post, post, ... post], link_id: [post, post, .., post], ...}
    threads = defaultdict(list)
    # iterate over submissions, creating threads
    for c, p in enumerate(paths_in):
        print(f'file {c+1}/{len(paths_in)}', end="\r")
        drive, tail = os.path.split(p)
        with gzip.open(p, "rt") as f:
            for line in f:

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

                # create / append thread
                threads[link_id].append(row)
    print()

    print("sorting within threads")
    # sort each thread by time (i.e. first one is (hopefully) the submission)
    id2time = list()
    for thread_id, thread_list in threads.items():
        thread = sorted(thread_list, key=lambda d: int(d['created_utc']))
        threads[thread_id] = thread
        id2time.append((thread_id, int(thread[0]['created_utc'])))

    print("sorting threads")
    # sort globally by submission creation
    id2time = sorted(id2time, key=lambda d: int(d[1]))

    print("writing")
    with gzip.open(path_out, "wt") as f_out:
        for c, (idx, time) in enumerate(id2time):
            print(f'thread {c+1}/{len(id2time)}', end="\r")
            f_out.write(ujson.dumps(threads[idx]) + "\n")
        print()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--glob_in',
                        type=str,
                        help='glob to raw files',
                        default="local/raw/*/R*")
    parser.add_argument('--path_ids',
                        type=str,
                        help='path to file containing link_ids (threads) to extract',
                        default="local/languages/de/posts-de-by-thread.tsv.gz")
    parser.add_argument('--path_out',
                        type=str,
                        help="where to save threads",
                        default="local/languages/de-gerede.ldjson.gz")
    parser.add_argument('--dir_monthly',
                        type=str,
                        help="where to save monthly files",
                        default="local/languages/de-posts/")
    parser.add_argument('--nr_proc',
                        type=int,
                        default=12,
                        help='how many processes to spawn')
    args = parser.parse_args()

    global DIR_OUT
    DIR_OUT = args.dir_out
    os.makedirs(DIR_OUT, exist_ok=True)

    print("getting relevant link-ids")
    df = read_csv(args.path_link_ids, sep="\t", dtype=str)
    global link_ids
    link_ids = set([idx.split("_")[-1] for idx in df['link_id']])

    print("looping through raw files")
    paths_raw = sorted(glob(args.glob_raw))
    paths_raw = [p for p in paths_raw if len(p.split("/")[-1].split(".")[0]) == 10]
    multi_proc(extract_threads, paths_raw, args.nr_proc)

    paths_in = glob(os.path.join(args.dir_out, "*ldjson.gz"))
    sort_threads(paths_in, args.path_out)
