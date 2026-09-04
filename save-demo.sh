#!/bin/bash
# 從剪貼簿存一張 demo 圖，並驗證不是重複（剪貼簿沒更新時會誤存上一張）
# 用法: ./save-demo.sh <style-id>
set -e
ID="$1"
[ -z "$ID" ] && { echo "用法: ./save-demo.sh <style-id>"; exit 1; }
cd "$(dirname "$0")"
B=$(pbpaste | tr -d '\n')

if [ ${#B} -lt 3000 ]; then
  echo "❌ 剪貼簿沒有圖片資料（長度 ${#B}）"
  exit 1
fi

TMP=$(mktemp /tmp/demo-XXXX.jpg)
printf '%s' "$B" | base64 -d > "$TMP" 2>/dev/null

if ! file "$TMP" | grep -q JPEG; then
  echo "❌ 解碼後不是 JPEG"; rm -f "$TMP"; exit 1
fi

NEW=$(md5 -q "$TMP")
for f in style-demos/*.jpg; do
  [ -e "$f" ] || continue
  if [ "$(md5 -q "$f")" = "$NEW" ]; then
    echo "❌ 與現有 $(basename $f) 完全相同 — 剪貼簿沒更新，未存檔"
    rm -f "$TMP"; exit 1
  fi
done

mv "$TMP" "style-demos/$ID.jpg"
echo "✅ $ID.jpg 已存（$(ls -l style-demos/$ID.jpg | awk '{print $5}') bytes）"
echo "   進度 $(ls style-demos/*.jpg | wc -l | tr -d ' ')/35"
