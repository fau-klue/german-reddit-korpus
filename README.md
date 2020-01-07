# GeRedE: A Corpus of German Reddit Exchanges
GeRedE is a 270 million token German CMC corpus containing
approximately 380,000 submissions and 6,800,000 comments posted on
[Reddit](https://www.reddit.com) between 2010 and 2018. Reddit is a
popular online platform combining social news aggregation, discussion
and micro-blogging. The CWB-indexed version of our final corpus is
available to registered academic users via
[CQPweb](https://corpora.linguistik.uni-erlangen.de/cqpweb/gerede_v1)

This repository contains the scripts we used to extract German
submissions and comments from the vast amount of data Jason
Baumgartner provides at https://files.pushshift.io/reddit. It also
contains the IDs of all submissions and comments included in our
corpus, so that those who wish to recreate our corpus are not required
to run all processing steps by themselves.

## Steps for Recreating the Corpus
1. download raw data from https://files.pushshift.io/reddit
   - it is recommended, though not necessary, to re-compress all files
   into gzip or bz2 format
2. run `extract-german-comments.py` on the raw comments and
   `extract-german-comment-ids.py` on the thus created
   `*-de.ldjson.gz`
   - this will identify comments that are most likely German
3. run `prop_german.R` on the directory containing the `*-lang.tsv.gz`
   files created in the second step
   - for each month, this will compute the proportion of German
     comments in each subreddit containing at least one German
     comment
4. run `subreddits.R` on the directory containing the
   `*-german_subreddits_prop.csv` files created in the previous step
   - creates `stats.csv`: statistics for all subreddits and months
   - creates `stats_filtered.csv`: subreddit filter; retains only
     subreddits where the proportion of comments classified as German
     is above the dynamic threshold (see paper for details)
5. run `threads-extract-ids.py` on `*-de.ldjson.gz`
   - this will extract all threads IDs with at least one German
     comment
6. run `threads-extract.py` on the thus created
   `*-thread-ids.tsv.gz` and the raw comments
   - this will extract all comments of threads that contain at least
     one German comment
7. run `threads-sort.py` on the thus created `*-de-threads.ldjson.gz`,
   saving the output in `threads-all.ldjson.gz`
   - this will sort the comments into threads
8. run `threads-language.py` on `stats_filtered.csv.gz`,
   `data/german-comment-ids.txt.gz` and the above created
   `threads-all.ldjson.gz`, saving the results in
   `threads-filtered.ldjson.gz` and the scores in
   `threads-all-lang-scores.tsv.gz`
   - this will filter out German threads with our combined approach
     (see paper for details)
9. run `threads-add-submissions.py` on the raw submissions and the
   `threads-all-lang-scores.tsv.gz`
   - this will filter out all submissions of German threads
10. *TODO* annotate all German comments and submissions
11. *TODO* run `build-vrt.py`

## Shortcuts
NB: the output files of the following steps can be found in the
`data/` sub-folder:
- step 2 (`german-comment-ids.txt.gz`)
- step 4 (`stats_filtered.csv.gz`)
- step 8 (`threads-all-lang-scores.tsv.gz`)

 
## Additional Files
- `data/thread-lang-annotated.tsv.gz` contains a manually annotated
  stratified sample of threads
