# Data dictionary — Iron March datasets

Public versions of the datasets used in the MSc thesis
*Social Network Analysis of the Iron March web-forum* (Technological
University Dublin, MSc Computer Science — Data Science, 2022) —
three anonymised files and one derived summary table
(`2016_mentions.csv`).
The raw files they replace contained email addresses, usernames and
full private-message text; those are **not** published here. How these
files were made from the raw export — Kaggle download, cleaning in
the R notebook, anonymisation — is in
[PREPROCESSING.md](PREPROCESSING.md).

## How the data was anonymised

- All identifiers (member IDs, message sender/receiver IDs, thread IDs)
  are replaced with the first 16 hex characters of
  `SHA-256(salt + "|" + original value)`. The salt is held privately and
  is **not** in this repository: without it, the hashes cannot be
  reversed by dictionary attack against known usernames.
- Email addresses, usernames, message text and thread titles are removed
  entirely — not hashed, not redacted, not present.
- Exact timestamps are replaced by half-year buckets (`2011.2` = second
  half of 2011), as in the original export.
- The process is scripted (`anonymise.py`) and verified (`verify.py`):
  row counts are preserved, hashes are consistent across files, and
  the outputs were checked for email patterns, sampled usernames,
  sampled message text and thread titles — none were found.

## Files

### `members_anonymised.csv` — 1,207 rows

One row per forum member in the original export.

| Column | Type | Description | Source / change |
|---|---|---|---|
| `node_id` | string (16 hex chars) | Anonymised member ID; the join key to the message files | `member_id`, hashed |
| `member_joined_half` | string, e.g. `2011.2` | Half-year the member joined | kept as-is |
| `member_msg_count` | integer | Private messages sent (as recorded in the member record) | kept as-is |
| `member_profile_views` | integer | Times the member's profile was viewed | kept as-is |
| `member_posts` | integer | Public forum posts made | kept as-is |
| `member_last_visit_half` | string, e.g. `2017.2` | Half-year of last visit | kept as-is |
| `member_last_activity_half` | string, e.g. `2017.2` | Half-year of last recorded activity | kept as-is |
| `member_role` | string | Forum role (e.g. Iron March Admin, Moderator, Member) | kept as-is |

Removed from the original: `member_name`, `member_email` (all 1,207
members had an email address), `member_joined` and
`member_last_activity_date` (exact datetimes).

### `messages_anonymised.csv` — 20,514 rows

One row per private message. **No message content is included** —
this file preserves only the network structure (who messaged whom,
when, in which thread).

| Column | Type | Description | Source / change |
|---|---|---|---|
| `thread_id` | string (16 hex chars) | Anonymised private-message thread ID | `msg_thread_id`, hashed |
| `sender_id` | string (16 hex chars) | Anonymised sender (`node_id` in the members file) | `msg_sender_id`, hashed |
| `receiver_id` | string (16 hex chars) | Anonymised receiver (`node_id` in the members file) | `msg_receiver_id`, hashed |
| `msg_date_half` | string, e.g. `2011.2` | Half-year the message was sent | kept as-is |

Removed from the original: `msg_thread_title`, `msg_sender_name`,
`msg_receiver_name`, `msg_post_id`, `msg_text` (present in 20,513 of
20,514 rows), `msg_date` (exact datetime).

### `edges.csv` — 4,663 rows

Aggregated directed edge list derived from `messages_anonymised.csv`,
for convenience. One row per ordered sender → receiver pair.

| Column | Type | Description |
|---|---|---|
| `sender_id` | string (16 hex chars) | Anonymised sender |
| `receiver_id` | string (16 hex chars) | Anonymised receiver |
| `message_count` | integer | Private messages sent along this edge |
| `thread_count` | integer | Distinct threads between this pair |
| `first_half` | string | Half-year of the earliest message on this edge |
| `last_half` | string | Half-year of the latest message on this edge |

### `2016_mentions.csv` — 33 rows

A derived summary table created during the analysis (not an
anonymised raw file): counts of keyword mentions in comments and
private messages, by half-year. Read by the notebook at line 4427
for the "Mentions of Key Events" chart. Included here so the notebook
can run end-to-end once the six Kaggle files are added.

| Column | Type | Description |
|---|---|---|
| `edge` | string | Where the mention appeared: `Comment` or `Message` |
| `keyword` | string | The keyword counted: Slavros, Trump, National Action, Brexit, Atomwaffen Division |
| `year` | integer | Year of the mentions (2015 or 2016) |
| `half` | string, e.g. `2016.1` | Half-year of the mentions |
| `mention` | integer | Number of mentions of that keyword in that half-year |

The keywords name events and people already discussed by name in
the thesis text; they are labels for counts, not identifiers linked
to any member row. The file has a UTF-8 byte-order mark at the start
(as in the original); it does not affect the notebook, which only
uses the `keyword`, `mention` and `year` columns.

## Known limitations

- **201 message participants appear in the message files but have no row
  in the members file** (accounts missing from the members export).
  Their hashed IDs still appear in the message and edge files.
- Usernames are gone, so individuals named in the thesis text (for
  example the forum's founder) cannot be identified from these files.
- With message text removed, these files support structural network
  analysis only — no content, sentiment or topic analysis is possible.
- Dates are half-year buckets: no daily or weekly time resolution.
- The data covers the forum's life up to the leak (2011–2017 halves).
