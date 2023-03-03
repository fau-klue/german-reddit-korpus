import gzip
from argparse import ArgumentParser
from vrt.vrt import iter_s, dict2meta
from vrt.utils import Progress


def main(path_in, path_out):

    pb = Progress()

    with gzip.open(path_in, "rt") as f, gzip.open(path_out, "wt") as f_out:

        for thread, meta_thread in iter_s(f, level='thread'):

            thread_s = ""
            date = None

            for text, meta_text in iter_s(thread):
                if date is None:
                    date = meta_text['date']
                thread_s += dict2meta(meta_text, level='post')
                thread_s += "\n".join(text) + "\n"
                thread_s += '</post>\n'

            meta_thread['date'] = date
            meta_thread['year'] = "y" + date[:4]
            meta_thread['month'] = "m" + date[:7].replace("-", "_")

            thread_s = dict2meta(meta_thread) + thread_s + "</text>\n"

            f_out.write(thread_s)
            pb.up()

    pb.fine()


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("--path_in", default="local/languages/de-gerede.vrt.gz")
    parser.add_argument("--path_out", default="local/languages/de-gerede-cqpweb.vrt.gz")
    args = parser.parse_args()

    main(args.path_in, args.path_out)
