#!/bin/bash
# Запускать когда Hiddify App включён (режим VPN/TUN)
# Проверяет: IP утечку, DNS утечку, скорость, доступность заблокированных сайтов

echo "=== Клиентский тест VPN ==="
echo ""

# Тест 1: Мой IP (должен быть NL, не РФ)
echo "→ Проверка IP..."
IP_INFO=$(curl -s --max-time 10 https://ipinfo.io)
MY_IP=$(echo "$IP_INFO" | grep -oP '"ip":\s*"\K[^"]+')
MY_COUNTRY=$(echo "$IP_INFO" | grep -oP '"country":\s*"\K[^"]+')
MY_ORG=$(echo "$IP_INFO" | grep -oP '"org":\s*"\K[^"]+' | sed 's/AS[0-9]* //g')

if [ "$MY_COUNTRY" = "NL" ]; then
    echo "  ✅ IP: $MY_IP | Страна: $MY_COUNTRY | Провайдер: $MY_ORG"
else
    echo "  ❌ IP: $MY_IP | Страна: $MY_COUNTRY (ожидалось NL) | Провайдер: $MY_ORG"
    echo "  ⚠️  VPN может не работать!"
fi

# Тест 2: DNS утечки
echo ""
echo "→ Проверка DNS утечки..."
DNS_CHECK=$(curl -s --max-time 10 "https://dns.google/resolve?name=whoami.akamai.net&type=A" \
    | grep -oP '"data":"\K[^"]+' | head -1)
echo "  DNS-запрос прошёл через: $DNS_CHECK"

# Тест 3: Доступность заблокированных сайтов
echo ""
echo "→ Тест доступности заблокированных сайтов..."
BLOCKED_SITES=("instagram.com" "youtube.com" "x.com" "facebook.com" "reddit.com" "telegram.org")

for site in "${BLOCKED_SITES[@]}"; do
    code=$(curl -s --max-time 8 -o /dev/null -w "%{http_code}" "https://$site")
    if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
        echo "  ✅ $site → HTTP $code"
    else
        echo "  ❌ $site → HTTP $code (недоступен)"
    fi
done

# Тест 4: Скорость
echo ""
echo "→ Тест скорости (загрузка 10 МБ)..."
SPEED=$(curl -s --max-time 30 -w "%{speed_download}" \
    -o /dev/null "https://speed.cloudflare.com/__down?bytes=10000000")
SPEED_MBPS=$(echo "scale=1; $SPEED / 1024 / 1024" | bc)
echo "  📊 Скорость: ${SPEED_MBPS} МБ/с"

if (( $(echo "$SPEED_MBPS > 5.0" | bc -l) )); then
    echo "  ✅ Скорость нормальная"
elif (( $(echo "$SPEED_MBPS > 1.0" | bc -l) )); then
    echo "  ⚠️  Скорость низкая — возможна деградация от Мегафон"
else
    echo "  ❌ Скорость критически низкая — проверить конфиг"
fi

echo ""
echo "=== Тест завершён ==="
echo ""
echo "💡 Если все тесты прошли — VPN работает корректно!"
echo "💡 Если IP не NL — проверьте что Hiddify App в режиме VPN (не Proxy)"
echo "💡 Если сайты недоступны — возможна проблема с SNI, попробуйте другой протокол из подписки"
