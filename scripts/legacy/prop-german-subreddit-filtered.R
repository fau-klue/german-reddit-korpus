#!/usr/bin/env Rscript

# Philipp Heinrich, 2022

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(tidyverse))

parser <- ArgumentParser()
parser$add_argument("--glob_in",
                    help = "glob to thread statistics",
		    default = "local/language-scores/comments/*de-per-thread.tsv.gz")
parser$add_argument("--path_subreddit",
                    help = "path to subreddit statistics",
		    default = "local/language-scores/RC-de-per-subreddit.tsv.gz")
parser$add_argument("--path_out",
                    help = "path to output",
		    default = "local/language-scores/RC-de-per-thread-subreddit-filtered.tsv.gz")
args <- parser$parse_args()

modus <- function(x) {
  # use the mode for subreddit of thread, since threads can span over different subreddits (?)
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

# subreddit filter
print("reading subreddit statistics")
german.subreddits <- fread(args$path_subreddit) %>%
  mutate(keep = confidence > (exp(-sqrt(n)/4) + .1)) %>% 
  filter(keep) %>% 
  pull(subreddit)
print(str_c("keeping ", as.character(length(german.subreddits)), " subreddits"))

# input files
paths <- Sys.glob(args$glob_in)
print(str_c("collected ", as.character(length(paths)), " files"))

d <- tibble()
for (p in paths){
  print(p)
  tmp <- fread(p) %>%
    filter(subreddit %in% german.subreddits)
  print(str_c("number of threads: ", as.character(nrow(tmp))))
  d <- rbind(d, tmp)
}

d <- d %>% group_by(link_id) %>%
  summarise(subreddit = modus(subreddit),
            confidence = weighted.mean(confidence, length),
            length = sum(length),
            n = sum(n)) %>%
  arrange(desc(confidence)) %>%
  replace_na(list(confidence = 0)) %>%
  write_tsv(args$path_out)
