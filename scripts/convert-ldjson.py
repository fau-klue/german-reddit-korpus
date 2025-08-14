#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
from pandas import DataFrame
from utils_markdown import process_thread


def process_threads(path_in, path_xml, path_meta):

    print("writing xml and collecting meta data")
    meta_records = list()
    with gzip.open(path_in, "rt") as f, gzip.open(path_xml, mode="wt") as f_out:
        f_out.write("<corpus>\n")
        for line in f:
            try:
                thread = ujson.loads(line)
                xml_str, meta = process_thread(thread)
                meta_records.extend(meta)
                f_out.write(xml_str)
            except:
                print("error in line, skipping")
                print(line)
        f_out.write("</corpus>\n")

    print("saving meta data")
    meta_data = DataFrame(meta_records)
    meta_data.to_csv(path_meta, compression="gzip", encoding="utf-8", sep="\t", index=False)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--path_in',
                        type=str,
                        help='path to threads in ldjson format',
                        default="local/languages/de/gerede.ldjson.gz")
    parser.add_argument('--path_xml',
                        type=str,
                        help="path to save texts",
                        default=None)
    parser.add_argument('--path_tsv',
                        type=str,
                        help="path to save meta data",
                        default=None)
    args = parser.parse_args()

    path_xml = args.path_in.replace('.ldjson.gz', '.xml.gz') if args.path_xml is None else args.path_xml
    path_tsv = args.path_in.replace('.ldjson.gz', '.tsv.gz') if args.path_tsv is None else args.path_tsv

    process_threads(args.path_in, path_xml, path_tsv)
