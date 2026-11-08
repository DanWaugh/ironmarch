# Ethics statement — Iron March datasets

## What this data is

These datasets come from the Iron March web-forum, a neo-Nazi forum
whose database was leaked publicly in November 2019. The data was
used for the MSc thesis *Social Network Analysis of the Iron March
web-forum* (Technological University Dublin, MSc Computer Science —
Data Science, 2022), conducted under the Institute's guidelines for
ethics in research. It is published here to make that research
reproducible — not as an archive of the forum.

## What was removed, and why

The raw export contained material that must not be redistributed:

- **Email addresses** for all 1,207 members — direct identifiers.
  Removed entirely.
- **Usernames** — pseudonymous, but identifying in context and
  linkable to real people. Removed entirely; IDs are replaced with
  salted hashes (see the data dictionary).
- **Full private-message text** (20,513 messages) and **thread
  titles** — private communications, some containing sensitive
  personal material. Removed entirely. Only the network structure
  (who messaged whom, when, how often) is published, plus the derived
  keyword-mention counts in `data/2016_mentions.csv`.
- **Exact timestamps** — replaced with half-year buckets.

What remains supports structural network analysis only. No message
content, no names, no contact details.

## Consent and re-identification

Forum users did not consent to this research, and the data exists
only because of the leak. That is why minimisation was applied:
publish the least data that still reproduces the analysis, and
nothing that identifies a person.

- Do **not** attempt to re-identify anyone in these files. The
  hashes are salted and the salt is held privately and never
  published; attempting to reverse them, or to link rows to people
  via outside data, is against the terms of use of this repository.
- Individuals discussed by name in the thesis text (for example the
  forum's founder, a public figure in reporting on the forum) are
  **not** identifiable from these datasets.
- If you believe you are identifiable in this data, or you want
  material removed, open an issue on this repository and it will be
  dealt with.

## Intended use

Research and education in social network analysis, network
resilience and disruption, and counter-extremism methods. Do not use
this data to harass, target, dox or contact any individual, or to
rebuild the forum's membership list.

## Content note

Iron March was an extremist forum. These files contain no message
content, but the subject matter — and the thesis itself — concerns
far-right extremism and terrorism.
