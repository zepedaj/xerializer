from xerializer import Serializer
import pytz


def test_all_timezones():
    serializer = Serializer()

    for tz_name in pytz.all_timezones:
        tz = pytz.timezone(tz_name)
        dsrlzd_tz = serializer.deserialize(x := serializer.serialize(tz))
        assert dsrlzd_tz is tz
