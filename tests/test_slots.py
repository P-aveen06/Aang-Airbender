from aang_airbender.slots import LatestValueSlot


def test_latest_value_slot_overwrites_stale_values() -> None:
    slot = LatestValueSlot[int]()
    first_version = slot.publish(1)
    latest_version = slot.publish(2)

    assert latest_version == first_version + 1
    assert slot.get_after(0) == (latest_version, 2)
    assert slot.get_after(latest_version) is None
