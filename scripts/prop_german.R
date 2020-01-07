#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)

# For each month, compute the proportion of "German" comments
# in each subreddit
# 
# Usage: ./prop_german.R <path to directory with *lang.tsv.gz files>
# <output directory> <optional: TRUE or 1 if existing output files
# should be overwritten>
#
# Calling the script with just one parameter will write output
# files to the input directory. Calling it without any parameters
# will assume the default directory specified below.
# 
# 
# Andreas Blombach, 2019

library(tidyverse)
library(data.table)

overwrite <- FALSE
if(length(args) == 0) {
  # default directory:
  path_in <- "/cip/corpora/Web/Reddit/raw/incoming/comments"
  path_out <- path_in
  msg <- str_c("No input/output directory specified, using ",
               path_in, "/ as default for both.")
  print(msg)
} else if (length(args) == 1) {
  path_in <- str_remove(args[1], "/$")
  path_out <- path_in
  msg <- str_c("Using ", path_in, "/ as the directory for both
               input and output.")
} else {
  path_in <- str_remove(args[1], "/$")
  path_out <- str_remove(args[2], "/$")
  
  if (length(args) >= 3) {
    overwrite <- as.logical(args[3])
  }
}

files <- list.files(path_in,
                    pattern = "*lang.tsv.gz",
                    full.names = FALSE)

for (file in files) {
  path <- path_out %>% str_c("/", file) %>%
    str_extract(".+(?=-)") %>%
    str_c("-german_subreddits_prop.csv")
  if (!file.exists(path) || overwrite == TRUE) {
    comments <- fread(str_c(path_in, "/", file),
                      na.strings = "None",
                      col.names = c("id", "subreddit", "german"))
    comments <- comments[, .(.N), by = .(subreddit, german)]
    comments[, c("total", "prop") := .(sum(N), N / sum(N)), by = subreddit]
    comments <- comments[german == TRUE][order(-N, -prop)]
    fwrite(comments, path)
    print(str_c(path, " created."))
  } else {
    print(str_c(path, " already exists. Skipping ", file, "."))
  }
}