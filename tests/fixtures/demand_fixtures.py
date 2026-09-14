"""
Demand-estimation fixtures D1-D4.

SIMULATED ILLUSTRATIVE FIXTURE DATA -- every value below is invented for
testing only and does not represent a real vendor.

Authoritative source: reports/phase5g_implementation_fixtures.md, Section 4.
"""

# --- D1: Cold Start with Valid Peers ---
# Purpose: same-category peer average when no own history exists.
D1_PEER_Q_VALUES = [8.0, 10.0, 9.0]
D1_EXPECTED_Q_I = 9.0

# --- D2: Limited History ---
# Purpose: moving-average-3 applies because >=3 usable records exist.
# Deliberately differs from the last-observed-value (8) to prove the
# correct method (moving average, not last-observed) is applied.
D2_DIARY_RECORDS = [6.0, 9.0, 8.0]  # chronological, most recent last
D2_EXPECTED_Q_I = 7.666666666666667  # (6+9+8)/3
D2_LAST_OBSERVED_VALUE_WOULD_BE = 8.0  # explicitly NOT the expected result

# --- D3: Insufficient Evidence ---
# Purpose: no own history and zero same-category peers -> ABSTAIN.
D3_DIARY_RECORDS: list = []
D3_PEER_Q_VALUES: list = []

# --- D4: Invalid/Missing Critical Input ---
# Purpose: a negative submitted quantity is a VALIDATION ERROR, distinct
# from D3's ABSTAIN (a well-formed but empty submission).
D4_INVALID_DIARY_RECORDS = [-5.0]
