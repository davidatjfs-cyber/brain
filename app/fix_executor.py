from app.auto_fix_engine import apply_fix, save_fix_record, get_fix_stats


def run_auto_fix(reasons: list) -> dict:
    if not reasons:
        return {
            "applied": False,
            "reason": "No failure reasons to fix",
        }

    result = apply_fix(reasons)

    if result["fix_count"] > 0:
        save_fix_record(result["applied_fixes"], reasons)

    return {
        "applied": result["fix_count"] > 0,
        "fix_count": result["fix_count"],
        "applied_fixes": result["applied_fixes"],
        "updated_params": result["updated_params"],
    }


def get_auto_fix_stats() -> dict:
    return get_fix_stats()
