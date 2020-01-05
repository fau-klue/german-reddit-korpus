#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)

# Combine the output from prop_german.R into a single file,
# "stats.csv".
# 
# Furthermore, apply a filter to only consider subreddits where
# the proportion of comments classified as German is above the
# dynamic threshold: "stats_filtered.csv".
# 
# Usage: ./subreddits.R <path to directory with
# *-german_subreddits_prop.csv files> <output directory>
#
# Calling the script with just one parameter will write output
# files to the input directory. Calling it without any parameters
# will assume the default directories specified below.
# 
# 
# Andreas Blombach, 2019

library(tidyverse)

if(length(args) == 0) {
  # default directory:
  path_in <- "/cip/corpora/Web/Reddit/raw/incoming/comments"
  path_out <- "/cip/corpora/Web/Reddit/meta"
  msg <- str_c("No input/output directory specified, using ",
               path_in, "/ as default for input and ",
               path_out, "/ as default for output.")
  print(msg)
} else if (length(args) == 1) {
  path_in <- str_remove(args[1], "/$")
  path_out <- path_in
  msg <- str_c("Using ", path_in, "/ as the directory for both
               input and output.")
} else {
  path_in <- str_remove(args[1], "/$")
  path_out <- str_remove(args[2], "/$")
}

files <- list.files(path_in,
                    pattern = "*prop.csv",
                    full.names = TRUE)

all <- read_csv(files[1], col_types = "c____")
for (file in files) {
  subcorpus <- file %>% str_extract("RC.+(?=-)")
  new <- read_csv(file, col_types = "c_iid")
  names(new) <- c("subreddit",
                  str_c(subcorpus, "_N"),
                  str_c(subcorpus, "_total"),
                  str_c(subcorpus, "_prop"))
  all <- full_join(all, new, by = "subreddit")
}

all$corpus_N <- all %>% select(ends_with("_N")) %>% rowSums(na.rm = TRUE)
all$corpus_total <- all %>% select(ends_with("_total")) %>% rowSums(na.rm = TRUE)
all <- all %>% mutate(corpus_prop = corpus_N / corpus_total)
all <- all %>% select(subreddit, corpus_N, corpus_total, corpus_prop, everything())
all <- all %>% arrange(desc(corpus_N), desc(corpus_prop))

print(str_c("Trying to write ", path_out, "/stats.csv"))
write_csv(all, str_c(path_out, "/stats.csv"))


# Subreddit filter:
filtered <- all %>%
  filter(corpus_N > 1 &
           corpus_prop >= (exp(-sqrt(corpus_total) / 4) + .015))

print(str_c("Trying to write ", path_out, "/stats_filtered.csv"))
write_csv(filtered, str_c(path_out, "/stats_filtered.csv"))
