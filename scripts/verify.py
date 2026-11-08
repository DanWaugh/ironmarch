#!/usr/bin/env python3
"""Verify the published Iron March datasets contain no leaked PII or content.

Runs from a fresh clone with no extra setup: it checks only the published
files in data/. If the private salt (salt.txt) and the cleaned source
files (raw/) are also present, it runs the full checks (hash consistency,
row counts, username/message-text sampling) and reports which checks
were skipped otherwise.

Usage: python3 scripts/verify.py   (from the repo root)
"""
import csv
import hashlib
import os
import random
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
DATA = os.path.join(BASE, "data")
RAW = os.path.join(BASE, "raw")  # cleaned source files; local only, never committed
SALT_FILE = os.path.join(BASE, "salt.txt")  # local only; never committed

fails = []
skipped = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(name)


def skip(name, reason):
    print(f"SKIP {name} — {reason}")
    skipped.append(name)


def h(value, salt):
    return hashlib.sha256(f"{salt}|{value}".encode("utf-8")).hexdigest()[:16]


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


members_out = read_csv(os.path.join(DATA, "members_anonymised.csv"))
messages_out = read_csv(os.path.join(DATA, "messages_anonymised.csv"))
edges_out = read_csv(os.path.join(DATA, "edges.csv"))
mentions_text = read_text(os.path.join(DATA, "2016_mentions.csv"))

out_text = {f: read_text(os.path.join(DATA, f)) for f in
            ["members_anonymised.csv", "messages_anonymised.csv", "edges.csv"]}
blob = "\n".join(out_text.values())

# --- Checks that need only the published files (always run) ---

# 1. No email addresses (anonymised files + the mentions summary table)
check("no '@' in any output", "@" not in blob and "@" not in mentions_text)
check("no email-like pattern in outputs",
      not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                    blob + mentions_text))

# 2. No exact datetimes (anonymised files + the mentions summary table)
check("no ISO datetimes in outputs",
      not re.search(r"\d{4}-\d{2}-\d{2}", blob + mentions_text))

# 3. Join integrity: every edge endpoint appears in the messages file;
#    every message sender/receiver is a member or a documented orphan
msg_ids = {r["sender_id"] for r in messages_out} | {r["receiver_id"] for r in messages_out}
edge_ids = {r["sender_id"] for r in edges_out} | {r["receiver_id"] for r in edges_out}
check("edge endpoints all appear in messages file", edge_ids <= msg_ids)
node_ids = {r["node_id"] for r in members_out}
orphans = msg_ids - node_ids
print(f"INFO orphan participants (in messages, not in members file): {len(orphans)}")

# 4. Edge aggregation reconciles with message rows
agg = Counter((r["sender_id"], r["receiver_id"]) for r in messages_out)
check("edges.csv message counts reconcile",
      all(agg[(r["sender_id"], r["receiver_id"])] == int(r["message_count"])
          for r in edges_out) and len(agg) == len(edges_out),
      f"{len(edges_out)} pairs")

# 5. Expected columns only
check("members columns as designed",
      list(members_out[0].keys()) == ["node_id", "member_joined_half",
                                      "member_msg_count", "member_profile_views",
                                      "member_posts", "member_last_visit_half",
                                      "member_last_activity_half", "member_role"])
check("messages columns as designed",
      list(messages_out[0].keys()) == ["thread_id", "sender_id", "receiver_id",
                                       "msg_date_half"])
check("edges columns as designed",
      list(edges_out[0].keys()) == ["sender_id", "receiver_id", "message_count",
                                    "thread_count", "first_half", "last_half"])

# 6. Node IDs unique
check("node_ids unique", len(node_ids) == len(members_out))

# --- Full checks (need the private salt and the cleaned source files) ---
# The mentions summary table is NOT included in the username / message-text
# checks below: its "Slavros" keyword is an intentional count label, not a
# leaked identifier.
have_salt = os.path.exists(SALT_FILE)
members_raw_path = os.path.join(RAW, "iron_march_members.csv")
messages_raw_path = os.path.join(RAW, "iron_march_private_messages.csv")
have_raw = os.path.exists(members_raw_path) and os.path.exists(messages_raw_path)

if have_salt and have_raw:
    with open(SALT_FILE) as f:
        salt = f.read().strip()
    members_raw = read_csv(members_raw_path)
    messages_raw = read_csv(messages_raw_path)

    # 7. No original usernames (sample 100 + the most prominent)
    random.seed(7)
    names = [m["member_name"] for m in members_raw]
    sample = random.sample(names, 100) + names[:5]
    leaked = [n for n in sample if n and n in blob]
    check("no sampled original usernames in outputs", not leaked,
          f"leaked: {leaked[:3]}" if leaked else f"checked {len(sample)} names")

    # 8. No message text (sample 50 non-trivial messages)
    texts = [p["msg_text"] for p in messages_raw if len(p["msg_text"]) > 40]
    sample_texts = random.sample(texts, 50)
    leaked_t = [t[:40] for t in sample_texts if t[:60] in blob]
    check("no sampled message text in outputs", not leaked_t,
          f"checked {len(sample_texts)} messages")

    # 9. No thread titles
    titles = {p["msg_thread_title"] for p in messages_raw if len(p["msg_thread_title"]) > 15}
    leaked_titles = [t for t in list(titles)[:200] if t in blob]
    check("no thread titles in outputs", not leaked_titles)

    # 10. Row counts preserved
    check("members row count preserved",
          len(members_out) == len(members_raw), f"{len(members_out)} vs {len(members_raw)}")
    check("messages row count preserved",
          len(messages_out) == len(messages_raw), f"{len(messages_out)} vs {len(messages_raw)}")

    # 11. Hash consistency: member 1 (Slavros) maps identically everywhere
    expected = h("1", salt)
    check("member_id 1 hashes consistently",
          any(r["node_id"] == expected for r in members_out) and
          any(r["sender_id"] == expected for r in messages_out))
else:
    reason = "needs salt.txt and raw/ (private; not in the repo)"
    skip("no sampled original usernames in outputs", reason)
    skip("no sampled message text in outputs", reason)
    skip("no thread titles in outputs", reason)
    skip("members row count preserved", reason)
    skip("messages row count preserved", reason)
    skip("member_id 1 hashes consistently", reason)

print()
if fails:
    print(f"FAILURES: {fails}")
else:
    print("ALL CHECKS PASSED", end="")
    if skipped:
        print(f" ({len(skipped)} checks skipped — run with salt.txt and raw/ for the full checks)")
    else:
        print()
sys.exit(1 if fails else 0)
