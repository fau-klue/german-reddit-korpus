#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
import os
from collections import defaultdict
from glob import glob


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

    parser = argparse.ArgumentParser()
    parser.add_argument('--glob_in',
                        type=str,
                        help='glob to dumps of comments and submissions',
                        default="local/languages/de-posts/*ldjson.gz")
    parser.add_argument('--path_out',
                        type=str,
                        help="path to save threads",
                        default="local/languages/de-gerede.ldjson.gz")
    args = parser.parse_args()
    threads_dict = sort_threads(sorted(glob(args.glob_in)), args.path_out)
