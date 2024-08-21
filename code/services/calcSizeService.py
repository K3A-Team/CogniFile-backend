import math
import re

def get_readable_file_size(size_in_bytes: int) -> str:
    """
    Convert a file size in bytes to a human-readable string format.

    Args:
        size_in_bytes (int): The size of the file in bytes.

    Returns:
        str: The human-readable file size (e.g., '10.5 MB').
    """
    if size_in_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_bytes_from_readable_size(size_str: str) -> int:
    """
    Convert a human-readable file size string to bytes.

    Args:
        size_str (str): The human-readable file size (e.g., '10.5 MB').

    Returns:
        int: The size of the file in bytes.

    Raises:
        ValueError: If the input string is not in a valid format.
    """
    size_name = ("B", "KB", "MB", "GB", "TB")
    size_str = size_str.strip().upper()
    match = re.match(r"(\d+(\.\d+)?)\s*(B|KB|MB|GB|TB)", size_str)
    
    if not match:
        raise ValueError("Invalid size format")
    
    size = float(match.group(1))
    unit = match.group(3)
    
    i = size_name.index(unit)
    return int(size * (1024 ** i))