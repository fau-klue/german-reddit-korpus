#!/usr/bin/env Rscript

# Philipp Heinrich, 2022

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(tidyverse))

parser <- ArgumentParser()
parser$add_argument("glob_in",
                    help = "glob to input files")
parser$add_argument("path_subreddit",
                    help = "glob to input files")
parser$add_argument("path_out",
                    help = "path to output")
args <- parser$parse_args()

modus <- function(x) {
  # use the mode for subreddit of thread, since threads can span over different subreddits (?)
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

# subreddit filter
german.subreddits <- read_tsv(args$path_subreddit, col_types = "cddd") %>%
  mutate(keep = confidence > (exp(-sqrt(n)/4) + .1)) %>% 
  filter(keep) %>% 
  pull(subreddit)

paths <- Sys.glob(args$glob_in)
print(str_c("collected ", as.character(length(paths)), " files"))

d <- tibble()
for (p in paths){
  print(p)
  tmp <- fread(p, col_types = "ccddd") %>%
    filter(subreddit %in% german.subreddits)
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
