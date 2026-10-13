"""Unit tests for media generation service."""

import pytest
from app.media_service import _slugify, BUCKET_NAME, PROJECT_ID, VIDEO_MODEL


def test_constants_and_slugify():
    assert PROJECT_ID == "qwiklabs-gcp-03-fde3effbf431"
    assert BUCKET_NAME == "liftmetrics-media-fde3effbf431"
    assert VIDEO_MODEL == "gemini-omni-flash-preview"
    assert _slugify("Barbell Back Squat!") == "barbell-back-squat"
