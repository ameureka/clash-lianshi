import argparse
import ipaddress
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "proxies.example.yaml"
RESTRICTED_FIRST_OCTETS = {9, 10, 11, 21, 30}


def required(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"缺少环境变量 {name}")
    if "\x00" in value:
        raise ValueError(f"环境变量 {name} 不能包含 NUL")
    return value


def public_ip(value):
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        raise ValueError("CHAIN_SOCKS5_SERVER 必须是公网 IP 地址") from None
    effective = getattr(address, "ipv4_mapped", None) or address
    restricted = effective.version == 4 and int(str(effective).split(".")[0]) in RESTRICTED_FIRST_OCTETS
    transition = address.version == 6 and (
        address.sixtofour is not None or address.teredo is not None or address.scope_id is not None
    )
    if not effective.is_global or effective.is_multicast or restricted or transition:
        raise ValueError("CHAIN_SOCKS5_SERVER 不允许私网、保留或受限地址")
    return str(address)


def render():
    server = public_ip(required("CHAIN_SOCKS5_SERVER"))
    username = required("CHAIN_SOCKS5_USERNAME")
    password = required("CHAIN_SOCKS5_PASSWORD")
    try:
        port = int(os.environ.get("CHAIN_SOCKS5_PORT", "1080"))
    except ValueError:
        raise ValueError("CHAIN_SOCKS5_PORT 必须是整数") from None
    if not 1 <= port <= 65535:
        raise ValueError("CHAIN_SOCKS5_PORT 必须在 1–65535 之间")
    udp = os.environ.get("CHAIN_SOCKS5_UDP", "true").strip().lower()
    if udp not in {"true", "false"}:
        raise ValueError("CHAIN_SOCKS5_UDP 只能为 true 或 false")
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    replacements = {
        '    server: "192.0.2.10"': "    server: " + json.dumps(server, ensure_ascii=True),
        '    username: "REPLACE_WITH_SOCKS5_USERNAME"': "    username: " + json.dumps(username, ensure_ascii=True),
        '    password: "REPLACE_WITH_SOCKS5_PASSWORD"': "    password: " + json.dumps(password, ensure_ascii=True),
        "    port: 1080": f"    port: {port}",
        "    udp: true": f"    udp: {udp}",
    }
    for old, new in replacements.items():
        if lines.count(old) != 1:
            raise ValueError("代理示例模板已改变，请核对字段和生成工具")
        lines[lines.index(old)] = new
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="从环境变量生成仓库外的私有 SOCKS5 代理增强")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.is_relative_to(ROOT):
        parser.error("私有配置必须写到本分享目录之外")
    try:
        text = render()
        os.umask(0o077)
        output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    except FileExistsError:
        print("目标文件已存在，未覆盖；请备份后选择新的输出文件。", file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print("无法生成私有配置，请检查路径和权限。", file=sys.stderr)
        return 1
    print("已生成私有代理增强，文件权限 600；请本地导入，不要提交。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
