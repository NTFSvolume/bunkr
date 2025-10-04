# Bunkrr Uploader

## Supports

- Bunkrr accounts
- Parallel uploads
- Retries
- Progress bars

<div align="center">

![Preview1](https://raw.githubusercontent.com/NTFSvolume/bunkrr-uploader/refs/heads/master/assets/preview1.png)

![Preview2](https://raw.githubusercontent.com/NTFSvolume/bunkrr-uploader/refs/heads/master/assets/preview2.png)

</div>

```shell
usage: bunkr_uploader [-h] [-t str] [-n {str,null}] [-c int] [--chunk-size ByteSize] [--use-max-chunk-size bool] [--public bool] [--config-file {Path,null}] [--upload-retries int] [--chunk-retries int]
                      [--upload-delay int] [--recurse bool]
                      PATH

positional arguments:
  PATH                  File or directory to look for files in to upload

options:
  -h, --help            show this help message and exit
  -t str, --token str   API token for your account so that you can upload to a specific account/folder. You can also set the BUNKR_TOKEN environment variable for this (required)
  -n {str,null}, --album-name {str,null}
                        (default: null)
  -c int, --concurrent-uploads int
                        Maximum parallel uploads to do at once (default: 2)
  --chunk-size ByteSize
                        (default: 0)
  --use-max-chunk-size bool
                        Use the server's maximum chunk size instead of the default one (default: True)
  --public bool         Make all files uploaded public (default: True)
  --config-file {Path,null}
                        (default: null)
  --upload-retries int  How many times to retry a failed upload (default: 1)
  --chunk-retries int   How many times to retry a failed chunk or chunk completion (default: 2)
  --upload-delay int    How many seconds to wait in between failed upload attempts (default: 1)
  --recurse bool        Read files in `path` recursely (default: False)
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
