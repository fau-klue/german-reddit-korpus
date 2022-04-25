#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bz2
import gzip
import lzma
import re
from multiprocessing import Pool

import enchant                  # pip3 install pyenchant
import zstandard as zstd
from tqdm import tqdm

dict_en = enchant.Dict("en_US")
dict_de = enchant.Dict("de_DE")


def spell_check(text):

    tcount = 0
    errors_en = 0
    errors_de = 0
    for token in re.findall(r'\w+', text, re.UNICODE):
        tcount += 1
        if dict_en.check(token) is False:
            errors_en += 1
        if dict_de.check(token) is False:
            errors_de += 1

    return tcount != 0 and ((errors_en/tcount) > 0.3) and ((errors_de/tcount) < 0.7)


def multi_proc(processor, items, nr_cpus=2):
    """
    wrapper for multicore processing with progress bar
    """
    pool = Pool(nr_cpus)

    # if the number of items is explicit:
    try:
        total = len(items)
    except TypeError:
        total = None

    # loop through the items
    for _ in tqdm(
            pool.imap_unordered(processor, items),
            total=total
    ):
        pass


def path2lines(path_in):
    """
    yields each json line of compressed files
    """

    # identify compression
    compression = path_in.split(".")[-1]

    # open input file with correct compression and yield lines
    if compression == 'xz':
        with lzma.open(path_in, "rt") as f_in:
            for line in f_in:
                yield line

    elif compression == 'bz2':
        with bz2.open(path_in, "rt") as f_in:
            for line in f_in:
                yield line

    elif compression == 'gz':
        with gzip.open(path_in, "rt") as f_in:
            for line in f_in:
                yield line

    elif compression == 'zst':
        with open(path_in, 'rb') as fh:
            dctx = zstd.ZstdDecompressor(max_window_size=2147483648)
            with dctx.stream_reader(fh) as reader:
                previous_line = ""
                while True:
                    chunk = reader.read(2**24)
                    if not chunk:
                        break

                    string_data = chunk.decode('utf-8')
                    lines = string_data.split("\n")
                    for i, line in enumerate(lines[:-1]):
                        if i == 0:
                            line = previous_line + line
                        yield line
                        previous_line = lines[-1]

    else:
        raise ValueError('compression type not supported')
