from numpy.lib.format import dtype_to_descr
from numpy.lib.recfunctions import repack_fields
import numpy as np

DT64_AS_STR_DTYPE = "U30"


def sanitize_dtype(in_dtype, datetime64_as_string=False):
    """
    Substitutes all datetime64 dtypes by strings. Returns a human-readable representation that can also converted to a dtype object.
    """
    kws = {"datetime64_as_string": datetime64_as_string}
    if isinstance(in_dtype, np.dtype):
        # Convert to list of tuples or string.
        in_dtype = repack_fields(in_dtype)
        return sanitize_dtype(dtype_to_descr(in_dtype), **kws)
    elif isinstance(in_dtype, str):
        # Base types.
        if np.dtype("O") == in_dtype:
            raise Exception("Object dtype not supported.")
        elif datetime64_as_string and np.issubdtype(in_dtype, np.datetime64):
            # Map datetime64 sub-dtypes to strings, preserves all others.
            return DT64_AS_STR_DTYPE
        elif np.issubdtype(in_dtype, "U"):
            return str(np.dtype(in_dtype))[1:]  # Skip endianness.
        else:
            return str(np.dtype(in_dtype))  # Get formal string representation.
    elif isinstance(in_dtype, list):
        # List of tuples (see below for case tuple).
        return [sanitize_dtype(_x, **kws) for _x in in_dtype]
    elif isinstance(in_dtype, tuple):
        # (field_name, field_dtype [, field_shape])
        in_dtype = list(in_dtype)
        in_dtype[1] = sanitize_dtype(in_dtype[1], **kws)
        return tuple(in_dtype)
    else:
        raise Exception("Unexpected case.")
