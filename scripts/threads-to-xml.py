#!/usr/bin/env python3

import argparse
import gzip
import ujson
from glob import glob

import pandas as pd

from utils import multi_proc
from utils_markdown import process_thread


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("glob_in", help="glob to files to read", type=str)
    parser.add_argument('--nr_proc', type=int, help='how many processes to spawn [8]', default=8)
    return parser.parse_args()


def process_file(path_in):

    # determine paths to write to
    base = path_in              # os.path.basename(path_in)
    if base[-10:] == ".ldjson.gz":
        base = base[:-10]
    path_meta = "%s.tsv.gz" % (base)
    path_xml = "%s.xml.gz" % (base)

    # write xml and collect meta data
    records = list()
    with gzip.open(path_in, mode="rt") as f_in, gzip.open(path_xml, mode="wt") as f_out:

        f_out.write("<corpus>\n")

        for i, thread_line in enumerate(f_in):
            # print(i, end="\r")
            # if i == 1000:
            #     break

            try:
                thread = ujson.loads(thread_line)
                xml_str, meta = process_thread(thread)
                records.extend(meta)
                f_out.write(xml_str)
            except KeyError:
                print("error processing following line:")
                print(thread_line)
                pass

        f_out.write("</corpus>\n")

    # save meta data separately as data frame
    # print("\nsaving meta data")
    meta_data = pd.DataFrame(records)
    meta_data.to_csv(path_meta, compression="gzip", encoding="utf-8", sep="\t")


def main():

    args = arguments()
    paths_in = glob(args.glob_in)
    multi_proc(process_file, paths_in, nr_cpus=args.nr_proc)


if __name__ == "__main__":
    main()
