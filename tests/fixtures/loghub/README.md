# LogHub fixture slices

Committed log slices for CI smoke tests are sourced from [LogHub](https://github.com/logpai/loghub)
(Zenodo [8196385](https://zenodo.org/records/8196385)).

Full datasets are **not** committed. Download larger corpora with `scripts/fetch_corpora.py`
(added in Chapter 9) into the gitignored `data/` directory.

## Citation

If you use LogHub data in research or publications, cite:

> Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu.
> Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics.
> IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.

See https://github.com/logpai/loghub/blob/master/CITATION for BibTeX.

## Planned fixtures (Chapter 2+)

| File | Source | Purpose |
|------|--------|---------|
| `apache_2k.log` | LogHub-2k | Parser + template smoke test |
| `openssh_2k.log` | LogHub-2k | Drain3 regression |
