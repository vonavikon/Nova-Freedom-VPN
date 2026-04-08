#!/bin/bash
# /opt/vpn-monitor/vpn_healthcheck.sh
# Проверяет работу Hiddify Manager и внешнюю доступность

TELEGRAM_TOKEN=""
TELEGRAM_CHAT_ID=""
SERVER_IP=$(curl -s https://api.ipify.org)
LOG_FILE="/var/log/vpn_healthcheck.log"
ALERT_FILE="/tmp/vpn_alert_sent"

# Функция отправки в Telegram
send_telegram() {
    [ -z "$TELEGRAM_TOKEN" ] && return
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="${message}" \
        -d parse_mode="HTML" > /dev/null
}

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# === ТЕСТ 1: Hiddify Manager работает ===
check_hiddify_service() {
    if pgrep -f "hiddify-core" > /dev/null; then
        log "✅ Hiddify service: RUNNING"
        return 0
    else
        log "❌ Hiddify service: DOWN"
        return 1
    fi
}

# === ТЕСТ 2: Порт 443 открыт и отвечает ===
check_port_443() {
    local result
    result=$(curl -sk --max-time 5 -o /dev/null -w "%{http_code}" "https://${SERVER_IP}:443")
    if [ "$result" != "000" ]; then
        log "✅ Port 443: OPEN (HTTP code: ${result})"
        return 0
    else
        log "❌ Port 443: NO RESPONSE"
        return 1
    fi
}

# === ТЕСТ 3: Исходящий интернет работает (из NL) ===
check_outbound() {
    local result
    result=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" "https://api.ipify.org")
    if [ "$result" = "200" ]; then
        log "✅ Outbound internet: OK"
        return 0
    else
        log "❌ Outbound internet: FAILED (${result})"
        return 1
    fi
}

# === ТЕСТ 4: SNI-домен доступен с сервера (проверка Reality) ===
check_sni_reachable() {
    local SNI="dl.google.com"
    local result
    result=$(curl -s --max-time 10 --tlsv1.3 --http2 \
        -o /dev/null -w "%{http_code}" "https://${SNI}")
    if [ "$result" = "200" ] || [ "$result" = "301" ] || [ "$result" = "302" ]; then
        log "✅ SNI domain (${SNI}): REACHABLE (${result})"
        return 0
    else
        log "❌ SNI domain (${SNI}): UNREACHABLE (${result})"
        return 1
    fi
}

# === ТЕСТ 5: Скорость скачивания с сервера ===
check_download_speed() {
    local speed
    speed=$(curl -s --max-time 15 -w "%{speed_download}" \
        -o /dev/null "https://speed.cloudflare.com/__down?bytes=1000000" 2>/dev/null)
    [ -z "$speed" ] && speed=0
    local speed_mbps
    speed_mbps=$(echo "scale=1; $speed / 1024 / 1024" | bc)

    if (( $(echo "$speed_mbps > 1.0" | bc -l) )); then
        log "✅ Download speed: ${speed_mbps} MB/s"
        return 0
    else
        log "⚠️ Download speed LOW: ${speed_mbps} MB/s"
        return 1
    fi
}

# === ОСНОВНАЯ ЛОГИКА ===
FAILURES=0

check_hiddify_service || FAILURES=$((FAILURES+1))
check_port_443        || FAILURES=$((FAILURES+1))
check_outbound        || FAILURES=$((FAILURES+1))
check_sni_reachable   || FAILURES=$((FAILURES+1))
check_download_speed  || FAILURES=$((FAILURES+1))

log "--- Результат: $FAILURES/5 проверок не прошли ---"

# Отправить алерт если есть проблемы и не отправляли в последние 30 мин
if [ "$FAILURES" -gt 0 ]; then
    if [ ! -f "$ALERT_FILE" ] || [ "$(( $(date +%s) - $(stat -c %Y "$ALERT_FILE") ))" -gt 1800 ]; then
        send_telegram "🚨 <b>VPN Alert</b>

❌ Проблем: <b>${FAILURES}/5</b>
🖥 Сервер: ${SERVER_IP}
🕐 Время: $(date '+%d.%m.%Y %H:%M')

Проверь: ssh root@\${SERVER_IP}
Команды:
• systemctl status hiddify
• hiddify  (меню)
• tail -100 /var/log/vpn_healthcheck.log"
        touch "$ALERT_FILE"
        log "📨 Telegram-алерт отправлен"
    fi
else
    rm -f "$ALERT_FILE"
    log "✅ Всё работает нормально"
fi
