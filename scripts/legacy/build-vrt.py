from glob import glob
import gzip
from cutils.cwb.vrt import iter_texts
from cutils.times import Progress
from pandas import read_csv
from cutils.cwb.vrt import dict2meta
# from cutils.cwb.vrt import plain2mysql
# from pandas import concat
# from cutils.times import unix2ymd


paths_comments = glob("../threads/threads-filtered-processed/input*.xml.gz.tok.tag.fix.gz")
path_submissions = "../threads/threads-filtered-processed/threads-filtered-submissions.tok.tag.fix.gz"
path_out = "../gerede-v1.1.vrt.gz"
# path_meta_submissions = "../threads/submissions-meta-classes.tsv.gz"
# path_meta_submissions_2 = "../threads/submissions-mini-meta.tsv"
# path_meta_comments = "../threads/threads-filtered.tsv.gz"

# meta preprocessing
# meta = read_csv(path_meta_submissions, sep="\t", index_col=0, dtype=str)
# meta['created_utc'] = meta['created_utc'].astype(int)
# meta['ymd'] = meta.created_utc.apply(unix2ymd)
# meta['ym'] = meta.ymd.apply(lambda x: x[:6])
# meta['year'] = meta.ymd.apply(lambda x: x[:4])
# meta['created_utc'] = meta['created_utc'].astype(str)
# meta_2 = read_csv(path_meta_comments, sep="\t", dtype=str)
# meta_2.index = meta_2.link_id.apply(lambda x: x.split("_")[-1])
# meta = concat([meta, meta_2])
# meta = meta.loc[~meta.index.duplicated(keep='first')]
# meta.fillna("NA", inplace=True)
# meta.drop(["retrieved_on"], axis=1, inplace=True)
# meta.link_flair_text_class = meta.link_flair_text_class.apply(plain2mysql)
# meta.to_csv("../meta/submissions-cqpweb.tsv.gz", compression="gzip", sep="\t")

# meta_comments = read_csv(path_meta_comments, sep="\t", index_col=0, dtype=str)
# meta_comments = meta_comments.loc[~meta_comments.index.duplicated(keep='first')]
# meta_comments.fillna("NA", inplace=True)
# meta_comments.drop(["subreddit", "subreddit_id", "retrieved_on"], inplace=True, axis=1)
# meta_comments.to_csv("../meta/comments-cqpweb.tsv.gz", compression="gzip", sep="\t")


meta_comments = read_csv("../meta/comments-cqpweb.tsv.gz", index_col=0, sep="\t", dtype=str)
meta_comments.fillna("NA", inplace=True)
meta = read_csv("../meta/submissions-cqpweb.tsv.gz", index_col=0, sep="\t", dtype=str)
meta.fillna("NA", inplace=True)


def insert_s(text):
    in_paragraph = False
    out = list()
    for line in text:
        if line == "<p>":
            in_paragraph = True
            out.append(line)
            out.append("<s>")
        elif line == "</p>":
            out.append("</s>")
            out.append(line)
            in_paragraph = False
        elif line == "" and in_paragraph:
            out.append("</s>")
            out.append("<s>")
        elif line != "":
            out.append(line)
    return out


submissions = dict()
pb = Progress()
with gzip.open(path_submissions, "rt") as f_in:
    for submission, meta_sub in iter_texts(f_in, level="submission"):
        out = insert_s(submission)
        submissions[meta_sub['id']] = (meta_sub, out)
        pb.up()
pb.fine()


pb = Progress(rate=1, length=len(meta))
with gzip.open(path_out, "wt") as f_out:
    for p in paths_comments:
        with gzip.open(p, "rt") as f_in:
            for thread, meta_thread in iter_texts(f_in, level="thread"):

                # get id
                idx = meta_thread['id'].split("_")[-1]

                # is there a submission
                try:
                    submission = submissions[idx]
                    submission_meta = submission[0]
                    submission_text = submission[1]
                except KeyError:
                    submission = None

                try:
                    # write thread meta as text
                    m = dict(meta.loc[idx])
                    m['id'] = idx
                    f_out.write(dict2meta(m))

                    # write submission
                    if submission:
                        f_out.write(dict2meta(submission_meta, level="submission"))
                        f_out.write("\n".join(submission_text) + "\n")
                        f_out.write("</submission>\n")

                    # write comments
                    for comment, meta_comment in iter_texts(thread, level="comment"):
                        m = dict(meta_comments.loc[meta_comment['id']])
                        m['id'] = meta_comment['id']
                        f_out.write(dict2meta(m, level="comment"))
                        f_out.write("\n".join(insert_s(comment)) + "\n")
                        f_out.write("</comment>\n")
                    f_out.write("</text>\n")
                except KeyError:
                    print()
                    print(idx)
                    print()
                pb.up()
