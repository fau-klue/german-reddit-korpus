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
            thread = ujson.loads(line)
            xml_str, meta = process_thread(thread)
            meta_records.extend(meta)
            f_out.write(xml_str)
        f_out.write("</corpus>\n")

    print("saving meta data")
    meta_data = DataFrame(meta_records)
    meta_data.to_csv(path_meta, compression="gzip", encoding="utf-8", sep="\t", index=False)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--path_in',
                        type=str,
                        help='path to threads in ldjson format',
                        default="local/languages/de-gerede.ldjson.gz")
    parser.add_argument('--path_xml',
                        type=str,
                        help="path to save texts",
                        default="local/languages/de-gerede.xml.gz")
    parser.add_argument('--path_tsv',
                        type=str,
                        help="path to save meta data",
                        default="local/languages/de-gerede.tsv.gz")
    args = parser.parse_args()

    process_threads(args.path_in, args.path_xml, args.path_tsv)
