#!/usr/bin/env Rscript

# Andreas Blombach & Philipp Heinrich, 2023

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(tidytable))

parser <- ArgumentParser()
parser$add_argument("--glob_in",
                    help = "glob to input files (in quotation marks)",
                    default = "local/languages/scores/*.tsv.gz")
parser$add_argument("--dir_out",
                    help = "directory in which to store output files",
                    default = "local/languages/de/")
parser$add_argument("--lang",
                    help = "ISO 639-1 code of the language you're interested in",
                    default = "de")
parser$add_argument("-o", "--overwrite",
                    action = "store_true",
                    help = "overwrite existing files?",
                    default = FALSE)
parser$add_argument("-s", "--skip1",
                    action = "store_true",
                    help = "skip first step (if output files for individual months already exist)",
                    default = FALSE)
args <- parser$parse_args()

aggregate_stats <- function(path_in, dir_monthly, language){

  label <- str_c("__label__", language)

  # paths to save results to
  file_name <- basename(path_in)
  path_out <- file.path(dir_monthly, file_name)
  path_subreddit <- str_replace(path_out, ".tsv.gz", "-by-subreddit.tsv.gz")
  path_thread <- str_replace(path_out, ".tsv.gz", "-by-thread.tsv.gz")
  
  cat(str_dup("=", 80), "\n")
  cat("- input:", path_in, "\n")
  cat("- subreddits:", path_subreddit, "\n")
  cat("- threads:", path_thread, "\n")

  if ((file.exists(path_subreddit) | file.exists(path_thread)) & !args$overwrite) {
    cat("WARNING: at least one of the output-files already exists. Use '-o' to overwrite existing files.\n")
    cat(str_dup("=", 80), "\n")
    return()
  }

  cat(str_dup("=", 80), "\n")

  cat("- reading\n")
  d <- fread.(path_in,
              select = c("link_id", "id", "created_utc", "subreddit", "language", "confidence", "length")) |>
    mutate.(link_id = ifelse.(is.na(link_id), str_c("t3_", id), link_id)) |> # for submissions
    drop_na.() |> 
    mutate.(confidence = ifelse.(length == 0, NA, ifelse.(language == label, confidence, 0)))

  cat("- summarising threads\n")
  d <- d |>
    arrange.(created_utc) |>
    summarise.(subreddit = last(subreddit), # a few comments belong to the same thread, but to different subreddits; apparently, this can happen when a thread is moved to another subreddit after the first comments have already been collected by pushshift
               confidence = weighted.mean(confidence, log(length), na.rm = TRUE), # log(length), otherwise individual very long posts can have undue influence
               length = sum(length),
               n = n(),
               .by = link_id)
  
  d |>
    write_tsv(path_thread)
  
  cat("- summarising subreddits\n")
  d |> 
    summarise.(confidence = weighted.mean(confidence, log(length), na.rm = TRUE),
               length = sum(length),
               n = n(),
               .by = subreddit) |>
    write_tsv(path_subreddit)

  cat(str_dup("=", 80), "\n")
  gc()
}


iso_codes_str <- "af als am an ar arz as ast av az azb ba bar bcl be bg bh bn bo bpy br bs bxr ca cbk ce ceb ckb co cs cv cy da de diq dsb dty dv el eml en eo es et eu fa fi fr frr fy ga gd gl gn gom gu gv he hi hif hr hsb ht hu hy ia id ie ilo io is it ja jbo jv ka kk km kn ko krc ku kv kw ky la lb lez li lmo lo lrc lt lv mai mg mhr min mk ml mn mr mrj ms mt mwl my myv mzn nah nap nds ne new nl nn no oc or os pa pam pfl pl pms pnb ps pt qu rm ro ru rue sa sah sc scn sco sd sh si sk sl so sq sr su sv sw ta te tg th tk tl tr tt tyv ug uk ur uz vec vep vi vls vo wa war wuu xal xmf yi yo yue zh"
iso_codes <- iso_codes_str |>
  str_split(" ") |>
  unlist()
if (!args$lang %chin% iso_codes) {
  stop("'", args$lang, "' is not in the list of supported languages. Use one of the following:\n", iso_codes_str)
}

if (!str_detect(args$glob_in, "\\.tsv\\.gz$")) {
  stop("The glob pattern ", args$glob_in , " for the input file(s) needs to end in '.tsv.gz'. If you need to know more about glob patterns, please see https://en.wikipedia.org/wiki/Glob_(programming).")
}

if (!dir.exists(args$dir_out)) {
  if (dir.create(args$dir_out, recursive = TRUE)) {
    cat("- created directory", args$dir_out, "\n")
  } else {
    stop("failed to create directory ", args$dir_out, ". Do you have the necessary rights?")
  }
}

dir_monthly <- file.path(args$dir_out, "monthly")
if (!dir.exists(dir_monthly)) {
  if (dir.create(dir_monthly, recursive = TRUE)) {
    cat("- created directory", dir_monthly, "\n")
  } else {
    stop("failed to create directory ", dir_monthly, ". Do you have the necessary rights?")
  }
}

# Step 1: two summary statistic files for each input file (submissions or
# comments), grouped by subreddit and thread
if (!args$skip1) {
  paths <- Sys.glob(args$glob_in)
  cat(str_dup("=", 80), "\n")
  cat("Step 1: reading", length(paths), "files and creating file-wise summary statistics by subreddit and thread.\n")
  cat(str_dup("=", 80), "\n")
  
  for (p in paths){
    aggregate_stats(p, dir_monthly, args$lang)
  }
} else {
  cat(str_dup("=", 80), "\n")
  cat("Skipping step 1.\n")
  cat(str_dup("=", 80), "\n")
}


# Step 2: read all the subreddit files just created as a single tidytable
paths2 <- list.files(dir_monthly,
                     pattern = "-by-subreddit\\.tsv\\.gz$",
                     full.names = TRUE)
subreddits_out <- file.path(args$dir_out, str_c("scores-by-subreddit.tsv.gz"))
cat(str_dup("=", 80), "\n")
cat("Step 2: reading", length(paths2), "files and creating a single file containing statistics for all subreddits/profile pages.\n")
cat(str_dup("=", 80), "\n")

if (file.exists(subreddits_out) & !args$overwrite) {
  stop(subreddits_out, " already exists. Use '-o' to overwrite existing files.")
}

sr <- read_tsv(paths2, show_col_types = FALSE)
sr <- sr |> 
  summarise.(confidence = weighted.mean(confidence, log(length), na.rm = TRUE),
             length = sum(length),
             n = sum(n),
             .by = subreddit)
cat("- found ", sum(sr$n), " comments in ", nrow(sr)," different subreddits/profile pages.\n")
cat("- writing output to", subreddits_out, "\n")
sr |> write_tsv(subreddits_out)


# Step 3: read all the thread files individually, filter out threads in
# irrelevant subreddits, then combine into a single tidytable
paths3 <- list.files(dir_monthly,
                     pattern = "-by-thread\\.tsv\\.gz$",
                     full.names = TRUE)
threads_out <- file.path(args$dir_out, "scores-by-thread.tsv.gz")
cat(str_dup("=", 80), "\n")
cat("Step 3: reading", length(paths3), "files and creating a single file containing statistics for all threads in relevant subreddits.\n")
cat(str_dup("=", 80), "\n")

if (file.exists(threads_out) & !args$overwrite) {
  stop(threads_out, " already exists. Use '-o' to overwrite existing files.")
}

relevant_sr <- sr |>
  filter.(length >= 100, confidence > (exp(-sqrt(n)/4) + .015)) |> # 1.5 % is the old threshold from our paper
  pull(subreddit)
cat("- keeping threads from", length(relevant_sr), "different subreddits -- for now\n")

threads <- tibble()
for (p in paths3) {
  tmp <- fread(p) |>
    filter.(subreddit %chin% relevant_sr)
    cat("- number of potentially relevant threads in ", p, ": ", nrow(tmp), "\n", sep = "")
    threads <- threads |> bind_rows.(tmp)
}

cat("- summarising, filtering and writing output to", threads_out, "\n")
threads <- threads |>
  summarise.(confidence = weighted.mean(confidence, log(length), na.rm = TRUE),
             length = sum(length),
             n = sum(n),
             .by = c(subreddit, link_id)) |> # link_ids now appear to be unique
  left_join.(sr |> select.(subreddit, sr_confidence = confidence)) |>
  mutate.(score = confidence * sr_confidence) |>
  filter.(confidence >= .5 & # weighted thread confidence >= 0.5
            score >= .01 & # for subreddits with very low confidence, consider only high confidence threads
            length >= 25 & # only threads containing at least 25 characters
            # at least 2 comments in thread or,
            # if not a profile page, at least 1 comments or
            # at least 150 characters in a subreddit with a weighted confidence of at least 0.1:
            (n >= 3 | (!str_detect(subreddit, "^u_") & (n >= 2 | (length >= 150 & sr_confidence >= .1)))) &
            # filter out certain annoying subreddits (language-specific!):
            !subreddit %chin% c("removalbot", "newstweetfeed", "TheLetterH",
                                "subreddit_simulacrum", "GoodDuckPanels")) |>
  mutate.(threads = n(), .by = subreddit) |>
  # after applying all filters above, keep only subreddits with at least 10 threads:
  filter.(threads >= 10) |>
  arrange.(desc.(threads))

threads |>
  write_tsv(threads_out)

stats <- threads |>
  summarise.(posts = sum(n), threads = n(), .by = subreddit)

cat("- kept ", nrow(threads), " threads from ", nrow(stats)," different subreddits, containing ", sum(stats$posts)," posts in total\n")

cat(str_dup("=", 80), "\n")
cat("All done!\n")
cat(str_dup("=", 80), "\n")
