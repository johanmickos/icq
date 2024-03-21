"""
Hashing utilities.
"""
import hashlib


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()
