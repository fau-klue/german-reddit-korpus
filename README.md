# GeRedE: A Corpus of German Reddit Exchanges
GeRedE is a xxx million token German CMC corpus containing approximately xxx submissions and xxx comments posted on [Reddit](https://www.reddit.com) between 2005 and 2022.  (Reddit is a popular online platform combining social news aggregation, discussion and micro-blogging.)  The CWB-indexed version of our final corpus is available to registered academic users via [CQPweb](https://corpora.linguistik.uni-erlangen.de/cqpweb/gerede_v2).

This repository contains the scripts we used to extract German submissions and comments from the vast amount of data Jason Baumgartner provides at https://files.pushshift.io/reddit.  It also contains the IDs of all submissions and comments included in our corpus, so that those who wish to recreate our corpus are not required to run all processing steps by themselves, but can just extract the threads that we identified as German from the raw data.

## Dependencies

Install all Python [requirements](requirements.txt); we recommend using a virtual environment:

    python3 -m ven venv
    source venv/bin/activate
    pip install -r requirements.txt
    
Additionally, you will need the [fasttext model](https://fasttext.cc/docs/en/language-identification.html) for language classification.  By default, the scripts assume it is located in `local/lid.176.bin`.

In order to run the R scripts, you will need the following libraries:

    argparse
    data.table
    R.utils
    tidyverse
    tidytable


## Steps for Recreating the Corpus

1. download the raw data
   - you need both comments and submissions (from the respective subdirectories)
   - https://files.pushshift.io/reddit
   - put them into `local/raw/comments/` and `local/raw/submissions/` respectively
   - they have to start with `RC` and `RS` respectively

2. classify comments by language
   ```
   python3 scripts/lang-classify.py
   ```
   this creates one file per input file
   ```
   local/languages/all/scores/R(C|S)_{YYYY}-{MM}.tsv.gz
   ```

3. aggregate language scores (for German) monthly and globally per thread and per subreddit, filter
   
    ```
   Rscript scripts/filter-relevant.R
   ```
   parameters:
   - to change the input path (default `local/language-scores/comments/*.tsv.gz`):
     `--glob_in path/*.tsv.gz`
   - to change the output directory (default `local/language-scores/aggregated`):
     `--dir_out some/path`
   - to change the language of the posts you're interested in, use the corresponding ISO 639-1 code (default `de`, i.e. German)
     `--lang en`
   - to overwrite existing files in the output directory, use the flag `-o` (by default, the program won't overwrite files, so you can restart it and continue the process without losing data if it runs out of memory)
   - if you only want to redo the filtering process after the files for individual months have already been created, you can skip this first step using the flag `-s` (probably together with `-o`)

   by default, this creates
   ```
   local/language-scores/de/R[CS]_{YYYY}-{MM}-de-per-subreddit.tsv.gz
   local/language-scores/de/R[CS]_{YYYY}-{MM}-de-per-thread.tsv.gz
   local/language-scores/de/posts-de-by-subreddit.tsv.gz (not strictly needed, but nice for analysis)
   local/language-scores/de/posts-de-by-thread.tsv.gz
   ```

4. extract submissions and comments from raw data (done separately so we can easily multiprocess)
   ```
   python3 scripts/threads-extract.py
   ```
   this creates
   ```
   local/languages/de-posts/R[CS]_{YYYY}-{MM}.ldjson.gz
   ```

5. collect and build XML texts and TSV table of meta data
   ```
   python3 scripts/threads-process.py
   ```
   this creates
   ```
   local/languages/de-gerede.xml.gz
   local/languages/de-gerede.tsv.gz
   ```
   Note that this needs a couple hundred gigabytes of RAM.
   
6. annotation with SoMaJo + SoMeWeTa:
   ```
   somajo-tokenizer --xml --split_sentences --sentence-tag s --tag p --parallel 20 local/languages/de-gerede.xml | somewe-tagger --xml --sentence-tag s --parallel 20 --tag local/german_newspaper_2020-05-28.model - > local/languages/de-gerede.vrt
   ```
        
7. cohorting for CQPweb
   **TODO** `threads-process.py` should already create an XML file compatible with CQPweb
   ```
   python3 scripts/vrt-cohorting.py
   ```
   also, this needs my private `cwb-vrt` suite


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
