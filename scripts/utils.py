#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bz2
import gzip
import lzma
import os
from multiprocessing import Pool

import zstandard as zstd
from tqdm import tqdm


class MultiFileWriter:
    """write to multiple files at a time without specifing paths in
    advance.  takes care of appropriately opening and closing all file
    connections, respecting the upper limit of connections.

    """

    def __init__(self, compression='gzip', init_mode='wt', create_dir=True, limit=512):

        # upper limit for open connections = 1024
        # on ubuntu: run $ ulimit -n
        self.limit = limit
        self.init_mode = init_mode
        self.create_dir = create_dir
        self.compression = compression
        self.paths = dict()     # [path]: dict(open?, count, connection)
        self.nr_open = 0

    def _open(self, path, mode, warning=True):

        # close if no more space
        # TODO: add heuristics for closing rarely used connections
        if self.nr_open >= self.limit:
            if warning:
                print('\n' + 'closing all connections')
            self.close()

        # check if parent directories exist
        if self.create_dir:
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError as exc:  # guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

        # open connection
        if self.compression == 'gzip':
            self.paths[path]['connection'] = gzip.open(path, mode=mode)
        elif self.compression is None:
            self.paths[path]['connection'] = open(path, mode=mode)
        self.paths[path]['open'] = True

        # increase count
        self.nr_open += 1

    def write(self, path, string):

        if path not in self.paths.keys():

            # init path
            self.paths[path] = dict()
            # open connection for first time
            self._open(path, self.init_mode)
            # start counting
            self.paths[path]['count'] = 0

        elif not self.paths[path]['open']:

            # re-open connection (attach to file)
            self._open(path, 'at')

        # write
        self.paths[path]['connection'].write(string)
        # count use
        self.paths[path]['count'] += 1

    def close(self):

        # close all paths
        for path in self.paths.keys():
            if 'connection' in self.paths[path].keys():
                self.paths[path]['connection'].close()
            self.paths[path]['open'] = False
        self.nr_open = 0


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
