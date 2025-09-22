import hashlib
from typing import Tuple

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def validate_passwords(pw1: str, pw2: str) -> Tuple[bool, str]:
    if pw1 == "" or pw2 == "":
        return False, "パスワードが未入力です。"
    if pw1 != pw2:
        return False, "パスワードが一致しません！"
    return True, ""
