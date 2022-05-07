#!/usr/bin/env python3

import argparse
import collections
import functools
import gzip
import logging
import math
import operator
import os
import re

import enchant   # pip3 install pyenchant
import langid    # pip3 install langid
import ujson     # pip3 install ujson

import utils

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

# global variables
target_languages = []
language_dicts = {}
regex = {}


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outdir", type=os.path.abspath, required=True, help="Output directory")
    # parser.add_argument("--nr-proc", type=int, default=2, help="How many processes to spawn")
    parser.add_argument("-c", "--comments", type=os.path.abspath, nargs="+", required=True, help="Comment files")
    parser.add_argument("-s", "--submissions", type=os.path.abspath, nargs="+", required=True, help="Submission files")
    return parser.parse_args()


def sanitize_text(text):
    sanitized_text = text.replace("\r", "")
    sanitized_text = sanitized_text.replace("\n", " ")
    sanitized_text = regex["url"].sub("", sanitized_text)
    return sanitized_text


def get_error_rate(words, target_lang):
    errors = 0
    total = len(words)
    wordfreq = collections.Counter(words)
    for word, freq in wordfreq.items():
        if not language_dicts[target_lang](word):
            errors += freq
    return errors / total


def process_line(line, is_submission):
    """line-by-line filtering"""
    parsed_json = ujson.loads(line.strip())
    if is_submission:
        thread_id = "t3_" + parsed_json["id"]
        # there are some submissions outside of subreddits; seem to be ads
        if "subreddit_id" not in parsed_json:
            return None
    else:
        thread_id = parsed_json["link_id"]
    result = {
        "idx": parsed_json["id"],
        "subreddit": parsed_json["subreddit"],
        "language": None,
        "created_utc": parsed_json["created_utc"],
        "subreddit_id": parsed_json["subreddit_id"],
        "parent_id": parsed_json.get("parent_id", "None"),
        "link_id": thread_id
    }
    if is_submission:
        sanitized_text = sanitize_text(parsed_json["selftext"])
    else:
        sanitized_text = sanitize_text(parsed_json["body"])

    if len(sanitized_text) <= 10 or sanitized_text == "[deleted]":
        result["language"] = "None"
        return result

    words = regex["word"].findall(sanitized_text)
    if len(words) == 0:
        result["language"] = "None"
        return result

    errors_en = get_error_rate(words, "en")
    if errors_en <= 0.3:
        result["language"] = "other"
        return result

    candidates = set([tl for tl in target_languages if get_error_rate(words, tl) < 0.7])
    if len(candidates) > 0:
        langid_response = langid.classify(sanitized_text)
        if langid_response[0] in candidates:
            result["language"] = langid_response[0]
            return result

    result["language"] = "other"
    return result


def extract_metadata(args):
    path_in, base, outdir, is_submission = args
    path_meta = os.path.join(outdir, "%s-meta.tsv.gz" % base)
    with gzip.open(path_meta, "wt", encoding="utf-8") as f_meta:
        f_meta.write("\t".join("id submission language created_utc subreddit subreddit_id link_id parent_id".split()) + "\n")
        for line in utils.path2lines(path_in):
            result = process_line(line, is_submission)
            if result is None:
                continue
            f_meta.write("\t".join([result["idx"],
                                    str(is_submission),
                                    str(result["language"]),
                                    str(result["created_utc"]),
                                    result["subreddit"],
                                    result["subreddit_id"],
                                    result["link_id"],
                                    result["parent_id"]]) + "\n")


def analyze_metadata(bases, outdir, target_lang):
    subreddits = {}
    threads = {}

    logging.info("Finding subreddits and threads with at least one '%s' comment" % target_lang)
    for base in bases:
        filename = os.path.join(outdir, "%s-meta.tsv.gz" % base)
        with gzip.open(filename, "rt", encoding="utf-8") as f:
            for line in f:
                idx, is_submission, language, created_utc, subreddit, subreddit_id, link_id, parent_id = line.rstrip().split("\t")
                if language == target_lang:
                    subreddits[subreddit_id] = collections.defaultdict(int)
                    threads[link_id] = collections.defaultdict(int)
                    threads[link_id]["subreddit_id"] = subreddit_id

    logging.info("Scoring found subreddits and threads")
    for base in bases:
        filename = os.path.join(outdir, "%s-meta.tsv.gz" % base)
        with gzip.open(filename, "rt", encoding="utf-8") as f:
            for line in f:
                idx, is_submission, language, created_utc, subreddit, subreddit_id, link_id, parent_id = line.rstrip().split("\t")
                if subreddit_id in subreddits:
                    subreddits[subreddit_id]["total"] += 1
                    if language == target_lang:
                        subreddits[subreddit_id]["target"] += 1
                if link_id in threads:
                    threads[link_id]["total"] += 1
                    if language == target_lang:
                        threads[link_id]["target"] += 1

    path_subreddits = os.path.join(outdir, "subreddit-scores-%s.tsv.gz" % target_lang)
    logging.info("Writing subreddit scores to %s" % path_subreddits)
    with gzip.open(path_subreddits, "wt", encoding="utf-8") as out:
        out.write("\t".join("subreddit_id target total fraction threshold exceeded".split()) + "\n")
        for subreddit_id, freqs in subreddits.items():
            fraction = freqs["target"] / freqs["total"]
            threshold = math.exp(math.sqrt(freqs["total"]) / -4) + 0.015
            out.write("\t".join([subreddit_id,
                                 str(freqs["target"]),
                                 str(freqs["total"]),
                                 str(fraction),
                                 str(threshold),
                                 str(fraction >= threshold)]) + "\n")

    path_threads = os.path.join(outdir, "thread-scores-%s.tsv.gz" % target_lang)
    logging.info("Writing thread scores to %s" % path_threads)
    with gzip.open(path_threads, "wt", encoding="utf-8") as out:
        out.write("\t".join("link_id target total fraction subreddit_fraction score exceeded".split()) + "\n")
        for link_id, dic in threads.items():
            fraction = dic["target"] / dic["total"]
            subreddit_fraction = subreddits[dic["subreddit_id"]]["target"] / subreddits[dic["subreddit_id"]]["total"]
            score = fraction * subreddit_fraction
            out.write("\t".join([link_id,
                                 str(dic["target"]),
                                 str(dic["total"]),
                                 str(fraction),
                                 str(subreddit_fraction),
                                 str(score),
                                 str(score >= 0.1)]) + "\n")


def extract_threads(comments, submissions, outdir, target_lang):
    logging.info("Extract threads identified as %s" % target_lang)
    threads = {}
    path_threads = os.path.join(outdir, "thread-scores-%s.tsv.gz" % target_lang)
    with gzip.open(path_threads, "rt", encoding="utf-8") as f:
        for line in f:
            link_id, target, total, fraction, subreddit_fraction, score, exceeded = line.rstrip().split("\t")
            if exceeded == "True":
                threads[link_id] = []
    for filename in comments:
        for line in utils.path2lines(filename):
            parsed_json = ujson.loads(line)
            link_id = parsed_json["link_id"]
            if link_id in threads:
                threads[link_id].append((parsed_json["created_utc"], parsed_json["id"], line))
    for filename in submissions:
        for line in utils.path2lines(filename):
            parsed_json = ujson.loads(line)
            parsed_json = ujson.loads(line)
            link_id = "t3_" + parsed_json["id"]
            if link_id in threads:
                threads[link_id].append((parsed_json["created_utc"], parsed_json["id"], line))

    output = os.path.join(outdir, "threads-%s.ldjson.gz" % target_lang)
    logging.info("Writing extracted threads to %s" % output)
    skipped = 0
    with gzip.open(output, "wt", encoding="utf-8") as out:
        for thread, comments in threads.items():
            ids = set()
            for created_utc, idx, line in sorted(comments, key=operator.itemgetter(0)):
                # skip duplicates
                if idx in ids:
                    skipped += 1
                    continue
                ids.add(idx)
                out.write(line)
    logging.info("Skipped %d duplicate comments" % skipped)


def set_global_variables():
    global target_languages
    # target languages in decreasing order (most to fewest comments):
    target_languages = ["de", "it", "sq"]
    global language_dicts
    language_dicts["en"] = functools.lru_cache(2 ** 16)(enchant.Dict("en_US").check)
    language_dicts["de"] = functools.lru_cache(2 ** 16)(enchant.Dict("de_DE").check)
    language_dicts["it"] = functools.lru_cache(2 ** 16)(enchant.Dict("it_IT").check)
    language_dicts["sq"] = functools.lru_cache(2 ** 16)(enchant.Dict("sq_AL").check)
    global regex
    regex["url"] = re.compile(r"\(?http[^ ]+\)?")
    regex["word"] = re.compile(r"\w+", re.UNICODE)


def main():
    args = arguments()
    set_global_variables()
    comments = args.comments
    comment_bases = [os.path.splitext(os.path.basename(fn))[0] for fn in comments]
    submissions = args.submissions
    submission_bases = [os.path.splitext(os.path.basename(fn))[0] for fn in submissions]
    all_bases = comment_bases + submission_bases

    # logging.info("Extract metadata from comments using %d processes" % args.nr_proc)
    # multi_args = zip(comments, comment_bases, itertools.repeat(args.outdir), itertools.repeat(False))
    # utils.multi_proc(extract_metadata, multi_args, nr_cpus=args.nr_proc)
    logging.info("Extract metadata from comments and identify languages")
    for filename, base in zip(comments, comment_bases):
        logging.info(filename)
        extract_metadata((filename, base, args.outdir, False))

    # logging.info("Extract metadata from submissions using %d processes" % args.nr_proc)
    # multi_args = zip(submissions, submission_bases, itertools.repeat(args.outdir), itertools.repeat(True))
    # utils.multi_proc(extract_metadata, multi_args, nr_cpus=args.nr_proc)
    logging.info("Extract metadata from submissions and identify languages")
    for filename, base in zip(submissions, submission_bases):
        logging.info(filename)
        extract_metadata((filename, base, args.outdir, True))

    logging.info("Analyze metadata")
    for target_lang in target_languages:
        analyze_metadata(all_bases, args.outdir, target_lang)

    logging.info("Extract threads")
    for target_lang in target_languages:
        extract_threads(comments, submissions, args.outdir, target_lang)


if __name__ == "__main__":
    main()
