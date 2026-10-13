import pytest
from app.diet_service import generate_budget_diet_plan, calculate_cost_per_gram_protein

def test_generate_budget_diet_plan_veg_bulk():
    plan = generate_budget_diet_plan(
        daily_budget_inr=150.0,
        diet_preference="Pure Veg",
        fitness_goal="Weight Gain / Bulking",
        current_weight_kg=65.0,
        gender="male",
    )
    assert plan["status"] == "success"
    assert "Bulking" in plan["fitness_goal"]
    assert plan["diet_preference"] == "Pure Veg"
    assert plan["budget_tier"] == "Hostel / Student Budget (High-ROI)"
    assert plan["daily_budget_inr"] == 150.0
    assert plan["total_daily_protein_g"] >= 100.0
    assert len(plan["meals"]) == 5
    assert len(plan["cost_per_gram_protein_rankings"]) > 0
    assert plan["budget_variance_status"] in ["Within Budget", "Slight Overage (<15%)"]

def test_generate_budget_diet_plan_nonveg_recomp():
    plan = generate_budget_diet_plan(
        daily_budget_inr=250.0,
        diet_preference="Non-Veg",
        fitness_goal="Body Recomposition",
        current_weight_kg=75.0,
    )
    assert plan["status"] == "success"
    assert plan["budget_tier"] == "Working Professional (Balanced)"
    assert plan["total_daily_protein_g"] >= 120.0
    assert plan["usd_cost_day"] > 0

def test_generate_budget_diet_plan_usd_input():
    plan = generate_budget_diet_plan(
        daily_budget_inr=3.0,
        diet_preference="Eggetarian",
        fitness_goal="Fat Loss / Cutting",
        currency="USD",
        current_weight_kg=80.0,
    )
    assert plan["status"] == "success"
    assert plan["daily_budget_inr"] == 255.0
    assert plan["total_daily_protein_g"] >= 120.0

def test_generate_budget_diet_plan_invalid():
    res = generate_budget_diet_plan(daily_budget_inr=-50.0)
    assert "error" in res

def test_cost_per_gram_protein():
    rankings = calculate_cost_per_gram_protein("Pure Veg")
    assert len(rankings) > 0
    assert "soya" in rankings[0]["food"].lower()
    assert rankings[0]["cost_per_gram_protein_inr"] < 0.50
