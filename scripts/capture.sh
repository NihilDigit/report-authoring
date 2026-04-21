#!/usr/bin/env bash
# 利用 niri 的 screenshot-window --id 对指定 Alacritty 窗口截图
# 必须在 bash 下 source 或执行（用到 BASH_SOURCE）：
#   bash scripts/run-all-captures.sh
set -u

# 路径探测：优先 BASH_SOURCE，否则使用 EXP2_ROOT 环境变量
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
    ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
elif [[ -n "${EXP2_ROOT:-}" ]]; then
    ROOT="$EXP2_ROOT"
else
    ROOT="/home/spencer/Codes/bigdata/experiment2"
fi
SHOT_DIR="$ROOT/screenshots"
VENV_BIN="$ROOT/.venv/bin"
mkdir -p "$SHOT_DIR"

# 在 PATH 前插入 venv，使 python 指向项目虚拟环境
export PATH="$VENV_BIN:$PATH"

# 通过标题查找 niri 窗口 ID
_find_window_id() {
    local title="$1"
    niri msg -j windows 2>/dev/null | \
        jq -r --arg t "$title" '.[] | select(.title | contains($t)) | .id' | \
        head -1
}

# 等某标题的窗口出现并返回其 ID（超时 10s）
_wait_for_window() {
    local title="$1"
    local id=""
    for _ in $(seq 1 40); do
        id=$(_find_window_id "$title")
        [[ -n "$id" ]] && { echo "$id"; return 0; }
        sleep 0.25
    done
    return 1
}

# 在新 Alacritty 窗口中运行命令，运行完成后截图再关窗口
# $1 label  $2 命令  $3 估计运行时长（秒，默认 6）
capture_simple() {
    local label="$1"
    local cmd="$2"
    local run_time="${3:-6}"
    local title="EXP2-$label-$RANDOM"

    # 命令跑完后 sleep 999 保持窗口不关闭，等外部截图后 kill
    alacritty --title "$title" -o 'window.dimensions.columns=110' -o 'window.dimensions.lines=35' \
        -e bash -c "cd '$ROOT' && $cmd; echo; echo '==== DONE: $label ===='; sleep 999" &
    local apid=$!

    local wid
    wid=$(_wait_for_window "$title") || { echo "[capture] 未找到窗口: $title"; kill $apid 2>/dev/null; return 1; }

    sleep "$run_time"   # 等命令完成

    niri msg action screenshot-window --id "$wid" --path "$SHOT_DIR/${label}.png"
    local rc=$?

    kill $apid 2>/dev/null
    wait $apid 2>/dev/null

    if [[ $rc -eq 0 && -s "$SHOT_DIR/${label}.png" ]]; then
        echo "[capture] 已保存 $SHOT_DIR/${label}.png ($(stat -c %s "$SHOT_DIR/${label}.png") bytes)"
    else
        echo "[capture] !! 保存失败 rc=$rc"
    fi
}

# 同时开两个窗口：server 持续运行、client 一次性执行
# $1 label_base  $2 server_cmd  $3 client_cmd  $4 client 估计时长（秒，默认 5）
capture_dual() {
    local base="$1"
    local server_cmd="$2"
    local client_cmd="$3"
    local run_time="${4:-5}"
    local stitle="EXP2-$base-server-$RANDOM"
    local ctitle="EXP2-$base-client-$RANDOM"

    # server 本身持续运行，不用 sleep 保活
    alacritty --title "$stitle" -o 'window.dimensions.columns=100' -o 'window.dimensions.lines=30' \
        -e bash -c "cd '$ROOT' && $server_cmd" &
    local spid=$!
    local swid
    swid=$(_wait_for_window "$stitle") || { echo "[capture] server 窗口未找到"; kill $spid 2>/dev/null; return 1; }

    sleep 1.0

    # client 跑完后 sleep 保活
    alacritty --title "$ctitle" -o 'window.dimensions.columns=100' -o 'window.dimensions.lines=30' \
        -e bash -c "cd '$ROOT' && $client_cmd; echo; echo '==== client done ===='; sleep 999" &
    local cpid=$!
    local cwid
    cwid=$(_wait_for_window "$ctitle") || { echo "[capture] client 窗口未找到"; kill $cpid $spid 2>/dev/null; return 1; }

    sleep "$run_time"

    niri msg action screenshot-window --id "$swid" --path "$SHOT_DIR/${base}_server.png"
    niri msg action screenshot-window --id "$cwid" --path "$SHOT_DIR/${base}_client.png"

    kill $cpid $spid 2>/dev/null
    wait $cpid $spid 2>/dev/null
    echo "[capture] 已保存 ${base}_server.png / ${base}_client.png"
}

# 三窗口：server + 两个 client，运行 $4 秒后全部截图
# $1 label_base  $2 server_cmd  $3 client1_cmd  $4 client2_cmd  $5 duration（默认 15 秒）
capture_trio() {
    local base="$1"
    local server_cmd="$2"
    local c1_cmd="$3"
    local c2_cmd="$4"
    local dur="${5:-15}"

    local stitle="EXP2-$base-server-$RANDOM"
    local t1="EXP2-$base-c1-$RANDOM"
    local t2="EXP2-$base-c2-$RANDOM"

    alacritty --title "$stitle" -o 'window.dimensions.columns=100' -o 'window.dimensions.lines=30' \
        -e bash -c "cd '$ROOT' && $server_cmd" &
    local spid=$!
    local swid; swid=$(_wait_for_window "$stitle") || return 1
    sleep 1

    alacritty --title "$t1" -o 'window.dimensions.columns=100' -o 'window.dimensions.lines=30' \
        -e bash -c "cd '$ROOT' && $c1_cmd" &
    local p1=$!
    local w1; w1=$(_wait_for_window "$t1") || return 1

    alacritty --title "$t2" -o 'window.dimensions.columns=100' -o 'window.dimensions.lines=30' \
        -e bash -c "cd '$ROOT' && $c2_cmd" &
    local p2=$!
    local w2; w2=$(_wait_for_window "$t2") || return 1

    echo "[capture] 运行 $dur 秒..."
    sleep "$dur"

    niri msg action screenshot-window --id "$swid" --path "$SHOT_DIR/${base}_server.png"
    niri msg action screenshot-window --id "$w1"   --path "$SHOT_DIR/${base}_station1.png"
    niri msg action screenshot-window --id "$w2"   --path "$SHOT_DIR/${base}_station2.png"

    kill $p1 $p2 $spid 2>/dev/null
    echo "[capture] 已保存 ${base}_{server,station1,station2}.png"
}
