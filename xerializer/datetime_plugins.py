""" Serializers for datetime module classes. """
from .builtin_plugins import _BuiltinTypeSerializer
import numpy as np
import datetime
import pytz


class _PytzTZinfoSerializer(_BuiltinTypeSerializer):
    signature = "pytz.timezone"
    handled_type = pytz.tzinfo.BaseTzInfo
    inheritable = True
    register = True

    def as_serializable(self, obj):
        return {"name": str(obj)}

    def from_serializable(cls, name):
        return pytz.timezone(name)


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


# Register datetime's datetime, timedelta and tzinfo.
class TimeSerializer(_BuiltinTypeSerializer):
    signature = "time"
    handled_type = datetime.time
    register = True

    def as_serializable(self, obj):
        return {"value": str(obj)}

    def from_serializable(self, value, timezone=None):
        # One could also use datetime.datetime.fromisoformat(value).replace(tzinfo=timezone)
        # but that fromisformat does not support second decimals with  other than 3 or 6 positions.
        try:
            return datetime.datetime.strptime(value, "%H:%M:%S.%f").time()
        except ValueError:
            return datetime.datetime.strptime(value, "%H:%M:%S").time()
