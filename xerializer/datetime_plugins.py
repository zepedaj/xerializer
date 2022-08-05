from .builtin_plugins import _BuiltinTypeSerializer
import numpy as np
import datetime
import pytz


class _PytzTZinfoSerializer:
    signature = "pytz.timezone"

    def as_serializable(self, obj):
        return {"name": str(obj)}

    def from_serializable(cls, name):
        return pytz.timezone(name)


for _tzname in pytz.all_timezones:
    # Register all pytz timezone classes.
    globals()[_tzname] = type(
        _tzname,
        (_PytzTZinfoSerializer, _BuiltinTypeSerializer),
        {
            "handled_type": type(pytz.timezone(_tzname)),
            "__module__": __name__,
            "register": True,
        },
    )


# Register datetime's datetime, timedelta and tzinfo.
class DatetimeSerializer(_BuiltinTypeSerializer):
    signature = "datetime"
    handled_type = datetime.datetime
    register = True

    def as_serializable(self, obj):
        out = {"value": obj.replace(tzinfo=None).isoformat()}
        if obj.tzinfo:
            out["timezone"] = obj.tzinfo
        return out

    def from_serializable(self, value, timezone=None):
        # One could also use datetime.datetime.fromisoformat(value).replace(tzinfo=timezone)
        # but that fromisformat does not support second decimals with  other than 3 or 6 positions.
        return np.datetime64(value).item().replace(tzinfo=timezone)
