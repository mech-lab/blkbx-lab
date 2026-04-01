from hybrid_mechlab import profiles, schedules


def test_native_portfolio_profiles_conform():
    for profile in profiles.all_native():
        report = profile.conformance()
        assert report.passed is True
        assert report.bridge_count >= 1


def test_reference_profiles_have_understanding_first_lane():
    for profile in profiles.all_reference():
        assert profile.family.lane == schedules.PortfolioLane.understanding_first


def test_custom_schedule_nonempty():
    family = schedules.family_descriptor(schedules.TransportFamilyKind.custom)
    sched = schedules.custom_schedule(
        [
            schedules.TransportRegimeKind.recurrent_transport,
            schedules.TransportRegimeKind.global_bridge,
        ],
        family=family,
    )
    assert len(sched.ops) == 2
    assert sched.bridge_mask() == [False, True]
