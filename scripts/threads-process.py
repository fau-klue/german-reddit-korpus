#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
import os
from pandas import DataFrame
from collections import defaultdict
from glob import glob
from utils_markdown import process_thread


def process_threads(paths_in, path_xml, path_meta):
    # NB: I don't make no distinction between submissions and comments
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

    print("writing xml and collecting meta data")
    meta_records = list()
    with gzip.open(path_xml, mode="wt") as f_out:

        f_out.write("<corpus>\n")
        for c, (idx, time) in enumerate(id2time):
            print(f'thread {c+1}/{len(id2time)}', end="\r")
            xml_str, meta = process_thread(threads[idx])
            meta_records.extend(meta)
            f_out.write(xml_str)
        print()
        f_out.write("</corpus>\n")

    print("saving meta data")
    # save meta data separately as data frame
    meta_data = DataFrame(meta_records)
    meta_data.to_csv(path_meta, compression="gzip", encoding="utf-8", sep="\t", index=False)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--glob_in',
                        type=str,
                        help='glob to dumps of comments and submissions',
                        default="local/languages/de-posts/*ldjson.gz")
    parser.add_argument('--path_xml',
                        type=str,
                        help="path to save texts",
                        default="local/languages/de-gerede.xml.gz")
    parser.add_argument('--path_tsv',
                        type=str,
                        help="path to save meta data",
                        default="local/languages/de-gerede.tsv.gz")

    args = parser.parse_args()

    threads_dict = process_threads(sorted(glob(args.glob_in)), args.path_xml, args.path_tsv)
