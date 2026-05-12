from __future__ import annotations

import logging
import os

import boto3
from botocore.exceptions import ProfileNotFound

from app.core.config import settings

logger = logging.getLogger(__name__)

_clients: dict[str, object] = {}


def get_s3_client():
    if "s3" not in _clients:
        session_kwargs = {"region_name": settings.aws_region}
        
        if settings.aws_profile_name:
            session_kwargs["profile_name"] = settings.aws_profile_name
            logger.info("[AWS] Creating S3 client with profile '%s'", settings.aws_profile_name)

        else:
            logger.info("[AWS] Creating S3 client with default credential chain")

        try:
            session = boto3.Session(**session_kwargs)
            _clients["s3"] = session.client("s3")

        except ProfileNotFound as exc:
            raise RuntimeError(
                f"AWS profile '{settings.aws_profile_name}' was not found. "
                "Run aws configure sso or unset AWS_PROFILE_NAME to use the default credential chain."
            ) from exc

    return _clients["s3"]


def get_bedrock_client():
    if "bedrock" not in _clients:

        if not settings.aws_bearer_token_bedrock:
            raise RuntimeError("AWS_BEARER_TOKEN_BEDROCK not set")
        
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.aws_bearer_token_bedrock
        logger.info("[AWS] Creating Bedrock client in region '%s'", settings.aws_region)

        _clients["bedrock"] = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region,
        )
        
    return _clients["bedrock"]
