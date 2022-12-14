# Gcs Snapshot

Google cloud storage snapshots.

It copy a GCS bucket into a new one (with the same name suffixed by `-bkp-{date}`) and keep a limited number of snapshots you'll be able to configure.

You can also choose to store all the backups in a single bucket and subfolders named with the backup's date (sometimes your service account doesn't have the right to dynamically create new buckets).

There's also a "restore" mode to copy a specific snapshot to the source bucket.

## Table of contents

[[_TOC_]]

## Git repositories

* Main repo: https://gitlab.comwork.io/oss/gcp/gcs-snapshot.git
* Github mirror: https://github.com/idrissneumann/gcs-snapshot.git
* Gitlab mirror: https://gitlab.com/ineumann/gcs-snapshot.git
* Froggit mirror: https://lab.frogg.it/ineumann/gcs-snapshot.git
* Bitbucket mirror: https://bitbucket.org/idrissneumann/gcs-snapshot.git

## Environment variables

### Snapshot mode

* `GCP_PROJECT` (required): gcp project
* `GCS_LOCATION`: GCS location (i.e: `europe-west1`)
* `GCS_SRC_BUCKET_NAME` (required): the source bucket you want to snapshot
* `GCS_SNAPSHOT_RETENTION` (required): the number of days to keep snapshots
* `GCS_DEST_DATE_FORMAT` (optional): the date format (default: `%Y%m%d`)
* `GCS_REGEXP_DATE_FORMAT` (optional): the regexp date format (default: `[0-9]{6,8}`). Beware it's need to be consistent with `GCS_DEST_DATE_FORMAT`
* `WAIT_TIME` (optional): if you want the pod to stay alive like a service worker, it will wait this time (in seconds). Otherwise, it'll `exit 0` in order to allow you to use the image in a cron job or a pipeline/workflow using something else.
* `GCS_TARGET_PREFIX` (optional): if you want the backup bucket to get a specific prefix name (by default it'll pick the value of `GCS_SRC_BUCKET_NAME` and get the last 63 characters)
* `GCS_TARGET_SINGLE_BUCKET_MODE` (optional): `enabled`, `true` or `yes` if you want to store the backup in a single GCS bucket with subfolders (it's disabled by default and create dynamic GCS bucket backups)
* `LOG_LEVEL` (optional): log level, default `INFO`
* `MAX_RETRY` (optional): max retry on copy blob (default to `5`)
* `GOOGLE_APPLICATION_CREDENTIALS` (optional): path the the service account json file (to mount as a volume). No need when you're using Kubernetes cloud identity

## Restore mode

* `GCP_PROJECT` (required): gcp project
* `GCS_LOCATION`: GCS location (i.e: `europe-west1`)
* `GCS_SRC_BUCKET_NAME` (required): the source bucket you want to snapshot
* `GCS_DEST_DATE_FORMAT` (optional): the date format (default: `%Y%m%d`)
* `GCS_REGEXP_DATE_FORMAT` (optional): the regexp date format (default: `[0-9]{6,8}`). Beware it's need to be consistent with `GCS_DEST_DATE_FORMAT`
* `SNAPSHOT_TO_RESTORE` (required): the snapshot bucket to restore
* `GCS_TARGET_SINGLE_BUCKET_MODE` (optional): `enabled`, `true` or `yes` if you want to store the backup in a single GCS bucket with subfolders (it's disabled by default and create dynamic GCS bucket backups)
* `GCS_SNAPSHOT_DATE` (optional): the date subfolder to restore (mandatory if `GCS_TARGET_SINGLE_BUCKET_MODE` is enabled)
* `LOG_LEVEL` (optional): log level, default `INFO`
* `MAX_RETRY` (optional): max retry on copy blob (default to `5`)
* `GOOGLE_APPLICATION_CREDENTIALS` (optional): path the the service account json file (to mount as a volume). No need when you're using Kubernetes cloud identity

Beware:
* The bucket `GCS_SRC_BUCKET_NAME` will be erased if it exists
* If you don't set the `SNAPSHOT_TO_RESTORE` you will fallback in the snapshot mode above

## Test with docker-compose

1. Generate a service account json key file and place it in the following path: `./service-account-file.json`
2. Generate a `.env` file from the [`.env.example`](./.env.example)

```shell
cp .env.example .env
# change the values inside
```

3. Run docker-compose

```shell
docker-compose up --build --force-recreate
```
