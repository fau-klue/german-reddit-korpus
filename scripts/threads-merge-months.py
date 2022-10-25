#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gzip
from glob import glob
from cutils.times import Progress
from argparse import ArgumentParser


IGNORE_TAGS = {
    'corpus'
    'ul',
    'li',
    'strong',
    'ol',
    'sup',
    'hr',
    'del'
}


def main(paths_in, path_out, corpus_name):
    with gzip.open(path_out, "wt") as f_out:

        f_out.write('<corpus name="%s">\n' % corpus_name)

        for p in paths_in:

            print(p)

            cohort_idx = p.split("/")[-1].split(".")[0]
            f_out.write('<cohort id="%s">\n' % cohort_idx)

            with gzip.open(p, "rt") as f:
                for line in f:
                    if line.startswith("<"):
                        row = line.split(" ")[0].rstrip(">\n").lstrip("</")
                        if row in IGNORE_TAGS:
                            continue
                    f_out.write(line)

            f_out.write("</cohort>\n")

        f_out.write("</corpus>\n")


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("glob_in",
                        help='glob to paths to read from',
                        type=str)
    parser.add_argument("path_out",
                        help="path to write to",
                        type=str)
    parser.add_argument("--name",
                        help="name of the corpus [derived from path_out]",
                        default=None,
                        type=str)
    parser.add_argument("--sort",
                        "-s",
                        help="sort the paths alphabetically? [True]",
                        action='store_false',
                        default=True)

    args = parser.parse_args()
    corpus_name = args.path_out.split("/")[-1].split(".")[0] if args.name is None else args.name
    paths_in = sorted(glob(args.glob_in)) if args.sort else glob(args.glob_in)
    main(paths_in, args.path_out, corpus_name)
