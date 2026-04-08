#!/bin/bash
# Скрипт для проверки Cloudflare DNS настроек
# Использование: ./cloudflare_check.sh <domain> [api_token]

DOMAIN="${1:-YOUR_CDN_DOMAIN}"
API_TOKEN="${2}"

echo "=== Проверка DNS для $DOMAIN ==="
echo ""

# 1. Проверка разрешения DNS
echo "→ Проверка DNS разрешения..."
DIG_RESULT=$(dig +short $DOMAIN A @1.1.1.1)
if [ -n "$DIG_RESULT" ]; then
    echo "  ✅ DNS разрешается в:"
    echo "$DIG_RESULT" | while read ip; do
        echo "     - $ip"
    done
else
    echo "  ❌ DNS не разрешается"
fi

# 2. Проверка HTTP через Cloudflare
echo ""
echo "→ Проверка HTTP/HTTPS..."
HTTP_CODE=$(curl -sk --max-time 10 -o /dev/null -w "%{http_code}" "https://$DOMAIN")
if [ "$HTTP_CODE" != "000" ]; then
    echo "  ✅ HTTPS отвечает: HTTP $HTTP_CODE"
else
    echo "  ❌ HTTPS не отвечает"
fi

# 3. Проверка SSL сертификата
echo ""
echo "→ Проверка SSL сертификата..."
SSL_INFO=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | grep -E "subject|issuer|CN=")
if [ -n "$SSL_INFO" ]; then
    echo "  ✅ SSL сертификат:"
    echo "$SSL_INFO" | sed 's/^/     /'
else
    echo "  ❌ SSL сертификат не получен"
fi

# 4. Если есть API токен - проверка Cloudflare
if [ -n "$API_TOKEN" ]; then
    echo ""
    echo "→ Проверка Cloudflare API..."

    # Получить Zone ID
    ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['result'][0]['id']) if d.get('result') else ''" 2>/dev/null)

    if [ -n "$ZONE_ID" ]; then
        echo "  ✅ Zone ID: $ZONE_ID"

        # Получить DNS записи
        DNS_RECORDS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$DOMAIN" \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" | python3 -c "import json,sys; d=json.load(sys.stdin); r=d.get('result',[]); print('\n'.join([f\"{x['type']} {x['name']} -> {x['content']} (proxied={'Yes' if x.get('proxied') else 'No'})\" for x in r]))" 2>/dev/null)

        if [ -n "$DNS_RECORDS" ]; then
            echo "  DNS записи:"
            echo "$DNS_RECORDS" | sed 's/^/     /'
        fi
    else
        echo "  ❌ Не удалось получить Zone ID (проверьте API токен)"
    fi
else
    echo ""
    echo "💡 Для проверки Cloudflare API укажите токен:"
    echo "   $0 $DOMAIN <your_api_token>"
fi

echo ""
echo "=== Проверка завершена ==="
