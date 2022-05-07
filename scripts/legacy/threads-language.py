#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import gzip
import ujson
from pandas import read_csv


def german(d):
    """ gives a German score to a thread """
    prior = d['sr']
    N_thread = 0
    score = 0
    for el in d['lale']:
        N_thread += el[1]
        if el[0] == 'german':
            score += el[1]
    return prior * score / N_thread


def main(path_lang, path_threads, path_subreddits, path_out, path_scores):

    german_ids = set()
    with gzip.open(path_lang, "rt") as f:
        for line in f:
            german_ids.add(line.rstrip())
    subreddit = read_csv(path_subreddits, index_col=0)

    with gzip.open(path_threads, "rt") as f, gzip.open(path_out, "wt") as f_out, gzip.open(path_scores, "wt") as f_scores:
        for line in f:
            thread = ujson.loads(line)
            out = dict()
            # check subreddit
            comment = thread[0]
            out['link_id'] = comment['link_id']
            out['lale'] = list()
            try:
                out['sr'] = subreddit.loc[comment['subreddit']]['corpus_prop']
                for comment in thread:
                    if comment['id'] in german_ids:
                        la = "german"
                    else:
                        la = "nope"
                    le = len(comment['body'].split(" "))
                    out['lale'].append((la, le))
                out['score'] = german(out)
                f_scores.write(ujson.dumps(out))
                f_scores.write("\n")
                if out['score'] >= 0.1:
                    f_out.write(line)
            except KeyError:
                pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path_lang',
                        type=str,
                        help='path to german comment ids')
    parser.add_argument('path_scores',
                        type=str,
                        help="path to save scores to")
    parser.add_argument('path_threads',
                        type=str,
                        help="path to threads-all.ldjson.gz")
    parser.add_argument('path_subreddits',
                        type=str,
                        help="path to stats_filtered.csv.gz")
    parser.add_argument('path_out',
                        type=str,
                        help="path to save result to")
    args = parser.parse_args()

    main(args.path_lang,
         args.path_threads, args.path_subreddits,
         args.path_out, args.path_scores)
