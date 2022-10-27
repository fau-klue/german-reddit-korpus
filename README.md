# GeRedE: A Corpus of German Reddit Exchanges
GeRedE is a xxx million token German CMC corpus containing approximately xxx submissions and xxx comments posted on [Reddit](https://www.reddit.com) between 2010 and mid-2021. Reddit is a popular online platform combining social news aggregation, discussion and micro-blogging. The CWB-indexed version of our final corpus is available to registered academic users via [CQPweb](https://corpora.linguistik.uni-erlangen.de/cqpweb/gerede_v2).

This repository contains the scripts we used to extract German submissions and comments from the vast amount of data Jason Baumgartner provides at https://files.pushshift.io/reddit. It also contains the IDs of all submissions and comments included in our corpus, so that those who wish to recreate our corpus are not required to run all processing steps by themselves.

## Dependencies

Install all Python [requirements](requirements.txt); we recommend using a virtual environment:

    python3 -m ven venv
    source venv/bin/activate
    pip install -r requirements.txt
    
Additionally, you will need the [fasttext model](https://fasttext.cc/docs/en/language-identification.html) for language classification. By default, the scripts assume it is located in `local/lid.176.bin`.

In order to run the R scripts, you will need the following libraries:

    argparse
    data.table
    R.utils
    tidyverse


## Steps for Recreating the Corpus

1. download the raw data
   - you need both comments and submissions (from the respective subdirectories)
   - https://files.pushshift.io/reddit
   - put them into `local/raw/comments/` and `local/raw/submissions/` respectively
   - they have to start with `RC` and `RS` respectively

2. classify comments by language
   ```
   python3 scripts/lang-classify.py (raw)
   ```
   by default, this creates two files per input file
   ```
   local/languages/all/scores/R(C|S)_{YYYY}-{MM}.tsv.gz  # scores for every language
   local/languages/de/scores/R(C|S)_{YYYY}-{MM}.tsv.gz   # scores for de
   ```
   you can use `--lang` to modify which languages should be extracted.


# TODO refactor R scripts (combine, add language option)
3. aggregate language scores (for German) monthly and globally per thread and per subreddit, filter
   ```
   Rscript scripts/prop-german-monthly.R (local/languages/de/scores/R(C|S)_{YYYY}-{MM}.tsv.gz)

   Rscript scripts/prop-german-complete.R

   Rscript scripts/prop-german-subreddit-filtered.R
   ```
   this creates
   ```
   local/languages/de/scores/R_{YYYY}-{MM}-per-subreddit.tsv.gz
   local/languages/de/scores/R_{YYYY}-{MM}-per-thread.tsv.gz
   
   local/languages/de/scores-per-subreddit.tsv.gz
   
   local/languages/de/filtered-ids.tsv.gz
   ```

4. extract submissions and comments from raw data (done separately so we can easily multiprocess)
   ```
   python3 scripts/threads-extract.py (local/languages/de/filtered-ids.tsv.gz, raw)
   ```
   this creates
   ```
   local/languages/de/posts/R(C|S)_{YYYY}-{MM}.ldjson.gz
   ```

5. collect and build XML texts and TSV table of meta data
   ```
   python3 scripts/threads-process.py (local/languages/de/posts/R(C|S)_{YYYY}-{MM}.ldjson.gz)
   ```
   this creates
   ```
   local/languages/de/gerede.xml.gz
   local/languages/de/gerede.tsv.gz
   ```


## References

Blombach, Andreas, Natalie Dykes, Philipp Heinrich, Besim Kabashi, and Thomas Proisl. 2020. “A Corpus of German Reddit Exchanges (GeRedE).”  In *Proceedings of the 12th Conference on Language Resources and Evaluation (LREC 2020)*, 6310–6316. Marseille: European Language Resources Association. [PDF](https://www.aclweb.org/anthology/2020.lrec-1.774.pdf).

```bibtex
@InProceedings{Blombach_et_al_LREC:2020,
author =    {Blombach, Andreas and Dykes, Natalie and Heinrich,
Philipp and Kabashi, Besim and Proisl, Thomas},
title =     {A Corpus of {G}erman {R}eddit Exchanges ({GeRedE})},
year =      {2020},
booktitle = {Proceedings of the 12th Conference on Language
Resources and Evaluation ({LREC} 2020)},
pages =     {6310--6316},
publisher = {European Language Resources Association},
address =   {Marseille},
url =       {https://www.aclweb.org/anthology/2020.lrec-1.774},
}
```
