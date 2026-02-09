import hashlib
from datetime import date
from itertools import product
from bson import ObjectId

# ============================================================
# Parameterized Opportunity Generator
# ACTIONS x CONTEXTS x TARGETS x CONSTRAINTS = 5,000+ combos
# ============================================================

ACTIONS = [
    {"id": "ask_discount", "label": "Ask for a discount", "verb": "Ask for a discount", "diff_mod": 0},
    {"id": "ask_feedback", "label": "Request feedback", "verb": "Request feedback on your work", "diff_mod": 1},
    {"id": "pitch", "label": "Pitch your idea", "verb": "Pitch your idea", "diff_mod": 1},
    {"id": "cold_outreach", "label": "Cold outreach", "verb": "Reach out cold", "diff_mod": 2},
    {"id": "negotiate", "label": "Negotiate", "verb": "Negotiate a deal", "diff_mod": 1},
    {"id": "ask_favor", "label": "Ask for a favor", "verb": "Ask for a favor", "diff_mod": 0},
    {"id": "request_meeting", "label": "Request a meeting", "verb": "Request a meeting", "diff_mod": 1},
    {"id": "submit_work", "label": "Submit your work", "verb": "Submit your work", "diff_mod": 1},
    {"id": "volunteer", "label": "Volunteer yourself", "verb": "Volunteer yourself", "diff_mod": 0},
    {"id": "challenge", "label": "Challenge a decision", "verb": "Challenge a decision", "diff_mod": 2},
]

CONTEXTS = [
    {"id": "in_person", "label": "in person", "diff_mod": 1},
    {"id": "by_email", "label": "by email", "diff_mod": 0},
    {"id": "by_phone", "label": "by phone", "diff_mod": 1},
    {"id": "on_social", "label": "on social media", "diff_mod": 0},
    {"id": "at_event", "label": "at a live event", "diff_mod": 1},
    {"id": "at_work", "label": "at work", "diff_mod": 1},
    {"id": "in_public", "label": "in a public setting", "diff_mod": 1},
    {"id": "on_video", "label": "on a video call", "diff_mod": 0},
]

TARGETS = [
    {"id": "stranger", "label": "a stranger", "diff_mod": 1, "domains": ["social", "general"]},
    {"id": "friend", "label": "a friend", "diff_mod": 0, "domains": ["social", "general"]},
    {"id": "boss", "label": "your boss", "diff_mod": 2, "domains": ["career", "general"]},
    {"id": "client", "label": "a client or customer", "diff_mod": 1, "domains": ["sales", "entrepreneurship"]},
    {"id": "expert", "label": "an industry expert", "diff_mod": 2, "domains": ["career", "networking"]},
    {"id": "creator", "label": "a content creator", "diff_mod": 1, "domains": ["creative", "networking"]},
    {"id": "investor", "label": "an investor", "diff_mod": 3, "domains": ["entrepreneurship", "sales"]},
    {"id": "service_provider", "label": "a service provider", "diff_mod": 0, "domains": ["general", "sales"]},
    {"id": "colleague", "label": "a colleague", "diff_mod": 0, "domains": ["career", "social"]},
    {"id": "executive", "label": "a company executive", "diff_mod": 3, "domains": ["career", "networking"]},
]

CONSTRAINTS = [
    {"id": "cold", "label": "with no prior relationship", "diff_mod": 2},
    {"id": "same_day", "label": "and get a response today", "diff_mod": 1},
    {"id": "face_to_face", "label": "face to face", "diff_mod": 1},
    {"id": "with_followup", "label": "and follow up within 48 hours", "diff_mod": 0},
    {"id": "in_writing", "label": "with a written proposal", "diff_mod": 0},
    {"id": "no_script", "label": "without any script or notes", "diff_mod": 1},
    {"id": "group_setting", "label": "in front of a group", "diff_mod": 2},
    {"id": "on_the_spot", "label": "on the spot with no preparation", "diff_mod": 1},
]

# Incompatible pairs: (action_id/context_id/target_id, action_id/context_id/target_id)
INCOMPATIBLE = {
    # Can't do face-to-face constraint with email/social/video contexts
    ("by_email", "face_to_face"),
    ("on_social", "face_to_face"),
    ("on_video", "face_to_face"),
    # Can't negotiate with a friend easily (too awkward framing)
    ("negotiate", "friend"),
    # Can't cold outreach a colleague (you already know them)
    ("cold_outreach", "colleague"),
    # Can't challenge an investor (wrong dynamic)
    ("challenge", "investor"),
    # Can't do in-person context with email constraint
    ("by_email", "in_person"),
    ("by_phone", "in_person"),
    # "with no prior relationship" doesn't work for boss/colleague
    ("boss", "cold"),
    ("colleague", "cold"),
    ("friend", "cold"),
    # Can't submit work "on the spot with no preparation"
    ("submit_work", "on_the_spot"),
    # Can't negotiate on social media (too informal)
    ("negotiate", "on_social"),
}


def _is_compatible(action, context, target, constraint):
    ids = {action["id"], context["id"], target["id"], constraint["id"]}
    for a, b in INCOMPATIBLE:
        if a in ids and b in ids:
            return False
    return True


def _compute_difficulty(action, context, target, constraint):
    raw = 1 + action["diff_mod"] + context["diff_mod"] + target["diff_mod"] + constraint["diff_mod"]
    return max(1, min(4, round(raw / 2.5)))


def _make_combo_id(action, context, target, constraint):
    return f"{action['id']}:{context['id']}:{target['id']}:{constraint['id']}"


def _make_description(action, context, target, constraint):
    return f"{action['verb']} to {target['label']} {context['label']} {constraint['label']}."


def _make_title(action, context, target, constraint):
    return f"{action['label']} — {target['label']} ({context['label']})"


def _get_domains(action, target):
    domains = set(target.get("domains", ["general"]))
    # Add domain hints based on action
    action_domains = {
        "pitch": ["entrepreneurship"],
        "negotiate": ["sales"],
        "submit_work": ["creative", "writing"],
        "volunteer": ["career"],
        "cold_outreach": ["networking"],
    }
    for d in action_domains.get(action["id"], []):
        domains.add(d)
    if len(domains) == 0:
        domains.add("general")
    return sorted(domains)


def generate_opportunity(action, context, target, constraint):
    return {
        "combo_id": _make_combo_id(action, context, target, constraint),
        "title": _make_title(action, context, target, constraint),
        "description": _make_description(action, context, target, constraint),
        "difficulty": _compute_difficulty(action, context, target, constraint),
        "domains": _get_domains(action, target),
        "source": "generated",
        "components": {
            "action": action["label"],
            "context": context["label"],
            "target": target["label"],
            "constraint": constraint["label"],
        },
    }


def get_all_valid_combinations():
    combos = []
    for action, context, target, constraint in product(ACTIONS, CONTEXTS, TARGETS, CONSTRAINTS):
        if _is_compatible(action, context, target, constraint):
            combos.append(generate_opportunity(action, context, target, constraint))
    return combos


def _deterministic_shuffle(items, seed_str):
    def sort_key(item):
        h = hashlib.md5((seed_str + item["combo_id"]).encode()).hexdigest()
        return h
    return sorted(items, key=sort_key)


def get_opportunities_for_user(db, user_id, count=10, domain=None, difficulty=None, min_difficulty=None):
    # Ensure user_id is ObjectId for queries
    uid = ObjectId(user_id) if isinstance(user_id, str) else user_id

    # Get user's completed combos
    completed = set()
    if db is not None:
        cursor = db.completed_combos.find(
            {"user_id": uid},
            {"combo_id": 1}
        )
        completed = {doc["combo_id"] for doc in cursor}

    # Get user's total_nos for progressive difficulty
    if db is not None and min_difficulty is None:
        user_doc = db.users.find_one({"_id": uid})
        if user_doc:
            total_nos = user_doc.get("total_nos", 0)
            if total_nos >= 500:
                min_difficulty = 3
            elif total_nos >= 200:
                min_difficulty = 2
            else:
                min_difficulty = 1

    all_combos = get_all_valid_combinations()

    # Filter out completed
    available = [c for c in all_combos if c["combo_id"] not in completed]

    # Filter by domain
    if domain:
        available = [c for c in available if domain in c["domains"]]

    # Filter by difficulty
    if difficulty is not None:
        available = [c for c in available if c["difficulty"] == difficulty]
    elif min_difficulty is not None and min_difficulty > 1:
        available = [c for c in available if c["difficulty"] >= min_difficulty]

    # Deterministic shuffle per user + date
    seed = f"{user_id}:{date.today().isoformat()}"
    shuffled = _deterministic_shuffle(available, seed)

    return shuffled[:count]
