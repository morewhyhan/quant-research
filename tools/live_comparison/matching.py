"""Deterministic entry matching, not a claim of causal equivalence."""
from tools.data.time import timestamp


def match_trades(left, right, tolerance_seconds=300):
    if tolerance_seconds < 0:
        raise ValueError("tolerance must be nonnegative")
    for trade in left + right:
        if not trade.get("pair") or not isinstance(trade.get("is_short"), bool):
            raise ValueError("Matching requires pair and boolean is_short")
        timestamp(trade["open_date"])
    used, rows = set(), []
    for i, a in enumerate(left):
        candidates = []
        for j, b in enumerate(right):
            if j in used or a["pair"] != b["pair"] or a["is_short"] != b["is_short"]:
                continue
            delta = abs((timestamp(a["open_date"]) - timestamp(b["open_date"])).total_seconds())
            if delta <= tolerance_seconds:
                candidates.append((delta, j))
        if not candidates:
            rows.append({"left_index": i, "right_index": None})
            continue
        delta, j = min(candidates)
        used.add(j)
        b = right[j]
        exit_delta = None
        if a.get("close_date") and b.get("close_date"):
            exit_delta = (timestamp(b["close_date"]) - timestamp(a["close_date"])).total_seconds()
        rows.append({"left_index": i, "right_index": j, "entry_abs_seconds": delta,
                     "exit_right_minus_left_seconds": exit_delta,
                     "left_profit_abs": a["profit_abs"], "right_profit_abs": b["profit_abs"],
                     "same_exit_reason": a.get("exit_reason") == b.get("exit_reason")})
    return {"method": "left-order greedy nearest entry; one-to-one; deterministic index tie-break",
            "tolerance_seconds": tolerance_seconds, "matched": len(used),
            "unmatched_left": len(left) - len(used), "unmatched_right": len(right) - len(used), "rows": rows}
