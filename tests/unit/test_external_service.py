"""Unit tests for external API service."""

import pytest
from app.external_service import fetch_nutrition_facts, lookup_external_muscle_info


def test_fetch_nutrition_facts_fallback():
    result = fetch_nutrition_facts("rolled oats")
    assert result["status"] == "success"
    assert "macros_per_100g" in result
    assert result["macros_per_100g"]["protein_g"] > 0
    assert result["macros_per_100g"]["calories_kcal"] > 0


def test_lookup_external_muscle_info():
    result = lookup_external_muscle_info("Pectoralis major")
    assert result["status"] == "success"
    assert result["count"] >= 1
    assert "muscles" in result
    assert any("Pectoralis major" in m["scientific_name"] for m in result["muscles"])
