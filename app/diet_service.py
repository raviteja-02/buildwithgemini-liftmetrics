"""Indian-friendly and global budget nutrition engine for LiftMetrics.

Provides balanced, macro-optimized, and budget-conscious meal plans across:
1. Strength / Powerlifting
2. Body Recomposition
3. Weight Gain / Bulking
4. Weight Loss / Cutting
5. Athletic Endurance / Conditioning
"""

import math
from typing import Any, Dict, List, Optional

# Currency conversion reference: 1 USD ≈ 85 INR
INR_TO_USD = 1.0 / 85.0

# Nutritional profiles per 100g of staple foods (Calories, Protein, Carbs, Fat, Est. Cost INR)
STAPLE_FOODS: Dict[str, Dict[str, Any]] = {
    # Vegetarian & High-Efficiency Desi Staples
    "soya_chunks": {
        "name": "Soya Chunks (Nutrela / Desi Soya)",
        "protein_per_100g": 52.0,
        "carbs_per_100g": 33.0,
        "fats_per_100g": 0.5,
        "calories_per_100g": 345,
        "cost_inr_per_100g": 15.0,  # ₹150/kg -> ₹0.29/g protein (Highest efficiency in India)
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "sattu": {
        "name": "Roasted Chana Sattu (Desi Whey)",
        "protein_per_100g": 20.6,
        "carbs_per_100g": 65.0,
        "fats_per_100g": 5.2,
        "calories_per_100g": 390,
        "cost_inr_per_100g": 9.0,   # ₹90/kg
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "paneer": {
        "name": "Fresh Dairy Paneer (Cottage Cheese)",
        "protein_per_100g": 18.3,
        "carbs_per_100g": 3.4,
        "fats_per_100g": 20.8,
        "calories_per_100g": 274,
        "cost_inr_per_100g": 42.0,  # ₹420/kg
        "diet_types": ["pure_veg", "eggetarian", "non_veg"],
    },
    "tofu": {
        "name": "Soy Tofu",
        "protein_per_100g": 17.0,
        "carbs_per_100g": 2.8,
        "fats_per_100g": 8.0,
        "calories_per_100g": 144,
        "cost_inr_per_100g": 35.0,  # ₹350/kg
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "curd_dahi": {
        "name": "Desi Curd / Dahi",
        "protein_per_100g": 4.0,
        "carbs_per_100g": 4.7,
        "fats_per_100g": 3.2,
        "calories_per_100g": 61,
        "cost_inr_per_100g": 8.0,   # ₹80/kg
        "diet_types": ["pure_veg", "eggetarian", "non_veg"],
    },
    "chana_sprouts": {
        "name": "Sprouted Black Chana / Moong",
        "protein_per_100g": 15.0,
        "carbs_per_100g": 40.0,
        "fats_per_100g": 2.0,
        "calories_per_100g": 240,
        "cost_inr_per_100g": 10.0,  # ₹100/kg
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "dal_lentils": {
        "name": "Moong / Toor / Masoor Dal (Cooked)",
        "protein_per_100g": 9.0,
        "carbs_per_100g": 20.0,
        "fats_per_100g": 1.0,
        "calories_per_100g": 116,
        "cost_inr_per_100g": 12.0,
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "peanut_butter": {
        "name": "Natural Peanut Butter / Roasted Peanuts",
        "protein_per_100g": 25.0,
        "carbs_per_100g": 20.0,
        "fats_per_100g": 50.0,
        "calories_per_100g": 588,
        "cost_inr_per_100g": 25.0,
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    # Eggetarian & Non-Vegetarian Staples
    "eggs": {
        "name": "Whole Eggs (per 2 large eggs ≈ 100g)",
        "protein_per_100g": 12.6,
        "carbs_per_100g": 0.8,
        "fats_per_100g": 9.5,
        "calories_per_100g": 143,
        "cost_inr_per_100g": 14.0,  # ₹7 per egg
        "diet_types": ["eggetarian", "non_veg"],
    },
    "egg_whites": {
        "name": "Egg Whites (per 3 whites ≈ 100g)",
        "protein_per_100g": 11.0,
        "carbs_per_100g": 0.7,
        "fats_per_100g": 0.2,
        "calories_per_100g": 52,
        "cost_inr_per_100g": 18.0,
        "diet_types": ["eggetarian", "non_veg"],
    },
    "chicken_breast": {
        "name": "Boneless Chicken Breast (Raw)",
        "protein_per_100g": 31.0,
        "carbs_per_100g": 0.0,
        "fats_per_100g": 3.6,
        "calories_per_100g": 165,
        "cost_inr_per_100g": 28.0,  # ₹280/kg
        "diet_types": ["non_veg"],
    },
    "fish_rohu": {
        "name": "Freshwater Fish (Rohu / Katla / Tilapia)",
        "protein_per_100g": 20.0,
        "carbs_per_100g": 0.0,
        "fats_per_100g": 2.5,
        "calories_per_100g": 102,
        "cost_inr_per_100g": 26.0,  # ₹260/kg
        "diet_types": ["non_veg"],
    },
    # Carbs & Healthy Additions
    "rolled_oats": {
        "name": "Rolled Oats / Daliya",
        "protein_per_100g": 13.0,
        "carbs_per_100g": 66.0,
        "fats_per_100g": 6.0,
        "calories_per_100g": 389,
        "cost_inr_per_100g": 16.0,
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "chapati_roti": {
        "name": "Whole Wheat Roti / Chapati (per 2 rotis ≈ 80g)",
        "protein_per_100g": 8.0,
        "carbs_per_100g": 46.0,
        "fats_per_100g": 3.0,
        "calories_per_100g": 240,
        "cost_inr_per_100g": 6.0,
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "brown_rice": {
        "name": "Steamed Rice / Brown Rice (Cooked)",
        "protein_per_100g": 2.7,
        "carbs_per_100g": 28.0,
        "fats_per_100g": 0.3,
        "calories_per_100g": 130,
        "cost_inr_per_100g": 5.0,
        "diet_types": ["pure_veg", "eggetarian", "non_veg", "vegan"],
    },
    "whey_protein": {
        "name": "Whey Protein Concentrate (1 scoop = 33g)",
        "protein_per_100g": 75.0,
        "carbs_per_100g": 6.0,
        "fats_per_100g": 5.0,
        "calories_per_100g": 390,
        "cost_inr_per_100g": 200.0,  # ₹2000/kg -> ₹66 per scoop
        "diet_types": ["pure_veg", "eggetarian", "non_veg"],
    },
}


def generate_budget_diet_plan(
    goal: str = "recomposition",
    daily_budget_inr: float = 200.0,
    diet_type: str = "pure_veg",
    bodyweight_kg: float = 70.0,
    target_calories: Optional[int] = None,
    currency: str = "INR",
    diet_preference: Optional[str] = None,
    fitness_goal: Optional[str] = None,
    current_weight_kg: Optional[float] = None,
    gender: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a balanced, budget-conscious Indian & global diet plan.

    Args:
        goal: Training objective ('strength', 'recomposition', 'weight_gain'/'bulk', 'weight_loss'/'cut', 'endurance').
        daily_budget_inr: Daily budget in INR (₹) or USD if currency="USD".
        diet_type: Dietary preference ('pure_veg', 'eggetarian', 'non_veg', 'vegan').
        bodyweight_kg: User's bodyweight in kilograms (kg).
        target_calories: Optional explicit daily caloric goal.
        currency: 'INR' or 'USD'.
        diet_preference: Alias for diet_type.
        fitness_goal: Alias for goal.
        current_weight_kg: Alias for bodyweight_kg.
        gender: Optional gender ('male' or 'female').

    Returns:
        Structured meal plan, macronutrient distribution, itemized cost in INR & USD,
        and protein cost-efficiency rankings.
    """
    if fitness_goal:
        goal = fitness_goal
    if diet_preference:
        diet_type = diet_preference
    if current_weight_kg:
        bodyweight_kg = current_weight_kg

    if daily_budget_inr <= 0:
        return {"error": "Daily budget must be greater than 0."}

    if currency.strip().upper() == "USD":
        daily_budget_inr = daily_budget_inr * 85.0

    clean_goal = goal.strip().lower()
    clean_diet = diet_type.strip().lower().replace("-", "_").replace(" ", "_")
    if clean_diet not in ["pure_veg", "eggetarian", "non_veg", "vegan"]:
        clean_diet = "pure_veg"

    # Base BMR & TDEE Estimation (Harris-Benedict baseline for active lifters)
    bmr = 10 * bodyweight_kg + 6.25 * 175 - 5 * 25 + 5  # approx active male 25yo 175cm
    tdee = bmr * 1.55  # Moderate to heavy gym training

    # Caloric and Macronutrient Targets by Goal
    if "strength" in clean_goal:
        cals = int(target_calories or round(tdee + 250))
        protein_g_per_kg = 1.8
        fats_ratio = 0.25
        goal_title = "Strength & Powerlifting (Glycogen & Joint Support)"
    elif "recomp" in clean_goal:
        cals = int(target_calories or round(tdee))
        protein_g_per_kg = 2.2
        fats_ratio = 0.22
        goal_title = "Body Recomposition (Fat Loss & Lean Muscle Retention)"
    elif "gain" in clean_goal or "bulk" in clean_goal:
        cals = int(target_calories or round(tdee + 450))
        protein_g_per_kg = 2.0
        fats_ratio = 0.25
        goal_title = "Clean Hypertrophy Bulking (High Quality Mass)"
    elif "loss" in clean_goal or "cut" in clean_goal:
        cals = int(target_calories or round(tdee - 500))
        protein_g_per_kg = 2.2
        fats_ratio = 0.20
        goal_title = "Fat Loss & Shredding (Muscle Sparing Deficit)"
    elif "endurance" in clean_goal:
        cals = int(target_calories or round(tdee + 300))
        protein_g_per_kg = 1.6
        fats_ratio = 0.20
        goal_title = "Athletic Conditioning & Endurance"
    else:
        cals = int(target_calories or round(tdee + 200))
        protein_g_per_kg = 1.8
        fats_ratio = 0.25
        goal_title = f"{goal.capitalize()} Fitness Protocol"

    target_protein_g = round(bodyweight_kg * protein_g_per_kg, 1)
    target_fats_g = round((cals * fats_ratio) / 9.0, 1)
    remaining_cals = cals - (target_protein_g * 4.0) - (target_fats_g * 9.0)
    target_carbs_g = max(50.0, round(remaining_cals / 4.0, 1))

    # Select Meals based on Budget Tier & Diet Type
    # Tier 1 (Low Budget <= ₹150), Tier 2 (₹151 - ₹350), Tier 3 (₹351+)
    is_budget_tier = daily_budget_inr <= 160.0
    is_premium_tier = daily_budget_inr >= 360.0

    meals: List[Dict[str, Any]] = []
    total_cost_inr = 0.0

    if clean_diet == "pure_veg":
        # 1. Breakfast: High-fiber Oats or Daliya with Sattu / Milk
        if is_budget_tier:
            meals.append({
                "meal": "1. Power Breakfast",
                "timing": "8:00 AM",
                "items": [
                    "60g Sattu Sharbat (mixed in water with lemon & roasted cumin)",
                    "1 Banana + 50g Roasted Peanuts",
                ],
                "protein_g": 25.0,
                "carbs_g": 62.0,
                "fats_g": 26.0,
                "calories": 580,
                "cost_inr": 22.0,
            })
        else:
            meals.append({
                "meal": "1. Power Breakfast",
                "timing": "8:00 AM",
                "items": [
                    "70g Rolled Oats cooked with 200ml milk, 1 scoop Whey Protein, sliced banana & almonds",
                ],
                "protein_g": 38.0,
                "carbs_g": 72.0,
                "fats_g": 14.0,
                "calories": 560,
                "cost_inr": 85.0,
            })

        # 2. Lunch: Soya Chunks Curry + Rotis + Curd + Dal
        meals.append({
            "meal": "2. High-Protein Lunch",
            "timing": "1:00 PM",
            "items": [
                "60g Soya Chunks curry (cooked in light tomato-onion gravy) [31g Protein!]",
                "3 Whole Wheat Rotis / 150g Rice",
                "150g Fresh Desi Curd / Dahi",
                "Green salad with cucumber & carrots",
            ],
            "protein_g": 43.0,
            "carbs_g": 75.0,
            "fats_g": 10.0,
            "calories": 560,
            "cost_inr": 32.0,
        })

        # 3. Pre-Workout / Snack
        meals.append({
            "meal": "3. Pre-Workout Fuel",
            "timing": "4:30 PM (1h before gym)",
            "items": [
                "1 Black Coffee / Green Tea (zero cal)",
                "2 Bananas or 2 slices brown bread with 20g peanut butter",
            ],
            "protein_g": 7.0,
            "carbs_g": 54.0,
            "fats_g": 10.0,
            "calories": 330,
            "cost_inr": 18.0,
        })

        # 4. Post-Workout Recovery
        if is_budget_tier:
            meals.append({
                "meal": "4. Post-Workout Recovery",
                "timing": "6:45 PM (immediately after training)",
                "items": [
                    "50g Chana Sattu Drink with pinch of rock salt (Desi Whey)",
                    "100g Sprouted Moong Dal chaat with lime",
                ],
                "protein_g": 26.0,
                "carbs_g": 58.0,
                "fats_g": 5.0,
                "calories": 380,
                "cost_inr": 18.0,
            })
        else:
            meals.append({
                "meal": "4. Post-Workout Recovery",
                "timing": "6:45 PM",
                "items": [
                    "1 scoop Whey Protein in water",
                    "1 Banana / Rice Cakes for rapid glycogen replenishment",
                ],
                "protein_g": 26.0,
                "carbs_g": 30.0,
                "fats_g": 2.0,
                "calories": 240,
                "cost_inr": 72.0,
            })

        # 5. Dinner: Paneer / Tofu Bhurji with Rotis
        meals.append({
            "meal": "5. Muscle Repair Dinner",
            "timing": "8:45 PM",
            "items": [
                "120g Fresh Paneer or Tofu Bhurji with bell peppers",
                "2 Whole Wheat Rotis",
                "1 bowl thick Yellow Dal (Moong / Toor)",
            ],
            "protein_g": 34.0,
            "carbs_g": 55.0,
            "fats_g": 25.0,
            "calories": 580,
            "cost_inr": 55.0,
        })

    elif clean_diet in ["eggetarian", "non_veg"]:
        # Eggetarian / Non-Veg Blueprint
        # 1. Breakfast: Eggs + Toast / Oats
        meals.append({
            "meal": "1. Champion Breakfast",
            "timing": "8:00 AM",
            "items": [
                "3 Whole Eggs + 2 Egg Whites scrambled with spinach & tomatoes",
                "2 slices whole grain toast or 50g oatmeal",
            ],
            "protein_g": 32.0,
            "carbs_g": 35.0,
            "fats_g": 18.0,
            "calories": 430,
            "cost_inr": 38.0,
        })

        # 2. Lunch: Chicken Breast / Soya / Fish with Rice & Dal
        main_source = "150g Grilled / Curry Chicken Breast" if clean_diet == "non_veg" else "60g Soya Chunks curry + 2 Boiled Eggs"
        main_cost = 45.0 if clean_diet == "non_veg" else 28.0
        meals.append({
            "meal": "2. High-Anabolic Lunch",
            "timing": "1:00 PM",
            "items": [
                f"{main_source} [~42g Protein!]",
                "150g Steamed Rice / 2 Chapatis",
                "1 bowl Dal + large green salad",
            ],
            "protein_g": 48.0,
            "carbs_g": 60.0,
            "fats_g": 8.0,
            "calories": 510,
            "cost_inr": main_cost + 15.0,
        })

        # 3. Pre-Workout Fuel
        meals.append({
            "meal": "3. Pre-Workout Ignition",
            "timing": "4:30 PM",
            "items": [
                "Strong black coffee",
                "2 Bananas + 15g Roasted Peanuts or 1 Boiled Egg",
            ],
            "protein_g": 8.0,
            "carbs_g": 55.0,
            "fats_g": 7.0,
            "calories": 310,
            "cost_inr": 16.0,
        })

        # 4. Post-Workout Recovery
        if is_budget_tier:
            meals.append({
                "meal": "4. Post-Workout Fuel",
                "timing": "6:45 PM",
                "items": [
                    "4 Boiled Egg Whites + 1 Whole Egg",
                    "1 Sweet Potato (150g) or 2 Bananas",
                ],
                "protein_g": 22.0,
                "carbs_g": 45.0,
                "fats_g": 5.0,
                "calories": 310,
                "cost_inr": 35.0,
            })
        else:
            meals.append({
                "meal": "4. Post-Workout Anabolic Window",
                "timing": "6:45 PM",
                "items": [
                    "1 scoop Whey Protein in 250ml water",
                    "1 large Banana or 30g Dextrose/Rice Cakes",
                ],
                "protein_g": 26.0,
                "carbs_g": 32.0,
                "fats_g": 2.0,
                "calories": 250,
                "cost_inr": 72.0,
            })

        # 5. Dinner: Fish / Chicken / Paneer + Rotis + Curd
        dinner_meat = "150g Fish / Chicken Curry (Light Oil)" if clean_diet == "non_veg" else "120g Paneer / Tofu Bhurji + 2 Boiled Eggs"
        dinner_cost = 45.0 if clean_diet == "non_veg" else 50.0
        meals.append({
            "meal": "5. Restorative Dinner",
            "timing": "8:45 PM",
            "items": [
                dinner_meat,
                "2 Whole Wheat Rotis",
                "150g Desi Curd / Dahi (casein protein for overnight slow release)",
            ],
            "protein_g": 42.0,
            "carbs_g": 40.0,
            "fats_g": 16.0,
            "calories": 470,
            "cost_inr": dinner_cost + 18.0,
        })

    else:  # vegan
        # 1. Breakfast: Sattu drink + Oats + Tofu
        meals.append({
            "meal": "1. Vegan Power Breakfast",
            "timing": "8:00 AM",
            "items": [
                "60g Roasted Chana Sattu Drink with lemon & mint",
                "60g Oats with soy milk, chia seeds & banana",
            ],
            "protein_g": 28.0,
            "carbs_g": 78.0,
            "fats_g": 12.0,
            "calories": 530,
            "cost_inr": 35.0,
        })

        # 2. Lunch: Soya Chunks + Brown Rice + Dal
        meals.append({
            "meal": "2. Soya Protein Feast",
            "timing": "1:00 PM",
            "items": [
                "70g Soya Chunks cooked in tomato-ginger gravy [36g Protein!]",
                "150g Steamed Rice",
                "1 bowl thick Rajma / Chana curry",
            ],
            "protein_g": 48.0,
            "carbs_g": 85.0,
            "fats_g": 5.0,
            "calories": 580,
            "cost_inr": 30.0,
        })

        # 3. Pre-Workout Snack
        meals.append({
            "meal": "3. Pre-Workout Energy",
            "timing": "4:30 PM",
            "items": [
                "Black coffee",
                "30g Roasted Peanuts + 2 Bananas",
            ],
            "protein_g": 9.0,
            "carbs_g": 58.0,
            "fats_g": 15.0,
            "calories": 400,
            "cost_inr": 18.0,
        })

        # 4. Post-Workout Recovery
        meals.append({
            "meal": "4. Post-Workout Muscle Reload",
            "timing": "6:45 PM",
            "items": [
                "100g Sprouted Moong Dal Chaat",
                "40g Sattu with coconut water",
            ],
            "protein_g": 24.0,
            "carbs_g": 50.0,
            "fats_g": 4.0,
            "calories": 330,
            "cost_inr": 25.0,
        })

        # 5. Dinner: Tofu Scramble + Roti
        meals.append({
            "meal": "5. High-Protein Vegan Dinner",
            "timing": "8:45 PM",
            "items": [
                "150g Pan-seared Tofu with spinach & turmeric",
                "3 Whole Wheat Rotis",
                "1 bowl Mixed Dal",
            ],
            "protein_g": 38.0,
            "carbs_g": 62.0,
            "fats_g": 18.0,
            "calories": 560,
            "cost_inr": 60.0,
        })

    # Sum totals
    actual_protein = sum(m["protein_g"] for m in meals)
    actual_carbs = sum(m["carbs_g"] for m in meals)
    actual_fats = sum(m["fats_g"] for m in meals)
    actual_calories = sum(m["calories"] for m in meals)
    actual_cost_inr = sum(m["cost_inr"] for m in meals)
    actual_cost_usd = round(actual_cost_inr * INR_TO_USD, 2)

    # Cost-per-gram-of-protein calculation
    cost_per_gram_protein_inr = round(actual_cost_inr / max(1.0, actual_protein), 2)

    # Budget Tier categorization
    if daily_budget_inr <= 150:
        budget_tier = "Hostel / Student Budget (High-ROI)"
    elif daily_budget_inr <= 350:
        budget_tier = "Working Professional (Balanced)"
    else:
        budget_tier = "Elite / Premium Athlete"

    # Budget Health Check
    if actual_cost_inr <= daily_budget_inr:
        budget_status = "Within Budget"
        variance_status = "Within Budget"
    elif actual_cost_inr <= daily_budget_inr * 1.15:
        budget_status = "Slightly Over Budget"
        variance_status = "Slight Overage (<15%)"
    else:
        budget_status = "Over Budget"
        variance_status = "Exceeds Budget"

    budget_variance_inr = round(daily_budget_inr - actual_cost_inr, 2)
    rankings = calculate_cost_per_gram_protein(clean_diet)

    return {
        "status": "success",
        "fitness_goal": goal_title,
        "diet_preference": clean_diet.replace("_", " ").title(),
        "budget_tier": budget_tier,
        "daily_budget_inr": daily_budget_inr,
        "daily_budget_usd": round(daily_budget_inr * INR_TO_USD, 2),
        "actual_cost_inr": round(actual_cost_inr, 1),
        "actual_cost_usd": actual_cost_usd,
        "usd_cost_day": actual_cost_usd,
        "budget_status": budget_status,
        "budget_variance_status": variance_status,
        "budget_variance_inr": budget_variance_inr,
        "total_daily_protein_g": round(actual_protein, 1),
        "total_daily_calories": actual_calories,
        "macronutrients": {
            "calories_target": cals,
            "calories_actual": actual_calories,
            "protein_g_target": target_protein_g,
            "protein_g_actual": round(actual_protein, 1),
            "carbohydrates_g_actual": round(actual_carbs, 1),
            "fats_g_actual": round(actual_fats, 1),
            "cost_per_gram_protein_inr": cost_per_gram_protein_inr,
        },
        "cost_per_gram_protein_rankings": rankings,
        "meals": meals,
        "budget_hacks_for_gym_goers": [
            "Soya Chunks provide 52% protein at ₹15/100g — the highest protein-to-cost ratio in India (₹0.29 per gram of protein).",
            "Chana Sattu (Desi Whey) gives 21g protein per 100g with complex carbs and fiber for under ₹10 per serving.",
            "Buy whole eggs in crates (30 eggs for ~₹180–₹200) to cut egg costs to ₹6–6.50 each.",
            "Buy local dairy paneer in 1kg blocks from local dairies instead of packaged brand paneer to save up to 30%.",
            "Timing: Drink curd or consume slow-digesting casein/dairy before bed for sustained 8-hour amino acid delivery.",
        ],
    }


def calculate_cost_per_gram_protein(diet_preference: str = "all") -> List[Dict[str, Any]]:
    """Calculate and rank all Indian staple foods by cost-effectiveness per gram of protein.

    Args:
        diet_preference: 'Pure Veg', 'Eggetarian', 'Non-Veg', 'Vegan', or 'all'.

    Returns:
        List of foods ranked from cheapest cost-per-gram to most expensive.
    """
    clean = diet_preference.strip().lower().replace("-", "_").replace(" ", "_")
    if clean in ["pure_veg", "veg", "vegetarian"]:
        target_diet = "pure_veg"
    elif clean in ["vegan"]:
        target_diet = "vegan"
    elif clean in ["eggetarian"]:
        target_diet = "eggetarian"
    elif clean in ["non_veg", "nonveg"]:
        target_diet = "non_veg"
    else:
        target_diet = "all"

    results = []

    for name, food in STAPLE_FOODS.items():
        diet_types = food.get("diet_types", [])
        if target_diet != "all" and target_diet not in diet_types:
            continue

        protein_100g = food.get("protein_per_100g", 0.0)
        cost_100g = food.get("cost_inr_per_100g", 0.0)

        if protein_100g <= 0:
            continue

        cost_per_g = round(cost_100g / protein_100g, 2)
        results.append({
            "food": food["name"],
            "cost_per_gram_protein_inr": cost_per_g,
            "protein_per_100g": protein_100g,
            "cost_inr_per_100g": cost_100g,
        })

    results.sort(key=lambda x: x["cost_per_gram_protein_inr"])
    return results
