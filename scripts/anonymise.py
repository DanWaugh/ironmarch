#!/usr/bin/env python3
"""Anonymise Iron March repo datasets for public release.

Reads the cleaned R-notebook outputs from ./raw/ (iron_march_members.csv
and iron_march_private_messages.csv, as produced by
analysis/iron_march_analysis.Rmd), writes anonymised files to ./data/:
  - members_anonymised.csv : one row per member, no names/emails/exact dates
  - messages_anonymised.csv: one row per private message, no text/titles/names
  - edges.csv               : aggregated sender -> receiver message counts

Hashing: SHA-256(salt + '|' + value), truncated to 16 hex chars.
The salt lives in ./salt.txt (generated on first run) or in the
IRONMARCH_SALT environment variable, and must NEVER be committed to
the repo: anyone with the salt + a known username could re-identify
rows by dictionary attack. Only the author can re-run this (it needs
the cleaned source files and the salt); everyone else can verify the
published files with scripts/verify.py.
"""
import csv
import hashlib
import os
import secrets
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
RAW = os.path.join(BASE, "raw")  # cleaned R-notebook outputs live here locally; never committed
OUT = os.path.join(BASE, "data")
SALT_FILE = os.path.join(BASE, "salt.txt")  # local only; gitignored, never committed


def get_salt():
    if os.environ.get("IRONMARCH_SALT"):
        return os.environ["IRONMARCH_SALT"]
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE) as f:
            return f.read().strip()
    salt = secrets.token_hex(16)
    with open(SALT_FILE, "w") as f:
        f.write(salt + "\n")
    print("Generated new salt in salt.txt — keep it out of the repo.")
    return salt


SALT = get_salt()


def h(value):
    return hashlib.sha256(f"{SALT}|{value}".encode("utf-8")).hexdigest()[:16]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    members = read_csv(os.path.join(RAW, "iron_march_members.csv"))
    messages = read_csv(os.path.join(RAW, "iron_march_private_messages.csv"))

    # --- Members ---
    member_rows = []
    for m in members:
        member_rows.append({
            "node_id": h(m["member_id"]),
            "member_joined_half": m["member_joined_half"],
            "member_msg_count": m["member_msg_count"],
            "member_profile_views": m["member_profile_views"],
            "member_posts": m["member_posts"],
            "member_last_visit_half": m["member_last_visit_half"],
            "member_last_activity_half": m["member_last_activity_half"],
            "member_role": m["member_role"],
        })
    write_csv(os.path.join(OUT, "members_anonymised.csv"),
              ["node_id", "member_joined_half", "member_msg_count",
               "member_profile_views", "member_posts",
               "member_last_visit_half", "member_last_activity_half",
               "member_role"], member_rows)

    # --- Messages (structure only, no text) ---
    msg_rows = []
    for p in messages:
        msg_rows.append({
            "thread_id": h(p["msg_thread_id"]),
            "sender_id": h(p["msg_sender_id"]),
            "receiver_id": h(p["msg_receiver_id"]),
            "msg_date_half": p["msg_date_half"],
        })
    write_csv(os.path.join(OUT, "messages_anonymised.csv"),
              ["thread_id", "sender_id", "receiver_id", "msg_date_half"],
              msg_rows)

    # --- Aggregated edge list ---
    edge_counts = Counter()
    edge_threads = defaultdict(set)
    edge_first = {}
    edge_last = {}
    for p in messages:
        key = (h(p["msg_sender_id"]), h(p["msg_receiver_id"]))
        edge_counts[key] += 1
        edge_threads[key].add(h(p["msg_thread_id"]))
        half = p["msg_date_half"]
        if key not in edge_first or half < edge_first[key]:
            edge_first[key] = half
        if key not in edge_last or half > edge_last[key]:
            edge_last[key] = half
    edge_rows = [{
        "sender_id": s,
        "receiver_id": r,
        "message_count": c,
        "thread_count": len(edge_threads[(s, r)]),
        "first_half": edge_first[(s, r)],
        "last_half": edge_last[(s, r)],
    } for (s, r), c in sorted(edge_counts.items(),
                              key=lambda kv: -kv[1])]
    write_csv(os.path.join(OUT, "edges.csv"),
              ["sender_id", "receiver_id", "message_count",
               "thread_count", "first_half", "last_half"], edge_rows)

    # --- Summary (the profiling numbers live in data/DATA_DICTIONARY.md) ---
    node_ids = {r["node_id"] for r in member_rows}
    orphans = ({h(p["msg_sender_id"]) for p in messages} |
               {h(p["msg_receiver_id"]) for p in messages}) - node_ids

    print(f"members: {len(members)} -> {len(member_rows)} rows")
    print(f"messages: {len(messages)} -> {len(msg_rows)} rows")
    print(f"edges: {len(edge_rows)} pairs; orphan participants: {len(orphans)}")


if __name__ == "__main__":
    main()
