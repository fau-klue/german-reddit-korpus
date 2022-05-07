#!/usr/bin/env Rscript

# Philipp Heinrich, 2022

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(tidyverse))

parser <- ArgumentParser()
parser$add_argument("glob_in",
	            help = "glob to input files",
                    default = "/cip/corpora/Web/Reddit/raw/comments")
parser$add_argument("-o", "--overwrite",
                    action = "store_true",
                    help = "overwriting existing files?",
                    default = FALSE)
args <- parser$parse_args()

modus <- function(x) {
  # use the mode for subreddit of thread, since threads can span over different subreddits (?)
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

aggregate.stats <- function(path.in){

  # paths to save results to
  path.subreddit <- str_replace(path.in, "-lang.tsv.gz", "-lang-per-subreddit.tsv.gz")
  path.thread <- str_replace(path.in, "-lang.tsv.gz", "-lang-per-thread.tsv.gz")

  cat(str_flatten(rep("=", 80)), "\n")
  cat("- input:", path.in, "\n")
  cat("- subreddits:", path.subreddit, "\n")
  cat("- threads:", path.thread, "\n")

  if ((file.exists(path.subreddit) | file.exists(path.thread)) & ! args$overwrite){
    cat("WARNING: at least one of the output-files already exists\n")
    cat(str_flatten(rep("=", 80)), "\n")
    return()
  }

  cat(str_flatten(rep("=", 80)), "\n")

  cat("- reading\n")
  d <- fread(path.in, 
             select = c("link_id", "subreddit", "language", "confidence", "length")) %>%
    drop_na() %>% 
    mutate(confidence = ifelse(language == '__label__de', confidence, 0))

  cat("- summarizing subreddits\n")
  d %>% 
    group_by(subreddit) %>% 
    summarise(confidence = weighted.mean(confidence, length), 
              length = sum(length), 
              n = n()) %>%
    write_tsv(path.subreddit)

  cat("- summarizing threads\n")
  d %>% 
    group_by(link_id) %>% 
    summarise(subreddit = modus(subreddit),
              confidence = weighted.mean(confidence, length), 
              length = sum(length), 
              n = n()) %>%
    write_tsv(path.thread)

  cat(str_flatten(rep("=", 80)), "\n")
}

paths <- Sys.glob(args$glob_in)
for (p in paths){
  aggregate.stats(p)
}
