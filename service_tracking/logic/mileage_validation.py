"""
Detects suspicious mileage entries before they're saved:
  - New reading lower than the previous reading.
  - Extremely large jump since the previous reading.
  - Duplicate reading (same value as the previous one, same day).
Callers should surface these as a confirmation step rather than a hard block.
"""

LARGE_JUMP_KM = 5000  # a single day/update jumping more than this is flagged for confirmation


def check_mileage(vehicle, new_reading, recorded_date):
    """Return (is_suspicious: bool, reason: str)."""
    latest = vehicle.latest_mileage_update

    if latest is None:
        return False, ""

    if new_reading < latest.odometer_reading:
        return True, (
            f"New reading ({new_reading:,} KM) is lower than the last recorded "
            f"reading ({latest.odometer_reading:,} KM)."
        )

    if new_reading == latest.odometer_reading and recorded_date == latest.recorded_date:
        return True, "This looks like a duplicate of the most recent mileage entry."

    jump = new_reading - latest.odometer_reading
    if jump > LARGE_JUMP_KM:
        return True, (
            f"This is a jump of {jump:,} KM since the last reading "
            f"({latest.odometer_reading:,} KM on {latest.recorded_date}), which is unusually large."
        )

    return False, ""
