# Publishing the Hugging Face dataset

`README.md` in this folder is the dataset card. The Hugging Face loader uses
one file format per repository, so the CSV tables are uploaded as JSON Lines
copies. `scripts/build_hf_dataset.py` writes the card, an unchanged copy of
`delegationcheck_v1_0.jsonl`, and those copies into one folder.

These commands use the `hf` command-line tool from `huggingface_hub` (the
syntax was checked against version 2.4.0; older releases provide
`huggingface-cli`, whose `upload` command takes the same arguments). Replace
`USERNAME` with your Hugging Face account, here and in the code example in
`README.md`. The `hf_upload/` build folder is ignored by git and by the
checksum and license scripts.

```bash
pip install -U "huggingface_hub>=1.0"
hf auth login

python scripts/build_hf_dataset.py --output hf_upload
hf repos create USERNAME/delegationcheck --repo-type dataset
hf upload USERNAME/delegationcheck hf_upload . --repo-type dataset \
  --commit-message "DelegationCheck v1.0"
```

To check the configurations before uploading, load the folder locally:

```bash
pip install datasets
python -c "import datasets; print(datasets.load_dataset('hf_upload', 'scenarios'))"
```

After the upload, the dataset page generates its own Croissant file. The
`croissant.json` at the repository root describes the GitHub release, with
file paths relative to the repository.
