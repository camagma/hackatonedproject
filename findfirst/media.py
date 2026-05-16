import base64
import urllib.parse


CASE_CONTEXT_PHOTOS = {
    "Flood": "https://picsum.photos/seed/findfirst-flood-water/320/320",
    "Wildfire": "https://picsum.photos/seed/findfirst-wildfire-field/320/320",
    "Mountain / Forest": "https://picsum.photos/seed/findfirst-mountain-forest/320/320",
    "Urban Area": "https://picsum.photos/seed/findfirst-urban-search/320/320",
    "Missing Person": "https://picsum.photos/seed/findfirst-search-path/320/320",
    "Other": "https://picsum.photos/seed/findfirst-rescue-field/320/320",
}

COMMONS_FILE_BASE = "https://commons.wikimedia.org/wiki/Special:Redirect/file/"

NAV_PHOTO_FILES = {
    "dashboard": "Font Awesome 5 solid tachometer-alt.svg",
    "my_missions": "Font Awesome 5 solid bullseye.svg",
    "all_cases": "Font Awesome 5 solid folder-open.svg",
    "teams": "Font Awesome 5 solid users.svg",
    "volunteers": "Font Awesome 5 solid user-friends.svg",
    "tracking": "Font Awesome 5 solid map-marker-alt.svg",
    "ai_log": "Font Awesome 5 solid robot.svg",
    "report_case": "Font Awesome 5 solid clipboard-list.svg",
    "my_cases": "Font Awesome 5 solid folder-open.svg",
}

CASE_CONTEXT_ICONS = {
    "Flood": "Font Awesome 5 solid tint.svg",
    "Wildfire": "Font Awesome 5 solid fire.svg",
    "Mountain / Forest": "Font Awesome 5 solid mountain.svg",
    "Urban Area": "Font Awesome 5 solid city.svg",
    "Missing Person": "Font Awesome 5 solid user.svg",
    "Other": "Font Awesome 5 solid map-marked-alt.svg",
}


def avatar_initials(name):
    parts = name.split()
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()


def uploaded_image_to_data_url(uploaded_file):
    if uploaded_file is None:
        return None
    file_bytes = uploaded_file.getvalue()
    mime = uploaded_file.type or "image/jpeg"
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def commons_file_url(filename: str, width: int = 96) -> str:
    return f"{COMMONS_FILE_BASE}{urllib.parse.quote(filename)}?width={width}"


def nav_photo_url(page_id: str) -> str:
    return commons_file_url(NAV_PHOTO_FILES.get(page_id, NAV_PHOTO_FILES["dashboard"]))


def case_photo_html(case: dict, is_dark: bool = False) -> str:
    uploaded = case.get("photo_data_url")
    if uploaded:
        return f'<img class="missing-photo" src="{uploaded}" alt="Missing person photo">'
    category = case.get("category", "Other")
    if is_dark:
        icon = commons_file_url(CASE_CONTEXT_ICONS.get(category, CASE_CONTEXT_ICONS["Other"]), 96)
        safe_label = category.replace("/", " / ")
        return f'<div class="missing-photo missing-photo-fallback" aria-label="{safe_label}"><img src="{icon}" alt=""><span>{safe_label}</span></div>'
    url = CASE_CONTEXT_PHOTOS.get(category, CASE_CONTEXT_PHOTOS["Other"])
    return f'<img class="missing-photo missing-photo-context" src="{url}" alt="{category} context photo" loading="lazy">'
