# Annotator vote counts

`panel_vote_distribution.csv` reports, for each scenario, how many of the three
annotators chose each decision, whether a majority exists, and the four-way and
binary majority labels. It does not say which annotator cast which vote, and it
contains no notes, confidence ratings, or identifying information.

The private source file has SHA-256
`01d8bf94ca154c9f1e70b26e1ed1bcbd83a0da140ec3dc537455e944246ccd61`.

Each row's four counts sum to three. `scripts/verify_artifact.py` checks this
and checks that no annotator-linked column is present.

File names in this directory that contain `expert` predate the paper and refer
to the three annotators.
