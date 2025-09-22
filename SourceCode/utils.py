import os, sys, subprocess
from typing import Optional, Tuple

def resource_path(relpath: str) -> str:
    """#説明: PyInstallerの展開ディレクトリ or 実行ディレクトリからリソースを解決"""
    base = getattr(sys, "_MEIPASS", None)
    if base and os.path.exists(base):
        p = os.path.join(base, relpath)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(sys.argv[0]), relpath)

def try_icon_path() -> Optional[str]:
    """#説明: 同梱アイコン候補から存在するパスを返す（なければNone）"""
    for candidate in ("pasgene.ico", "pasgene.ico"):
        p = resource_path(candidate)
        if os.path.exists(p):
            return p
    return None

def open_env_editor() -> Tuple[bool, str]:
    """#説明: Windowsの環境変数ダイアログを開く。失敗時は(False, エラー)"""
    try:
        if os.name != "nt":
            return False, "この機能はWindows専用です。各OSの環境変数設定手順を参照してください。"
        subprocess.run(["rundll32.exe", "sysdm.cpl,EditEnvironmentVariables"], check=True)
        return True, ""
    except Exception as e:
        return False, f"環境変数ダイアログを開けませんでした: {e}"

__all__ = ["resource_path", "try_icon_path", "open_env_editor"]
