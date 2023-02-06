import argparse
import gzip
import os
import ujson
from utils import path2lines


def extract_posts(link_ids, path_in, path_out):

    drive, tail = os.path.split(path_in)

    c = 0
    with gzip.open(path_out, "wt") as f_out:
        for line in path2lines(path_in):
            c += 1
            if c % 1000 == 0:
                print(c, end="\r")

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

            # write
            if link_id in link_ids:
                line = line.rstrip() + "\n"
                f_out.write(line)
        print()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path_link_ids',
                        type=str,
                        help='path to file containing link_ids (threads) to extract')
    parser.add_argument('path_in',
                        type=str,
                        help="where to extract from")
    parser.add_argument('path_out',
                        type=str,
                        help="where to save results")
    args = parser.parse_args()

    with open(args.path_link_ids, "rt") as f:
        link_ids = f.read().strip().split("\n")
    link_ids = set([idx.split("_")[1] for idx in link_ids])

    extract_posts(link_ids, args.path_in, args.path_out)
