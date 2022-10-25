# GeRedE: A Corpus of German Reddit Exchanges
GeRedE is a xxx million token German CMC corpus containing approximately xxx submissions and xxx comments posted on [Reddit](https://www.reddit.com) between 2010 and mid-2021. Reddit is a popular online platform combining social news aggregation, discussion and micro-blogging. The CWB-indexed version of our final corpus is available to registered academic users via [CQPweb](https://corpora.linguistik.uni-erlangen.de/cqpweb/gerede_v2)

This repository contains the scripts we used to extract German submissions and comments from the vast amount of data Jason Baumgartner provides at https://files.pushshift.io/reddit. It also contains the IDs of all submissions and comments included in our corpus, so that those who wish to recreate our corpus are not required to run all processing steps by themselves.

## Dependencies

Install all Python dependencies e.g. using the provided `Pipfile`. 

In order to run the R scripts, you will need the following libraries:

    argparse
    data.table
    R.utils
    tidyverse

You will need the German [dictionary](https://pyenchant.github.io/pyenchant/install.html#installing-a-dictionary) for `pyenchant` and that this dictionary is named `hunspell-de-de`.  On Ubuntu, you can run

    sudo apt install hunspell-de-de


## Steps for Recreating the Corpus

1. download the raw data
   - you need both comments and submissions (from the respective subdirectories)
   - https://files.pushshift.io/reddit
   - put them into `local/raw/comments/` and `local/raw/submissions/` respectively

2. classify comments by language
   ```
   python3 scripts/lang-classify-comments.py
   ```
   by default, this creates two files, one with scores for every language and one with scores for likely German comments
   ```
   local/language-scores/comments/RC_{YYYY}-{MM}-lang.tsv.gz
   local/language-scores/comments/RC_{YYYY}-{MM}-de.tsv.gz
   ```
   NB: you can use `--lang` to modify which languages should be extracted
   
3. aggregate language scores (for German) monthly per thread and per subreddit
   ```
   Rscript scripts/prop-german-monthly.R
   ```
   this creates
   ```
   local/language-scores/comments/RC_{YYYY}-{MM}-de-per-subreddit.tsv.gz
   local/language-scores/comments/RC_{YYYY}-{MM}-de-per-thread.tsv.gz
   ```

4. aggregate across months per thread and per subreddit
   ```
   Rscript scripts/prop-german-complete.R
   ```
   this creates
   ```
   local/language-scores/RC-de-per-subreddit.tsv.gz
   ```

5. filter threads based on subreddit language scores
   ```
   Rscript scripts/prop-german-subreddit-filtered.R
   ```
   this creates
   ```
   local/language-scores/RC-de-per-thread-subreddit-filtered.tsv.gz
   ```

6. extract submissions and comments from raw data
   ```
   python3 scripts/threads-extract.py
   ```
   this creates
   ```
   local/filtered-de/R(C|S)_{YYYY}-{MM}-de.ldjson.gz
   ```

# TODO
7. sort into threads
   ```
   python3 scripts/threads-sort.py "raw/comments/RC_{YYYY}-{MM}-lang-de.ldjson.gz" 
   ```

8. convert to XML and meta data
   ```
   python3 scripts/threads-to-xml.py "raw/comments/RC_{YYYY}-{MM}-lang-de.ldjson.gz"
   ```
   this creates
   ```
   raw/comments/RC_{YYYY}-{MM}-lang-de.tsv.gz
   raw/comments/RC_{YYYY}-{MM}-lang-de.xml.gz
   ```

9. build corpus


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
