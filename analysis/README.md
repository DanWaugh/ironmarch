# Original R analysis — `iron_march_analysis.Rmd`

The original analysis notebook for the MSc thesis (TU Dublin, MSc Computer
Science — Data Science, 2021–2022). 4,784 lines of R Markdown that turn the
raw Iron March forum exports into the network, the centrality results and
the change-over-time tests reported in the thesis.

It is published here as written, with two small clean-ups only: the student
number was removed from the header, and a dead commented-out `setwd()` line
was dropped. Nothing else was changed.

## Running it

It reads the raw forum exports, which are **not** in this repo (they contain
email addresses, usernames and full private-message text) — download them
from the [Kaggle dataset](https://www.kaggle.com/davidpham/iron-march-fascist-social-network-dataset)
and place them next to this notebook:

- `core_members.csv`, `core_message_posts.csv`, `core_message_topics.csv`
- `core_admin_logs.csv`, `core_moderator_logs.csv`, `core_search_index.csv`

Two other files the notebook reads are already covered: `2016_mentions.csv`
is in `../data/` (a derived summary table, included in this repo), and
`alpha_network_scores.csv` is written by the notebook itself at line 2343
before it is read back.

The anonymised network files in `../data/` are the shareable output of this
notebook, not its input. The NetworkX experiments (resilience and
contagion) were run separately in Jupyter from the edge lists this notebook
writes out (see "Network construction" below).

## Using the anonymised files in R

If you don't have the raw exports, you can still run the network part of
this notebook on the anonymised files in `../data/`. What maps to what:

- `../data/edges.csv` → the private-message edge list the notebook builds
  at L2052–2085 (sender → receiver, with message counts and first/last
  half-year). 4,663 edges, 880 distinct nodes.
- `../data/members_anonymised.csv` → the node list (L1872–1955) with
  attributes: role, joined half, message count, profile views, posts,
  last visit/activity half. It joins to the edges on `node_id` — 91% of
  edge endpoints have a members row; the rest are message participants
  with no members record (see `../data/DATA_DICTIONARY.md`).
- `../data/messages_anonymised.csv` → the message-level data (thread,
  sender, receiver, half-year), 20,514 rows, for time-split work at
  half-year granularity.

```r
library(igraph)
library(dplyr)

edges <- read.csv("../data/edges.csv")
members <- read.csv("../data/members_anonymised.csv")

# the private-message network, same construction as L2253 in the notebook
msg_network <- graph_from_data_frame(d = edges, vertices = members, directed = TRUE)

# the same calls the notebook uses (L2393 onward)
edge_density(msg_network, loops = FALSE)
mean_distance(msg_network)
diameter(msg_network, directed = TRUE)
centralization.degree(msg_network, mode = "all")
centralization.betweenness(msg_network, directed = TRUE)
V(msg_network)$degree <- degree(msg_network)
V(msg_network)$betweenness <- betweenness(msg_network)
V(msg_network)$closeness <- closeness(msg_network)
alpha_centrality(msg_network, alpha = 0.9)
wtc <- cluster_walktrap(msg_network)
modularity(msg_network, membership(wtc))
```

Scope — what this does and doesn't reproduce:

- It reproduces the **private-message sub-network** analysis (the
  messages network in thesis Figure 4.9, top row): 880 nodes, 4,663
  edges. The numbers will differ from thesis Table 4.1, which is for
  the full network.
- It does **not** rebuild the full 7,415-node / 187,140-edge network
  (Figures 4.1–4.3): that includes posts as nodes and comment edges,
  which aren't in the anonymised files — post titles are content and
  can't be published in anonymised form.
- The text-dependent sections can't run on these files either: keyword
  labelling, the 2015/2016 message deep dives, and the Liberal
  Degeneration / Trivial HAPPENINGs post analysis all need message text,
  usernames and post titles.

## What's inside, section by section

Line numbers refer to this file.

### Setup and libraries — L1–45

YAML header (title, author, date 10/8/2021) and the library load:
`tidyverse`, `dplyr`, `sqldf`, `lubridate`, `igraph`, `ggplot2` and others.
Then the raw CSVs are read in.

### Data pre-processing — L46–964

- **Posts/topics** (L46–145): titles added to the posts/topics dataset.
- **Dates** (L76–145): Unix timestamps converted Epoch → POSIXct → Date,
  then split into day/month/year and half-year buckets (`semester()`).
  The half-year buckets are what the thesis uses throughout
  ("joined 2016.2", "2017.1", …).
- **Users info** (L146–206), **message topics** (L207–402).
- **Message review — labelling users by keywords** (L403–588): users
  identified by keyword (terrorist groups, recruiters, moderators).
- **Private-message pre-processing** (L589–964), including the data issue
  at L843: every row after thread 4445 where sender == receiver.

### Data description and visuals — L965–1871

Descriptive statistics for private messages (L971–1020) and comments/posts
(L1021–1470), then visuals: members (L1470–1600), private messages
(L1601–1670), and boxplots with medians by role (L1671–1871).

### Network construction — L1872–2252

- **Node list** (L1872–1955).
- **Edge lists** (L1956–2085): member comments → posts/topics;
  post author → posts/topics; private messages member → member.
- **Final edge list** (L2086–2252): the three merged into one, then the
  NetworkX prep — this is where `iron_march_edges_networkx.csv` and the
  weighted `iron_march_edges_networkx_contagion.txt` /
  `iron_march_edges_networkx_resilience.txt` files are written out.
  Those are the files the Jupyter/NetworkX experiments consumed.

### The network — L2253–2644

- **Creating the network** (L2253–2331): `graph_from_data_frame` on the
  merged edge list — 7,415 nodes, 187,140 edges.
- **Alpha centrality** (L2332–2361), **density** (L2362–2368),
  **average path length** (L2369–2374), **diameter** (L2375–2395).
- **Network stats** (L2393–2411): the numbers in thesis Table 4.1 —
  centralisation (degree 0.692, betweenness 0.024), indegree 1.387,
  outdegree 1.049, density 0.003, average distance 3.271, diameter 8.
  Modularity: the thesis reports Mod(N) = 0.310; the notebook's
  walktrap computation here gives 0.267 — same method family, different
  implementation from the Gephi figure in the thesis, so don't expect
  an exact match on that one number.
- **Bridges** (L2412–2433), **connections to terrorists** (L2434–2486),
  **National Action** (L2487–2515), **connections to mods and admins**
  (L2516–2644). This is where the 93.7% / 4.61% terrorist reach
  asymmetry comes from.

### Centrality and distributions — L2645–2889

- **Node degrees** (L2645–2651), **degree distribution** (L2652–2685) —
  the super-linear power law, thesis Figure 4.1.
- **Degree centrality** (L2686–2746) and **plots** (L2747–2852) — the
  most-central-nodes chart, thesis Figures 4.3–4.5.
- **Closeness** (L2853–2864), **reciprocity and clustering
  coefficient** (L2865–2878), **constraints / Burt's structural holes**
  (L2879–2889).

### Change over time — L2890–3272

- **Network split by timing** (L2890–2963), **network stats before**
  (L2964–3001) and **after** (L3002–3040).
- **T-tests** (L3041–3272): Kolmogorov–Smirnov goodness-of-fit, then
  paired Wilcoxon tests on degree, indegree, outdegree, betweenness and
  alpha centrality — thesis §4.4.1. This is the statistical basis for
  "change was driven by friendship formation, not external events".

### Deep dives — L3273–3844

- **Structural and network stats, deep dive** (L3273–3361).
- **2015 private messages** (L3362–3617): kllш and Bear (2015.2),
  Neizbezhnost and Bear (2015.1), other top messagers.
- **Posts** (L3618–3741) and **Liberal Degeneration & National Action
  posts** (L3742–3844).

### RQ1: what happened in 2016 — L3845–4461

The 2016 activity spike: 2016 private messages (Moorish Fascist and
Kay Kay Kay, Blackshirt 13 and Xav, others), posts, and the
Trivial HAPPENINGs & TRUMP posts (L4259–4461). Ends with the
**complex contagion result** (L4462–4485): the four simulation outcomes
plotted as thesis Figure 4.14 (Slavros 121 nodes in 7 steps, terrorists
135 in 8, moderators 100 in 9, central nodes 135 in 5).

### Trump election check — L4486–4785

**Any change before and after the Trump election?** The before/after
t-tests on degree and betweenness (p = 0.1635 for degree; betweenness
p = 0.04923) — the basis for the thesis finding that the 2016 US
presidential election did not significantly move centrality measures
(§4.4.2).
