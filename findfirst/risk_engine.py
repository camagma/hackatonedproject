from datetime import datetime

from .geo import haversine
from .weather import WEATHER_ICONS, WEATHER_MODIFIERS


CLOSED_CASE_STATUSES = {"found", "closed", "unfound"}

INCIDENT_BASE_RISK = {
    "Flood": 38,
    "Wildfire": 45,
    "Mountain / Forest": 38,
    "Urban Area": 24,
    "Missing Person": 30,
    "Other": 25,
}

LOCATION_RISK_RULES = [
    ("water nearby", 16, ["river", "lake", "pond", "canal", "harbor", "sea", "beach", "bridge", "dam", "waterfall", "flood", "riverside"], ["Dive Rescue"]),
    ("remote terrain", 14, ["forest", "woods", "mountain", "trail", "valley", "cliff", "cave", "ravine", "wilderness", "park"], ["Mountain Rescue", "Forest / Wilderness"]),
    ("fire fuel zone", 10, ["dry grass", "wildfire", "smoke", "burn", "brush", "campfire"], ["Firefighter"]),
    ("industrial hazard", 9, ["factory", "warehouse", "construction", "abandoned", "rail", "station", "tunnel", "substation"], ["General Search"]),
    ("traffic corridor", 8, ["highway", "road", "motorway", "parking", "intersection", "bus stop"], ["General Search"]),
    ("dense urban area", 5, ["mall", "market", "downtown", "metro", "subway", "apartment", "school", "stadium"], ["General Search"]),
]

CIRCUMSTANCE_RISK_RULES = [
    ("medical vulnerability", 18, ["diabetes", "diabetic", "insulin", "heart", "seizure", "epilepsy", "dementia", "alzheimer", "autism", "medication"], ["Paramedic / Medic"]),
    ("reported injury", 18, ["injured", "bleeding", "broken", "fall", "collapsed", "unconscious", "hypothermia", "heatstroke"], ["Paramedic / Medic"]),
    ("violence or coercion concern", 20, ["abduct", "kidnap", "violence", "threat", "attack", "domestic", "stalker"], ["General Search"]),
    ("lost communication", 8, ["phone off", "no signal", "battery dead", "not answering", "last call"], ["General Search"]),
    ("low visibility or exposure", 10, ["night", "dark", "storm", "snow", "fog", "cold", "heat", "rain"], ["General Search"]),
]

DISASTER_TEAMS = {
    "Flood": {"icon": "🌊", "required": ["Dive Rescue"], "preferred": ["Paramedic / Medic", "General Search"], "size": 3, "note": "Dive team + medic + support"},
    "Wildfire": {"icon": "🔥", "required": ["Firefighter"], "preferred": ["Paramedic / Medic", "Mountain Rescue"], "size": 4, "note": "Fire suppression + evacuation + medic"},
    "Mountain / Forest": {"icon": "⛰️", "required": ["Mountain Rescue"], "preferred": ["K9 Handler", "Paramedic / Medic"], "size": 3, "note": "Alpine specialists + K9"},
    "Urban Area": {"icon": "🏙️", "required": ["General Search"], "preferred": ["Paramedic / Medic", "K9 Handler"], "size": 2, "note": "Search team + medic"},
    "Missing Person": {"icon": "🔍", "required": ["General Search"], "preferred": ["K9 Handler", "Paramedic / Medic"], "size": 2, "note": "Search + K9 tracker"},
    "Other": {"icon": "🚨", "required": [], "preferred": ["General Search", "Paramedic / Medic"], "size": 2, "note": "General response team"},
}

SKILL_GROUPS = {
    "Dive Rescue": ["Dive Rescue"],
    "Firefighter": ["Firefighter"],
    "Mountain Rescue": ["Mountain Rescue", "Forest / Wilderness"],
    "Forest / Wilderness": ["Forest / Wilderness", "Mountain Rescue"],
    "K9 Handler": ["K9 Handler"],
    "Paramedic / Medic": ["Paramedic / Medic"],
    "General Search": ["General Search", "Forest / Wilderness", "Mountain Rescue", "K9 Handler"],
}


def get_priority(score):
    if score >= 85:
        return "CRITICAL", "critical"
    if score >= 65:
        return "HIGH", "high"
    if score >= 40:
        return "MEDIUM", "medium"
    return "LOW", "low"


def clamp_score(value, low=0, high=100):
    return max(low, min(high, int(round(value))))


def is_case_closed(case: dict) -> bool:
    return case.get("status") in CLOSED_CASE_STATUSES


def is_case_active(case: dict) -> bool:
    return not is_case_closed(case)


def get_time_risk():
    hour = datetime.now().hour
    if 21 <= hour or hour < 5:
        return 20, "🌙 Night"
    if 5 <= hour < 7 or 18 <= hour < 21:
        return 10, "🌆 Dusk/Dawn"
    return 0, "☀️ Daytime"


def hours_missing_risk(hours):
    value = float(hours or 0)
    if value <= 1:
        return 0
    if value <= 3:
        return 4
    if value <= 6:
        return 8
    if value <= 12:
        return 14
    if value <= 24:
        return 22
    if value <= 48:
        return 30
    if value <= 72:
        return 38
    return 45


def age_risk(age):
    value = int(age or 0)
    if value <= 5:
        return 24, "very young child"
    if value <= 11:
        return 18, "child"
    if value <= 17:
        return 8, "teen"
    if value >= 75:
        return 18, "elderly adult"
    if value >= 60:
        return 14, "senior"
    return 0, "adult"


def collect_rule_hits(text, rules):
    hits, points, skills = [], 0, []
    lower = (text or "").lower()
    for label, pts, keywords, needed in rules:
        if any(keyword in lower for keyword in keywords):
            hits.append(label)
            points += pts
            skills.extend(needed)
    return hits, points, skills


def deterministic_case_risk(case, ensure_weather):
    category = case.get("category", "Other")
    weather_info = ensure_weather(case)
    weather = weather_info.get("category", "Clear")
    base = INCIDENT_BASE_RISK.get(category, INCIDENT_BASE_RISK["Other"])
    weather_points = WEATHER_MODIFIERS.get(weather, {}).get(category, 0)
    time_points, time_label = get_time_risk()
    missing_points = hours_missing_risk(case.get("time_missing", 0))
    age_points, age_label = age_risk(case.get("age", 0))
    text = f"{case.get('location', '')} {case.get('description', '')}"
    loc_hits, loc_points, loc_skills = collect_rule_hits(text, LOCATION_RISK_RULES)
    circumstance_hits, circumstance_points, circumstance_skills = collect_rule_hits(text, CIRCUMSTANCE_RISK_RULES)
    if case.get("location_source") != "map" and not (case.get("location") or "").strip():
        loc_hits.append("unknown last location")
        loc_points += 18
    elif case.get("location_source") != "map" and len((case.get("location") or "").strip()) < 8:
        loc_hits.append("vague last location")
        loc_points += 12
    if category == "Flood" and "water nearby" in loc_hits:
        loc_points += 8
        loc_hits.append("flood-water location match")
    if category == "Wildfire" and ("remote terrain" in loc_hits or "fire fuel zone" in loc_hits):
        loc_points += 10
        loc_hits.append("wildfire fuel/terrain match")
    if category == "Mountain / Forest" and "remote terrain" in loc_hits:
        loc_points += 8
        loc_hits.append("mountain/forest location match")
    raw = base + weather_points + time_points + missing_points + age_points + loc_points + circumstance_points
    score = clamp_score(raw, 5, 100)
    label, _ = get_priority(score)
    spec = DISASTER_TEAMS.get(category, DISASTER_TEAMS["Other"])
    required = []
    for skill in spec.get("required", []) + loc_skills + circumstance_skills + spec.get("preferred", [])[:1]:
        if skill and skill not in required:
            required.append(skill)
    if not required:
        required = ["General Search"]
    factors = [
        f"{category} baseline +{base}",
        f"{weather} weather {weather_points:+d}",
        f"{case.get('time_missing', 0)}h missing +{missing_points}",
        f"age {case.get('age', 0)} ({age_label}) +{age_points}",
        f"{time_label} +{time_points}",
    ]
    factors.extend([f"location: {item}" for item in loc_hits])
    factors.extend([f"circumstance: {item}" for item in circumstance_hits])
    radius = 1.0
    if category in ["Mountain / Forest", "Flood", "Wildfire"]:
        radius = 2.5
    radius += min(8.0, float(case.get("time_missing") or 0) * 0.18)
    if "remote terrain" in loc_hits:
        radius += 1.5
    action = {
        "CRITICAL": "Dispatch immediately, form a multi-skill team, and start high-priority field search.",
        "HIGH": "Assign a team now and begin structured search from the last known location.",
        "MEDIUM": "Open active search, verify last-seen details, and monitor escalation triggers.",
        "LOW": "Log report, verify details, and keep volunteers on standby.",
    }[label]
    reasoning = (
        f"Risk is {score}/100 ({label}) from {category.lower()} baseline, "
        f"{weather.lower()} weather, {case.get('time_missing', 0)} hours missing, "
        f"age {case.get('age', 0)} ({age_label}), and last-location hazards: {', '.join(loc_hits) if loc_hits else 'none detected'}."
    )
    return {
        "priority_score": score,
        "reasoning": reasoning,
        "required_skills": required,
        "risk_factors": factors,
        "recommended_action": action,
        "estimated_search_radius_km": round(radius, 1),
        "risk_breakdown": {
            "base_points": base,
            "weather": weather,
            "weather_points": weather_points,
            "time_of_day_label": time_label,
            "time_of_day_points": time_points,
            "hours_missing_points": missing_points,
            "age_points": age_points,
            "location_points": loc_points,
            "circumstance_points": circumstance_points,
            "raw_score": raw,
        },
    }


def compute_dynamic_risk(case, ensure_weather):
    weather_info = ensure_weather(case, persist=True)
    weather = weather_info.get("category", "Clear")
    weather_modifier = WEATHER_MODIFIERS.get(weather, {}).get(case.get("category", "Other"), 0)
    time_modifier, time_label = get_time_risk()
    breakdown = case.get("risk_breakdown") or {}
    if breakdown:
        total = (weather_modifier - int(breakdown.get("weather_points", 0))) + (time_modifier - int(breakdown.get("time_of_day_points", 0)))
    else:
        total = weather_modifier + time_modifier
    effective = clamp_score(case["priority_score"] + total)
    effective_label, effective_class = get_priority(effective)
    return {
        "weather": weather,
        "w_icon": WEATHER_ICONS.get(weather, ""),
        "w_mod": weather_modifier,
        "t_mod": time_modifier,
        "total": total,
        "effective": effective,
        "eff_label": effective_label,
        "eff_cls": effective_class,
        "t_label": time_label,
    }


def skill_match_level(vol_skill: str, desired_skills: list[str]) -> int:
    if not desired_skills:
        return 1
    if vol_skill in desired_skills:
        return 0
    compatible = set()
    for skill in desired_skills:
        compatible.update(SKILL_GROUPS.get(skill, [skill]))
    return 1 if vol_skill in compatible else 2


def unique_roles(roles: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for role in roles:
        key = (role["label"], tuple(role.get("skills", [])))
        if key not in seen:
            seen.add(key)
            result.append(role)
    return result


def team_requirements_for_case(case: dict, compute_dynamic):
    spec = DISASTER_TEAMS.get(case.get("category", "Other"), DISASTER_TEAMS["Other"])
    dynamic = compute_dynamic(case)
    effective = dynamic["effective"]
    weather = dynamic["weather"]
    age = int(case.get("age") or 0)
    hours_missing = float(case.get("time_missing") or 0)
    roles = []
    for skill in spec["required"]:
        roles.append({"label": skill, "skills": [skill], "priority": "required"})
    for skill in case.get("required_skills", []):
        if skill in SKILL_GROUPS:
            roles.append({"label": skill, "skills": [skill], "priority": "ai"})
    for skill in spec["preferred"]:
        roles.append({"label": skill, "skills": [skill], "priority": "preferred"})
    if effective >= 65 or age < 12 or age >= 60:
        roles.append({"label": "Medical cover", "skills": ["Paramedic / Medic"], "priority": "risk"})
    if effective >= 85 or dynamic["total"] >= 20:
        roles.append({"label": "Search lead", "skills": ["General Search", "Mountain Rescue"], "priority": "risk"})
    if case.get("category") == "Wildfire" or weather == "Extreme Heat":
        roles.append({"label": "Fire suppression", "skills": ["Firefighter"], "priority": "risk"})
        roles.append({"label": "Evacuation medic", "skills": ["Paramedic / Medic"], "priority": "risk"})
    if case.get("category") == "Flood" or weather in ["Rain", "Storm"]:
        roles.append({"label": "Water rescue", "skills": ["Dive Rescue"], "priority": "risk"})
    if case.get("category") == "Mountain / Forest" or weather in ["Snow", "Fog"]:
        roles.append({"label": "Terrain search", "skills": ["Mountain Rescue", "Forest / Wilderness"], "priority": "risk"})
    if hours_missing >= 6:
        roles.append({"label": "Tracker", "skills": ["K9 Handler", "General Search"], "priority": "risk"})
    base_size = spec["size"]
    if effective >= 85:
        target_size = base_size + 1
    elif effective >= 65 or dynamic["total"] >= 15:
        target_size = base_size
    else:
        target_size = max(1, base_size - 1)
    target_size = min(5, max(1, target_size))
    roles = unique_roles(roles)
    while len(roles) < target_size:
        roles.append({"label": "Support search", "skills": ["General Search", "Mountain Rescue", "Forest / Wilderness"], "priority": "support"})
    return roles[:target_size]


def volunteer_team_score(vol: dict, case: dict, role: dict) -> tuple:
    distance = haversine(vol["lat"], vol["lon"], case["lat"], case["lon"])
    match_level = skill_match_level(vol.get("skill", ""), role.get("skills", []))
    online_penalty = 0 if vol.get("online_status") == "online" else 8
    status_penalty = 0 if vol.get("status") == "active" else 100
    priority_penalty = {"required": 0, "ai": 3, "risk": 5, "preferred": 8, "support": 12}.get(role.get("priority"), 10)
    skill_penalty = [0, 15, 45][match_level]
    return status_penalty + online_penalty + priority_penalty + skill_penalty + distance * 4, match_level, distance


def build_team_for_case(case, available_vols, team_requirements=team_requirements_for_case, score_volunteer=volunteer_team_score):
    roles = team_requirements(case)
    assigned = []
    remaining = [v for v in available_vols if v.get("status") == "active" and v.get("online_status") != "offline"]
    for role in roles:
        if not remaining:
            break
        best = min(remaining, key=lambda v: score_volunteer(v, case, role))
        score = score_volunteer(best, case, role)
        match_level, distance = score[1], score[2]
        match_label = ["skill match", "compatible skill", "nearest cover"][match_level]
        role_icon = {"required": "🔴", "ai": "🧠", "risk": "⚠️", "preferred": "🟡", "support": "🔵"}.get(role.get("priority"), "🔵")
        assigned.append((best, f"{role_icon} {role['label']} · {distance:.1f}km · {match_label}"))
        remaining = [v for v in remaining if v["id"] != best["id"]]
    return assigned
