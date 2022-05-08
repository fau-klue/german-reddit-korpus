#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
from glob import glob
from collections import defaultdict


def collect_threads(paths_submissions, paths_comments):

    print("collecting threads")
    # NB: I don't make no distinction between submissions and comments
    # I hope that submissions are created consistently before comments
    threads = defaultdict(list)

    # iterate over submissions, creating threads
    for p in paths_submissions:
        print(p)
        with gzip.open(p, "rt") as f:
            for line in f:
                submission = ujson.loads(line)
                link_id = submission['id']
                threads[link_id].append(submission)

    # iterate over comments, add to threads
    for p in paths_comments:
        print(p)
        with gzip.open(p, "rt") as f:
            for line in f:
                comment = ujson.loads(line)
                link_id = comment['link_id'].split("_")[-1]
                threads[link_id].append(comment)

    return threads


def sort_threads(threads_dict):

    print("sorting threads internally")
    # sort all threads by created_utc of comments / submissions
    threads = list()
    for thread_id, thread_list in threads_dict.items():
        threads.append(sorted(thread_list, key=lambda d: int(d['created_utc'])))

    print("sorting threads globally")
    # sort threads by earliest created_utc
    threads = sorted(threads, key=lambda d: int(d[0]['created_utc']))

    return threads


def write_threads(threads, path_out):

    print("writing threads")
    with gzip.open(path_out, "wt") as f_out:
        for thread in threads:
            for comment in thread:
                f_out.write(ujson.dumps(comment) + "\n")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('glob_submissions',
                        type=str,
                        help='glob to submission files')
    parser.add_argument('glob_comments',
                        type=str,
                        help='glob to comment files')
    parser.add_argument('path_out',
                        type=str,
                        help="path to save result to")
    args = parser.parse_args()

    paths_submissions = sorted(glob(args.glob_submissions))
    paths_comments = sorted(glob(args.glob_comments))

    threads_dict = collect_threads(paths_submissions, paths_comments)
    threads = sort_threads(threads_dict)
    write_threads(threads, args.path_out)
