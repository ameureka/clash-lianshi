# SOCKS5 出口信息示例

> 这是脱敏占位示例，不是可用账号。原始出口 IP、两组账号密码及携带认证的测试命令已从公开副本移除。

## 1. 字段对应

| 字段 | 公开示例 | 本地环境变量 |
|---|---|---|
| 协议 | `socks5` | 固定协议，不要套用 Shadowsocks 参数 |
| Server | `192.0.2.10` | `CHAIN_SOCKS5_SERVER` |
| Port | `1080` | `CHAIN_SOCKS5_PORT`，默认 `1080` |
| Username | `REPLACE_WITH_SOCKS5_USERNAME` | `CHAIN_SOCKS5_USERNAME` |
| Password | `REPLACE_WITH_SOCKS5_PASSWORD` | `CHAIN_SOCKS5_PASSWORD` |
| UDP | `true`，仅为配置开关 | `CHAIN_SOCKS5_UDP`，可设 `true` 或 `false` |
| 前置拨号 | `前置选择` | 由模板的 `dialer-proxy` 指定 |

`192.0.2.10` 属于文档保留网段，没有对应的可用代理。生成工具仅接受公网 IP，不解析或访问域名，也拒绝私网、回环及额外限制的网段。域名出口需要在本地另行核验和配置。

## 2. macOS Zsh 输入示例

在本目录打开终端。下面使用交互输入，避免把真实密码直接写进命令历史；密码输入不回显：

```zsh
read -r 'CHAIN_SOCKS5_SERVER?公网 SOCKS5 IP: '
read -r 'CHAIN_SOCKS5_USERNAME?SOCKS5 用户名: '
read -rs 'CHAIN_SOCKS5_PASSWORD?SOCKS5 密码: '
printf '\n'
export CHAIN_SOCKS5_SERVER CHAIN_SOCKS5_USERNAME CHAIN_SOCKS5_PASSWORD
export CHAIN_SOCKS5_PORT=1080
export CHAIN_SOCKS5_UDP=true
python3 tools/render-proxies.py --output "$HOME/.config/clash-chain/private/proxies.local.yaml"
unset CHAIN_SOCKS5_SERVER CHAIN_SOCKS5_PORT CHAIN_SOCKS5_USERNAME CHAIN_SOCKS5_PASSWORD CHAIN_SOCKS5_UDP
```

端口不是 `1080` 时请调整；需要关闭 UDP 时设为 `false`。以上 `read` 写法用于 Zsh，其他终端请使用对应的环境变量设置方式。

生成文件不在仓库里，权限为 `600`，不会覆盖已有文件。请把内容导入自己当前订阅的代理增强，而不是上传到 GitHub。

## 3. 安全约定

- 凭据通过本地进程环境变量输入，公开文件只包含占位符。
- 环境变量不是加密存储；不要使用终端录像、调试输出或公开日志记录凭据。
- Clash Verge 读取的私有 YAML 最终仍含明文认证值，文件权限只是访问限制。
- 不要把真实 `.env`、订阅 URL、控制 `secret` 或管理账号放入分享目录。
- 不使用携带 `用户名:密码@服务器` 的代理 URL 做公开示例。
- Git 忽略规则不会清理历史；曾公开的凭据需要轮换。

完整流程见 [整体配置说明](整体配置说明.md)。
