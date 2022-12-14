import re
import os

from datetime import datetime
from time import sleep
from logger_utils import log_msg
from common_utils import is_not_empty, is_true

MAX_RETRY = int(os.environ['MAX_RETRY'])
REGEXP_DATE_FORMAT = os.environ['GCS_REGEXP_DATE_FORMAT']

def copy_blobs(gcs_client, src_bucket, target_bucket, src_dir = None, target_dir = ''):
    blobs = gcs_client.list_blobs(
        bucket_or_name = src_bucket.name,
        prefix = src_dir
    )
    
    for blob in blobs:
        copy_blob(blob, src_bucket, target_bucket, 0, target_dir)

def copy_blob(blob, source_bucket, target_bucket, retry, target_dir):
    file_name = blob.name
    if is_not_empty(target_dir) and target_dir == "root#restore":
        new_name = re.sub("^{}/".format(REGEXP_DATE_FORMAT), '', file_name)
    elif is_not_empty(target_dir):
        new_name = "{}/{}".format(target_dir, file_name)
    else:
        new_name = file_name
    
    log_msg("INFO", "[copy_blob] copy file {}".format(file_name))
    src_blob = source_bucket.blob(file_name)

    if retry >= MAX_RETRY:
        log_msg("ERROR", "[copy_blob] all retry have failed for blob {}, {}/{}".format(file_name, retry, MAX_RETRY))
        return

    try:
        source_bucket.copy_blob(src_blob, target_bucket, new_name)
    except Exception as e:
        log_msg("ERROR", "[copy_blob] unexpected error : {}, retrying {}/{}".format(e, retry, MAX_RETRY))
        sleep(1)
        copy_blob(blob, source_bucket, target_bucket, retry+1, target_dir)

def erase_bucket(gcs_client, name):
    blobs = gcs_client.list_blobs(name)
    for blob in blobs:
        log_msg("INFO", "[erase_bucket] deleting {}".format(blob.name))
        try:
            blob.delete()
        except Exception as e:
            log_msg("INFO", "[erase_bucket] seems blob {} is not found, e = {}".format(blob.name, e))

def find_or_create_bucket_with_erase_f(gcs_client, location, name, erase_function):
    try:
        target_bucket = gcs_client.get_bucket(name)
        erase_function(gcs_client, name)
        return target_bucket
    except Exception as e:
        log_msg("INFO", "[find_or_create_bucket] Error when searching bucket {}, e = {} (we'll create it for you)".format(name, e))
        target_bucket = gcs_client.bucket(name)
        try:
            target_bucket.create(location = location)
        except Exception as e2:
            log_msg("INFO", "[find_or_create_bucket] We don't have the right to recreate the bucket {}, e = {}".format(name, e2))
            erase_function(gcs_client, name)
        return target_bucket

def find_or_create_bucket(gcs_client, location, name):
    return find_or_create_bucket_with_erase_f(gcs_client, location, name, lambda x, y: None)

def reinit_bucket(gcs_client, location, name):
    return find_or_create_bucket_with_erase_f(gcs_client, location, name, erase_bucket)

def delete_old_dirs(current_date, target_name, gcs_client, date_format, retention, location):
    target_bucket = find_or_create_bucket(gcs_client, location, target_name)
    blobs = gcs_client.list_blobs(target_bucket)

    for blob in blobs:
        match = re.match("^({})/.*$".format(REGEXP_DATE_FORMAT), blob.name)
        if not match:
            log_msg("INFO", "[delete_old_dirs] The file {} will not be deleted because it's not matching a date".format(blob.name))
            continue

        try:
            creation_date = datetime.strptime(match.group(1), date_format)
        except Exception as e:
            log_msg("INFO", "[delete_old_dirs] The file {} will not be deleted because of : e = {}".format(blob.name, e))
            continue

        d = (current_date - creation_date).days
        if d >= retention:
            log_msg("INFO", "[delete_old_dirs] delete file {} because d = {} >= r = {}".format(blob.name, d, retention))
            blob.delete()

def delete_old_buckets(current_date, target_name, gcs_client, date_format, retention):
    prefix = re.sub("-bkp-[0-9]+$", '', target_name)
    for bucket in gcs_client.list_buckets(prefix = prefix):
        bucket_name = bucket.name
        try:
            creation_date = datetime.strptime(bucket_name, "{}-bkp-{}".format(prefix, date_format))
        except Exception as e:
            log_msg("INFO", "[delete_old_buckets] The bucket {} will not be deleted because of : e = {}".format(bucket_name, e))
            continue

        d = (current_date - creation_date).days
        if d >= retention:
            log_msg("INFO", "[delete_old_buckets] delete bucket {} because d = {} >= r = {}".format(bucket.name, d, retention))
            erase_bucket(gcs_client, bucket_name)
            bucket.delete(force=True)

def compute_target_bucket_backup_name(single_gcs_mode, target_prefix, src_bucket_name, current_date):
    if is_not_empty(target_prefix) and is_true(single_gcs_mode) and src_bucket_name != target_prefix:
        target_name = target_prefix
    elif is_true(single_gcs_mode):
        target_name = "{}-bkp".format(src_bucket_name)
    elif is_not_empty(target_prefix):
        target_name = "{}-bkp-{}".format(target_prefix, current_date)
    else:
        target_name = "{}-bkp-{}".format(src_bucket_name, current_date)
    
    return target_name[-63:]
