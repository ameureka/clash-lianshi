import ipaddress
import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".codebuddy", "__pycache__"}
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOC_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24", "2001:db8::/32"
))
SAFE_VALUE = re.compile(r"^(?:REPLACE_WITH_[A-Z0-9_]+|YOUR_[A-Z0-9_]+|<[^<>]+>|null|~)?$")
FIELD = re.compile(r"^\s*(?:-\s*)?(server|username|password|secret|uuid|token|private-key)\s*:\s*(.*?)\s*$", re.IGNORECASE)
QUERY = re.compile(r"(?:token|api_key|apikey|access_token|secret|password)=([^&\s`\"'<>]+)", re.IGNORECASE)
PATTERNS = (
    ("个人用户路径", re.compile(r"/(?:Users|home)/[^/\s`]+")),
    ("Windows 个人路径", re.compile(r"[A-Za-z]:\\Users\\[^\\\s`]+")),
    ("UUID", re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.IGNORECASE)),
    ("URL 内嵌认证", re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@", re.IGNORECASE)),
    ("私钥", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("常见访问令牌", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
)


def allowed_files():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    allowed = set()
    for line in lines:
        if not line.startswith("!") or line.endswith("/"):
            continue
        name = line[1:]
        if any(character in name for character in "*?[]") or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("公开白名单必须使用明确的相对文件名")
        allowed.add(name)
    if ".gitignore" not in allowed:
        raise ValueError("公开白名单缺少 .gitignore")
    return allowed


def safe_address(address):
    effective = getattr(address, "ipv4_mapped", None) or address
    return effective.is_loopback or any(
        effective.version == network.version and effective in network for network in DOC_NETWORKS
    )


def check_text(name, text):
    issues = []
    for number, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS:
            if pattern.search(line):
                issues.append((name, number, label))
        for value in IPV4.findall(line):
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                continue
            if not safe_address(address):
                issues.append((name, number, "非文档示例 IP"))
        for value in QUERY.findall(line):
            if not SAFE_VALUE.fullmatch(value):
                issues.append((name, number, "URL 查询认证值"))
        field = FIELD.match(line)
        if not field:
            continue
        key, value = field.groups()
        value = value.strip("\"'")
        if key.lower() == "server":
            if SAFE_VALUE.fullmatch(value):
                continue
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                issues.append((name, number, "非占位服务器地址"))
            else:
                if not safe_address(address):
                    issues.append((name, number, "非占位服务器地址"))
        elif not SAFE_VALUE.fullmatch(value):
            issues.append((name, number, "非占位认证字段"))
    return issues


def check_tree():
    allowed = allowed_files()
    seen = set()
    issues = []
    for base, dirs, files in os.walk(ROOT, followlinks=False):
        kept = []
        for directory in dirs:
            if directory in SKIP_DIRS:
                continue
            path = Path(base) / directory
            if path.is_symlink():
                issues.append((path.relative_to(ROOT).as_posix(), 0, "目录符号链接"))
            else:
                kept.append(directory)
        dirs[:] = kept
        for filename in files:
            if filename == ".DS_Store":
                continue
            path = Path(base) / filename
            name = path.relative_to(ROOT).as_posix()
            seen.add(name)
            if name not in allowed:
                issues.append((name, 0, "不在公开文件白名单"))
                continue
            if path.is_symlink():
                issues.append((name, 0, "文件符号链接"))
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                issues.append((name, 0, "非可读 UTF-8 文本"))
                continue
            issues.extend(check_text(name, text))
    issues.extend((name, 0, "白名单文件缺失") for name in allowed - seen)
    return sorted(set(issues)), len(allowed)


def main():
    try:
        issues, count = check_tree()
    except (OSError, ValueError):
        print("无法检查分享目录，请核对 .gitignore 白名单。", file=sys.stderr)
        return 1
    if issues:
        for name, line, label in issues:
            safe_name = IPV4.sub("<IP>", name)
            print(f"{safe_name}:{line}: {label}", file=sys.stderr)
        print("检查未通过；报告仅显示位置和类型，不显示敏感值。", file=sys.stderr)
        return 1
    print(f"检查通过：{count} 个公开文件，未发现所检查类型的敏感信息。")
    print("仅检查当前分享目录；不审计 Git 历史、远端或私人原件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
