# GeRedE: A Corpus of German Reddit Exchanges #

[Reddit](https://www.reddit.com) is a popular online platform combining social news aggregation, discussion and micro-blogging. GeRedE is a German CMC corpus containing all German threads posted on Reddit. The current version (v2) comprises all posts from the very first in 2005 until December 31, 2022.

- The CWB-indexed version of our final corpus is available to registered academic users via [CQPweb](https://corpora.linguistik.uni-erlangen.de/cqpweb/gerede_v2).
- We also provide the filtered and sorted raw data via our [web server](https://corpora.linguistik.uni-erlangen.de/data/de-gerede.ldjson.gz).  Each line is an array representing one thread, i.e. a list of the submission and corresponding comments represented as JSON objects (just as in the raw data on pushshift).  Threads are sorted by time – the first element of the array is thus usually the submission.

The repository at hand contains the scripts we used to extract German threads from the vast amount of data Jason Baumgartner provides at [pushshift](https://files.pushshift.io/reddit) and to convert them into XML/VRT (which is the input format for CWB/CQPweb).


## Dependencies and Resources ##

Install all python3 [requirements](requirements.txt); we recommend using a virtual environment:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Additionally, you will need the [fasttext model](https://fasttext.cc/docs/en/language-identification.html) for language classification.  By default, the scripts assume it is located at `local/lid.176.bin`.

In order to run the R script (step 3), you will need the following libraries:

    argparse
    data.table
    R.utils
    tidyverse
    tidytable
    
For POS annotation (see step 7), you will need the German Web and Social Media [model](https://corpora.linguistik.uni-erlangen.de/someweta/german_web_social_media_2020-05-28.model) of [SoMeWeTa](https://github.com/tsproisl/SoMeWeTa).  By default, the scripts assume it is located at `local/german_web_social_media_2020-05-28.model`.

## Language Classification ##

1. download the raw data from [pushshift](https://files.pushshift.io/reddit)
   - you need both comments and submissions (from the respective subdirectories)
   - put them into `local/raw/comments/` and `local/raw/submissions/` respectively
   - filenames have to start with `RC` (Reddit Comments) and `RS` (Reddit Submissions)

2. classify texts (`comment['body']` and `submission['title']` + `submission['selftext']`) by language
   ```
   python3 scripts/classify-languages.py
   ```
   this creates one file per input file
   ```
   local/languages/scores/R(C|S)_{YYYY}-{MM}.tsv.gz
   ```
   which comprises the most likely language and confidence of each comment/submission alongside IDs and some meta data

   script arguments:
   - to change the input paths:
     `--glob_in "local/raw/*/R*"`
   - to change the output directory:
     `--dir_out "local/languages/scores/"`
   - to change the path to the language model:
     `--model "local/lid.176.bin"`
   - to change the number of process to spawn:
     `--nr_proc 12`

## Determine and filter out German threads ##

3. aggregate language scores (here: for German, see script arguments for other languages) by thread and by subreddit
   ```
   Rscript scripts/filter-relevant.R
   ```
   this creates monthly aggregates
   ```
   local/languages/de/monthly/R[CS]_{YYYY}-{MM}-by-subreddit.tsv.gz
   local/languages/de/monthly/R[CS]_{YYYY}-{MM}-by-thread.tsv.gz
   ```
   as well as global scores
   ```
   local/languages/de/scores-by-subreddit.tsv.gz  # not strictly needed, but nice for analyses
   local/languages/de/scores-by-thread.tsv.gz     # used for filtering out threads
   ```

   script arguments:
   - to change the language of the posts to filter out, use the corresponding ISO 639-1 code:
     `--lang "de"`
   - to change the input paths:
     `--glob_in "local/languages/monthly/*.tsv.gz"`
   - to change the output directory:
     `--dir_out "local/languages/de/monthly/"`
   - to overwrite existing files in the output directory, use the flag `-o` (by default, the program won't overwrite files, so you can restart it and continue the process without losing data if it runs out of memory)
   - if you only want to redo the filtering process after the files for individual months have already been created, you can skip this first step using the flag `-s` (probably together with `-o`)

4. extract submissions and comments from raw data and sort by threads
   ```
   python3 scripts/extract-threads.py
   ```
   this creates a file for each month
   ```
   local/languages/de/monthly/R[CS]_{YYYY}-{MM}.ldjson.gz
   ```
   and a final file
   ```
   local/languages/de/gerede.ldjson.gz
   ```
   which comprises all threads classified as German.
   
   script arguments:
   - to change the paths to raw data:
     `--glob_raw "local/raw/*/R*"`
   - to change the path to relevant thread IDs:
     `--path_ids "local/languages/de/scores-by-thread.tsv.gz"`
   - to change the output path:
     `--path_out "local/languages/de/gerede.ldjson.gz"`
   - to change the output directory for monthly data:
     `--dir_out "local/languages/de/monthly/"`
   - to change the number of process to spawn:
     `--nr_proc 12`

## Linguistic Annotation (.vrt) ##

5. build XML file (meta data and texts) and a separate TSV table of all thread meta data
   ```
   python3 scripts/convert-ldjson.py
   ```
   this creates
   ```
   local/languages/de/gerede.xml.gz
   local/languages/de/gerede.tsv.gz
   ```
   
   arguments:
   - to change the input path:
     `--path_in "local/languages/de/gerede.ldjson.gz"`
   - to change the output path for XML file:
     `--path_xml "local/languages/de/gerede.xml.gz"`
   - to change the output path for TSV file:
     `--path_tsv "local/languages/de/gerede.tsv.gz"`
   
6. tokenise and pos-tag with SoMaJo + SoMeWeTa (on unzipped data):
   ```
   somajo-tokenizer --xml --split_sentences --sentence-tag s --tag p --parallel 12 local/languages/de/gerede.xml | somewe-tagger --xml --sentence-tag s --parallel 12 --tag local/german_web_social_media_2020-05-28.model - > local/languages/de/gerede.vrt
   ```


## References ##

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
