#!/usr/bin/env python3
"""Load publishing credentials without storing secrets in the repository."""
from pathlib import Path
import os
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = Path(os.environ.get('AI_TOOL_REVIEW_CONFIG_DIR', '~/.config/ai-tool-review')).expanduser()
class SecretConfigError(RuntimeError): pass
def _read_secret(env_name: str, file_env_name: str, default_filename: str) -> str:
    direct = os.environ.get(env_name, '').strip()
    if direct: return direct
    configured = os.environ.get(file_env_name, '').strip()
    path = Path(configured).expanduser() if configured else DEFAULT_CONFIG_DIR/default_filename
    if path.exists() and (value := path.read_text(encoding='utf-8').strip()): return value
    raise SecretConfigError(f'Missing {env_name}. Set it or place it in {path}. Do not store credentials in the repository.')
def load_toutiao_cookie() -> str: return _read_secret('TOUTIAO_COOKIE','TOUTIAO_COOKIE_FILE','toutiao_cookie.txt')
def load_zhihu_cookie() -> str: return _read_secret('ZHIHU_COOKIE','ZHIHU_COOKIE_FILE','zhihu_cookie.txt')
def github_raw_base() -> str:
    return os.environ.get('AI_TOOL_REVIEW_GITHUB_RAW_BASE','https://raw.githubusercontent.com/wk123-11/ai-tool-review/main/').rstrip('/')+'/'
