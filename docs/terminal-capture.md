# 终端截图自动化（Niri + Alacritty）

## 前置条件

- Niri ≥ 25.0（`niri msg action screenshot-window --id` 必须存在）
- Alacritty（`--title` 参数作为窗口唯一标识）
- `jq`（解析 `niri msg -j windows` JSON）

## 核心机制

1. `alacritty --title "唯一 title" -e bash -c "$cmd; sleep 999" &` 起一个带唯一 title 的窗口
2. `niri msg -j windows | jq '.[]|select(.title|contains("唯一 title"))|.id'` 查窗口 ID
3. 等命令跑一会儿让输出稳定
4. `niri msg action screenshot-window --id $WID --path /abs/path.png` 截图保存
5. `kill` alacritty 进程关窗

为什么 `sleep 999` 保活？——`alacritty -e` 在 cmd 退出时关窗，截图时窗口已不存在。用 sleep 保持存活，截完图外部 kill。

## 用法

```bash
source ${SKILL_DIR}/scripts/capture.sh

# 单命令单窗口
capture_simple "part1_demo" "cd proj && python demo.py" 5
# → 截图到 $EXP_ROOT/screenshots/part1_demo.png

# server + client 双窗口（学术规范要求独立截图，不并排）
capture_dual "tcp_demo" \
    "python tcp_server.py" \
    "sleep 1 && python tcp_client.py" \
    5
# → screenshots/tcp_demo_server.png 和 tcp_demo_client.png

# 三窗口并发（持续运行 15 秒后全部截图）
capture_trio "weather" \
    "python dataserver.py" \
    "python station.py 唐山" \
    "python station.py 北京" \
    15
```

## 后处理：裁空白

Alacritty 默认背景 `#282828`，命令输出不满屏时周围大量同色空白。用 magick 裁切：

```bash
magick in.png -fuzz 15% -trim +repage -bordercolor "#282828" -border 12 out.png
```

参数解释：
- `-fuzz 15%`：允许背景色有 15% 的色差（alacritty 有反锯齿，纯 0% 会失败）
- `-trim`：根据四边背景色裁切
- `+repage`：重置 canvas 坐标
- `-border 12`：保留 12 px 呼吸距离（看起来不太紧贴）

封装在 `scripts/trim_png.sh`。

## 跨平台指南

### Niri（推荐，完全自动化）
以上工作流已就绪。Niri 25+ 的 IPC 提供 `screenshot-window --id` 能按窗口 ID 精准截图。

### 其他 Wayland 合成器（Hyprland / Sway / KDE）
接近全自动。替换截图命令：
| 合成器 | 命令 |
|---|---|
| Hyprland | `hyprshot -m window -o /tmp -f name.png` |
| Sway     | `grim -g "$(swaymsg -t get_tree \| jq ...window geometry)" out.png` |
| KDE      | `spectacle -bnmao out.png`（窗口选中态） |

`capture.sh` 需要改窗口 ID 解析逻辑，其他保持一致。

### X11
`scrot -u out.png` 截聚焦窗口；`xdotool getactivewindow` 可配合。成熟且自动化程度不输 Niri，但
需要 X11 会话。

### macOS
`screencapture -l $WINDOW_ID out.png`。WINDOW_ID 可用 `osascript` 或 `yabai -m query --windows` 拿。
首次运行需授予「屏幕录制」无障碍权限。

### Windows（自动化困难，**推荐 Agent 指导手动**）

Windows Terminal / PowerShell 没有类似 Niri 的 IPC，第三方方案（NirCmd、PSScreenshot、PowerShell
`Add-Type`）稳定性差，常卡在字体渲染、DPI 缩放、UAC、窗口 handle 失效。**不要强求自动化**。

**推荐做法**：Agent 以**指导模式**运行——
1. Agent 告诉用户：「现在请打开 Windows Terminal，跑 `python demo.py`，等输出稳定后用
   `Win + Shift + S` 选定终端区域截图，保存到 `<项目>/assets/<label>.png`」
2. 用户截完、保存
3. Agent 读文件确认存在，继续下一步
4. Agent 用 `trim_png.sh`（通过 WSL / Git Bash 的 magick）裁空白；或者让用户用 Snipping Tool 直接
   截内容区域，省略裁切

这种模式下 `capture.sh` 不能用，但 `trim_png.sh`（如果装了 ImageMagick）和 `silicon_cli.sh`
（Windows 版 silicon 可用）都能跑，后续阶段不受影响。

### 无桌面 / CI / 服务器
用 `script -q -c "cmd" out.log` 录 ANSI 文本日志，再 `aha` 转 HTML → `wkhtmltopdf` 转图。效果接近
但字符画、颜色可能不如真实终端截图准确。适合批量自动化，不适合报告美观度要求高的场景。
