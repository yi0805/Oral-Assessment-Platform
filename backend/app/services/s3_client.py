"""
AWS S3 client wrapper.
AWS S3.

Owner: Bess
Provides: upload, download, delete, generate_presigned_url for S3 objects.

Key convention: courses/{course_id}/materials/{material_id}/{original_filename}

TODO (Week 4):
- [ ] initialize boto3 client from settings
- [ ] upload_file(file_bytes, storage_key) → S3 key
- [ ] download_file(storage_key) → bytes
- [ ] delete_file(storage_key)
- [ ] For local dev: implement a LocalFileStorage that mimics the S3 interface
      using the local filesystem, so you can develop without AWS credentials.
"""
pass
