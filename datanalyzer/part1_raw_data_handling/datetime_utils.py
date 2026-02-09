"""
Parse datetime from filename (e.g. end of filename in form yyyy-MM-ddTHH-mm-ss).
"""

from datetime import datetime
from typing import Optional
import re


def convert_end_string_in_filename_to_datetime(
    filename: str,
    str_to_find: str = "T",
    before_str_date_format: str = "yyyy-MM-dd",
    after_str_date_format: str = "HH-mm-ss",
    str_index: Optional[int] = None,
) -> datetime:
    """
    Extract datetime from filename. Default assumes datetime at end in form
    yyyy-MM-ddTHH-mm-ss (e.g. ...2020-09-15T09-33-28.h5).
    """
    idx_list = [m.start() for m in re.finditer(re.escape(str_to_find), filename)]
    if not idx_list:
        raise ValueError(f"Separator '{str_to_find}' not found in filename: {filename}")
    if str_index is not None:
        ind = idx_list[str_index]
    else:
        ind = idx_list[-1]
    if before_str_date_format == "yyyy-MM-dd":
        before_len = 10
    else:
        before_len = len(before_str_date_format.replace("yyyy", "____").replace("MM", "__").replace("dd", "__"))
    if after_str_date_format == "HH-mm-ss":
        after_len = 8
    else:
        after_len = len(after_str_date_format.replace("HH", "__").replace("mm", "__").replace("ss", "__"))
    start = ind - before_len
    end = ind + len(str_to_find) + after_len
    if start < 0 or end > len(filename):
        raise ValueError(f"Cannot extract date substring from: {filename}")
    date_str = filename[start:end]
    date_part = date_str[:10]
    time_part = date_str[11:].replace("T", "")
    try:
        return datetime.strptime(date_part + " " + time_part, "%Y-%m-%d %H-%M-%S")
    except ValueError:
        return datetime.strptime(date_part, "%Y-%m-%d")
