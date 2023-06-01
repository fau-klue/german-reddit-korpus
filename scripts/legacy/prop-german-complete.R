#!/usr/bin/env Rscript

# Philipp Heinrich, 2022

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(tidyverse))

parser <- ArgumentParser()
parser$add_argument("--glob_in",
                    help = "glob to input files",
		    default = "local/language-scores/comments/*de-per-subreddit.tsv.gz")
parser$add_argument("--path_out",
                    help = "path to output",
		    default = "local/language-scores/RC-de-per-subreddit.tsv.gz")
args <- parser$parse_args()

modus <- function(x) {
  # use the mode for subreddit of thread, since threads can span over different subreddits (?)
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

paths <- Sys.glob(args$glob_in)

print(str_c("collected ", as.character(length(paths)), " files"))

d <- tibble()
for (p in paths){
  print(p)
  d <- rbind(d, read_tsv(p, show_col_types = F))
}

var <- colnames(d)[1]

print(str_c("grouping by: ", var))

if (var == "subreddit"){
  d <- d %>% group_by(!!sym(var)) %>%
    summarise(confidence = weighted.mean(confidence, length), 
              length = sum(length), 
              n = sum(n)) %>%
    arrange(desc(confidence)) %>%
    replace_na(list(confidence = 0)) %>%
    write_tsv(args$path_out)
} else if (var == "link_id"){
  d <- d %>% group_by(!!sym(var)) %>%
    summarise(subreddit = modus(subreddit),
              confidence = weighted.mean(confidence, length), 
              length = sum(length), 
              n = sum(n)) %>%
    arrange(desc(confidence)) %>%
    replace_na(list(confidence = 0)) %>%
    write_tsv(args$path_out)
} else {
  print("wrong grouping variable")
}