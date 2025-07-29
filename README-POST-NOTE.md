### Post filename (tiny PR)

You can control the output filename of the first LinkedIn post via an env var:
```bash
export POST_FILENAME=post_001.md   # default is post_linkedin.md
```
This affects only new runs. Existing runs under `out/` remain unchanged.
