# Preprocessing — from the Kaggle leak to the analysis datasets

How to take the original Iron March dataset, clean it up the way the
thesis did, and then run the R analysis notebook on it. Three stages:

1. **Get the data** — download the original export from Kaggle.
2. **Clean it** — run `analysis/iron_march_analysis.Rmd`, which turns the
   six raw files into the cleaned datasets.
3. **Anonymise it** (optional, for publishing) — the step that produced
   the shareable files in `data/`.

## 1. Get the original dataset

The original dataset is [Iron March 'Fascist Social Network'
Dataset](https://www.kaggle.com/davidpham/iron-march-fascist-social-network-dataset)
(David Pham, Kaggle, 2019): 99 CSV files, 251 MB, from the November
2019 leak of the forum's database. You need a free Kaggle account to
download it. Download the zip and extract it.

You only need six of the 99 files:

| File | What it is |
|---|---|
| `core_members.csv` | Member records (1,207 members): IDs, names, email addresses, join/last-visit/last-activity timestamps, post counts |
| `core_message_posts.csv` | Text of private-message replies (20,513 with text): message ID, topic ID, author ID, date, text |
| `core_message_topics.csv` | Private-message threads: thread ID, title, starter ID, recipient ID, dates, reply counts |
| `core_search_index.csv` | Forum posts and comments (the search index): item IDs, titles, content, author IDs, dates |
| `core_moderator_logs.csv` | Moderator log: who became a moderator, when |
| `core_admin_logs.csv` | Admin log: admin actions by member |

The other 93 files (calendars, attachments, caches, settings tables)
are not used by the analysis.

## 2. Set up R

The notebook was written against R 4.1 and RStudio 2021.09.1. It
needs these packages — install them first:

```r
install.packages(c("tidyverse", "igraph", "sqldf", "lubridate",
  "ggplot2", "ggpubr", "car", "psych", "gmodels", "anytime",
  "hrbrthemes", "gridExtra", "grid", "forcats", "plyr",
  "formattable", "quanteda", "CINNA", "ggraph", "tidygraph"))
```

The four that do most of the work are `tidyverse`, `igraph`, `sqldf`
and `lubridate`; the rest are for specific plots and tests. A few of
these have moved or been archived since 2022 — if one won't install
on current R, that is the known risk with a 2022 notebook (see
"What won't reproduce exactly" below).

Then:

1. Make a working folder and put the six CSVs in it.
2. Copy `analysis/iron_march_analysis.Rmd` into the same folder.
   The notebook reads its inputs by bare filename, with no paths, so
   everything must sit next to it.
3. Also copy `data/2016_mentions.csv` from this repo into the folder —
   the notebook reads it at line 4427 for the "Mentions of Key Events"
   chart, and it is not on Kaggle (it is a summary table made during
   the analysis; see `data/DATA_DICTIONARY.md`).
4. Open the `.Rmd` in RStudio, set the working directory to that
   folder (Session → Set Working Directory → To Source File
   Location), and run it — Run All, or Knit to HTML.

It is 4,784 lines; knitting takes a while. The derived datasets it
writes land in the working directory as it goes.

## 3. What the notebook does — the cleaning, in order

Line numbers refer to `analysis/iron_march_analysis.Rmd`. The
section-by-section guide in `analysis/README.md` covers the whole
notebook; this is the cleaning part only (lines 46–2252).

1. **Load (L40–43).** Reads the six files into `iron_march_core_*`
   data frames.
2. **Post titles (L46–69).** The forum-posts file has no titles on
   every row, so a SQL query pulls the distinct post titles
   (`index_class = 'IPS\forums\Topic\Post'`, blank titles dropped)
   and matches them back onto the posts by item ID.
3. **Dates (L73–145).** Every timestamp in the export is a Unix epoch
   number. They are converted Epoch → POSIXct (GMT) and then into
   half-year buckets with `lubridate::semester(with_year = TRUE)` —
   the `2016.2` / `2017.1` halves used throughout the thesis. Applied
   to members (joined, last visit, last activity), message dates,
   topic dates and post dates.
4. **Text cleanup and names (L403–470).** HTML clutter is stripped
   from message text and post content (`</p>`, `<p>`, newlines, tabs).
   Member names are joined onto messages and topics by member ID.
5. **Keyword labelling (L403–588).** Users are labelled by keyword —
   terrorist groups, recruiters, moderators. The keyword lists are in
   the notebook; the labelled subsets are written out as the
   `*_keywords_*` and `*_recruitment_*` files in the table below.
6. **Private-message merge (L589–665).** Topics are joined to posts
   on `msg_topic_id`. Two cases are handled separately — messages
   where the sender is the thread's recipient, and messages where
   they are not — then bound together into
   `iron_march_core_message_all3.csv`. This is the step that gives
   every private message a sender and a receiver.
7. **The thread-4445 fix (L843–964).** After thread 4445 the receiver
   IDs in the export are wrong: sender and receiver are the same
   person. The notebook finds the correct receivers from matching
   rows and swaps them in. Without this fix, the 2016-onwards
   private-message data is largely lost.
8. **Moderators and admins (L1129–1200).** The log files are read;
   `member_id` 0 is dropped (an error in the export — that member
   does not exist). Log timestamps become dates and half-year
   buckets; the first moderator date per member is taken and joined
   into the members table. The notebook's own note: 650 moderators
   over the forum's life, 29% of members by the end.
9. **Members table (L1466).** `iron_march_members.csv` — the cleaned
   members table with roles attached.
10. **Private-message dataset (L1597).**
    `iron_march_private_messages.csv` — the restored private-message
    dataset: every message with sender, receiver, date and half.
11. **Comments and posts (L1740).**
    `iron_march_comments_posts.csv` — the cleaned forum posts and
    comments.
12. **Nodes and edges (L1872–2252).** The node list
    (`iron_march_nodes.csv`, plus a Gephi version) and three edge
    lists — member comments → posts/topics, post author → posts/topics,
    and private messages member → member — merged into one final edge
    list (`iron_march_edges.csv`, plus Gephi and NetworkX versions).
    This is also where the NetworkX `.txt` edge lists are written out
    — the files the resilience and contagion experiments consumed.
13. **Alpha scores (L2343).** `alpha_network_scores.csv` is written by
    the notebook mid-run, then read back for the centrality analysis.

## 4. What you get — the derived datasets

Files the notebook writes into the working directory:

| File | What it is |
|---|---|
| `iron_march_core_message_all3.csv` | All private messages with sender and receiver identified |
| `iron_march_terrorist_keywords_messages.csv` | Messages matching terrorist-group keywords |
| `iron_march_recruitment_messages.csv` | Messages matching recruitment keywords |
| `iron_march_terrorist_keywords_comments.csv` | Comments matching terrorist-group keywords |
| `iron_march_recruitment_comments.csv` | Comments matching recruitment keywords |
| `iron_march_keywords_posts.csv` | Posts matching the keyword lists |
| `iron_march_recruitment_posts.csv` | Posts matching recruitment keywords |
| `iron_march_members.csv` | Cleaned members table, with roles |
| `iron_march_private_messages.csv` | Restored private-message dataset |
| `iron_march_comments_posts.csv` | Cleaned forum posts and comments |
| `iron_march_nodes.csv` | Node list for the network (+ `iron_march_nodes_gephi.csv` for Gephi) |
| `iron_march_edges.csv` | Merged edge list (+ Gephi and NetworkX versions) |
| `iron_march_edges_networkx.csv` | Edge list for the NetworkX experiments |
| `iron_march_edges_networkx_resilience.txt`, `iron_march_edges_networkx_contagion.txt`, `iron_march_edges_networkx_contagion_comments.txt`, `iron_march_edges_networkx_contagion_all_edges.txt` | Weighted edge lists for the resilience and contagion experiments |
| `alpha_network_scores.csv` | Alpha centrality scores, written mid-run |
| `mods_steps_out_df.csv` | Moderator step counts |
| `insurrectionist_messages.csv` | Messages from the insurrectionist deep dive |
| `trivial_haps.csv` | "Trivial HAPPENINGs" post data |

(Three more writes are commented out in the notebook and not
produced: the cleaned forum-posts file, the completed message file,
and the Liberal Degeneration / National Action / Trivial HAPPENINGs /
TRUMP subsets.)

## 5. Then the analysis runs

Once the cleaning is done, the rest of the notebook (L2253 onward)
builds the network with `graph_from_data_frame` (7,415 nodes,
187,140 edges), computes centrality (degree, betweenness, closeness,
alpha), runs the change-over-time tests, and produces the figures.
`analysis/README.md` is the section-by-section guide to all of it.

The disruption experiments (resilience, simple and complex contagion)
were run separately in Jupyter/NetworkX from the `.txt` edge lists
above — they are not in the R notebook.

## 6. Anonymising — to publish like this repo

The shareable files in `data/` were made from the cleaned outputs
with `scripts/anonymise.py`: identifiers replaced with salted SHA-256
hashes, email addresses, usernames, message text and thread titles
removed entirely, exact timestamps already in half-year buckets.
`scripts/verify.py` checks the outputs (15 checks: row counts,
hash consistency, no leaked emails, usernames, message text or
timestamps). Full detail in `data/DATA_DICTIONARY.md`.

The salt is held privately and is **not** in this repository — without
it the hashes cannot be reversed. Never commit the raw Kaggle files,
the cleaned files with message text, or the salt: `.gitignore`
covers `raw/` and `salt.txt`.

## What won't reproduce exactly

- **Modularity.** The thesis reports Mod(N) = 0.310 (Gephi); the
  notebook's walktrap computation gives 0.267. Same method family,
  different implementation — don't expect an exact match on that one
  number.
- **R and package versions.** The notebook was written against R 4.1
  (RStudio 2021.09.1). Some packages have moved or been archived
  since 2022; if one won't install, that is the risk with a 2022
  notebook, not a problem with the data.
- **The 2016 chart** needs `2016_mentions.csv` from `data/` — it is
  included in this repo, but it is not on Kaggle.
