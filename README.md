# Bunkr Uploader

[![PyPI - Version](https://img.shields.io/pypi/v/bunkr)](https://pypi.org/project/bunkr/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bunkr?style=flat)](https://pypi.org/project/bunkr/)
[![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/NTFSvolume/bunkr/actions/workflows/ruff.yml)
[![GitHub License](https://img.shields.io/github/license/NTFSvolume/bunkr)](https://github.com/NTFSvolume/bunkr/blob/master/LICENSE)

## Supports

- Bunkr accounts
- Parallel uploads
- Retries
- Progress bars

<div align="center">

![Preview1](https://raw.githubusercontent.com/NTFSvolume/bunkrr-uploader/refs/heads/master/assets/preview1.png)

![Preview2](https://raw.githubusercontent.com/NTFSvolume/bunkrr-uploader/refs/heads/master/assets/preview2.png)

</div>

```shell
Usage: bunkr upload --token STR [OPTIONS] PATH

Upload a file or files to bunkr

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  PATH  File or directory to look for files in to upload [required]                                                                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Parameters ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│    --recurse                Read files in PATH recursely [default: False]                                                                          │
│ *  --token -t               API token for your account so that you can upload to a specific account/folder. You can also set the BUNKR_TOKEN       │
│                             environment variable for this [env var: BUNKR_TOKEN] [required]                                                        │
│    --album-name -n          Name to use for album. If an album with this name already exists, add the files to that album                          │
│    --concurrent-uploads -c  Maximum parallel uploads to do at once [default: 2]                                                                    │
│    --chunk-size             Size of chunks to use for uploads. 0 or None will use the server's maximum chunk size                                  │
│    --public --no-public     Make all uploaded files public [default: True]                                                                         │
│    --retries -R             How many times to retry a failed file upload [default: 1]                                                              │
│    --chunk-retries          How many times to retry a failed chunk upload [default: 2]                                                             │
│    --delay                  How many seconds to wait in between failed upload attempts [default: 1.0]  
```

## TODO

- [X] Slit API and UploadClient
- [X] Migrate to aiohttp
- [X] Upload logging
- [X] Replace tqdm with rich progress
- [ ] Skipping duplicate uploads
- [X] Private and public directory uploads
- [ ] Update README
- [X] Make it work
- [ ] Add file zipping and cleanup
- [ ] Add tests
- [ ] Add github runners for tests
- [X] Recursive directory upload support

Original code by [alexmi256](https://github.com/alexmi256/bunkrr-uploader)
