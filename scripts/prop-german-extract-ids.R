library(tidyverse)
library(girafe)

d <- read_tsv("../local/RC-lang-de-per-thread-subreddit-filtered.tsv.gz") %>%
  drop_na()

d %>% ggplot(aes(x = confidence)) + 
  geom_histogram()

d %>% ggplot(aes(x = log(length))) + 
  geom_histogram()

d %>% filter(confidence > .01, length > 100) %>%
  ggplot(aes(x = log(length), y = confidence)) + 
  geom_point()

d %>% filter(confidence > .1) %>%
  pull(link_id) %>%
  write("german-thread-ids.txt.gz")
