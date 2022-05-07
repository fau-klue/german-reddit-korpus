#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Philipp Heinrich, 2022.

import gzip
from argparse import ArgumentParser
from glob import glob
from utils import multi_proc


def main(path_in, lang="de"):

    path_out = path_in.split(".")[0] + "-%s.tsv.gz" % lang

    with gzip.open(path_out, 'wt') as f_out, gzip.open(path_in, 'rt') as f_in:
        for line in f_in:
            row = line.split("\t")
            # TODO: remove NAs
            try:
                if row[6] == '__label__%s' % lang:
                    f_out.write(line)
            except IndexError:
                print(row)


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--glob_in", type=str, default="/cip/corpora/Web/Reddit/raw/comments/*lang.tsv.gz")
    parser.add_argument('--nr_proc', type=int, default=10, help='how many processes to spawn')

    args = parser.parse_args()

    paths_in = sorted(glob(args.glob_in))
    multi_proc(main, paths_in, nr_cpus=args.nr_proc)
