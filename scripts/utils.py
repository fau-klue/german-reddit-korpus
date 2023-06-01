#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bz2
import gzip
import io
import lzma
from multiprocessing import Pool

import zstandard as zstd
from tqdm import tqdm


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
            stream_reader = dctx.stream_reader(fh)
            text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')
            for line in text_stream:
                yield line

    else:
        raise ValueError('compression type not supported')
