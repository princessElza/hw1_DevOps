#!/bin/bash
# Функциональное тестирование контейнера imagenet-classifier
# Используется в CD pipeline для проверки развернутого сервиса

set -e

# Параметры
HOST="${1:-localhost}"
PORT="${2:-8000}"
TEST_RESULTS="${3:-.}"

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Счетчики
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

echo "═══════════════════════════════════════════════════════════════"
echo "         FUNCTIONAL TESTS - imagenet-classifier API"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Target: http://${HOST}:${PORT}"
echo "Test Results Directory: ${TEST_RESULTS}"
echo ""

# Проверяем доступность хоста
echo "▶ Pre-flight: Checking connectivity..."
if ! curl -s -f "http://${HOST}:${PORT}/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to http://${HOST}:${PORT}${NC}"
    echo "Check if service is running and port is accessible"
    exit 1
fi
echo -e "${GREEN}✓ Service is accessible${NC}"
echo ""

# Test 1: Health Endpoint
echo "▶ TEST 1: GET /health endpoint"
echo "─────────────────────────────────────────"
RESPONSE=$(curl -s -w "\n%{http_code}" "http://${HOST}:${PORT}/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Status: 200 OK${NC}"
    echo "Response: $BODY"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Status: $HTTP_CODE (expected 200)${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# Test 2: Info Endpoint
echo "▶ TEST 2: GET /info endpoint"
echo "─────────────────────────────────────────"
RESPONSE=$(curl -s -w "\n%{http_code}" "http://${HOST}:${PORT}/info")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Status: 200 OK${NC}"
    echo "Response: $BODY" | head -c 100
    echo ""
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Status: $HTTP_CODE (expected 200)${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# Test 3: Predict Endpoint
echo "▶ TEST 3: POST /predict endpoint"
echo "─────────────────────────────────────────"

# Генерируем тестовые данные (2352 случайных float значений)
PIXEL_DATA=$(python3 << 'PYTHON'
import json
import random
random.seed(42)
pixels = [random.random() for _ in range(2352)]
print(json.dumps({"pixels": pixels}))
PYTHON
)

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "http://${HOST}:${PORT}/predict" \
    -H "Content-Type: application/json" \
    -d "$PIXEL_DATA")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Status: 200 OK${NC}"
    echo "Response: $BODY"
    
    # Проверяем что есть необходимые поля
    if echo "$BODY" | grep -q '"prediction"' && echo "$BODY" | grep -q '"class_name"' && echo "$BODY" | grep -q '"confidence"'; then
        echo -e "${GREEN}✓ Response contains required fields${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Response missing required fields${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}✗ Status: $HTTP_CODE (expected 200)${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# Test 4: Predict Image Endpoint
echo "▶ TEST 4: POST /predict_image endpoint"
echo "─────────────────────────────────────────"

# Проверяем наличие тестового изображения
if [ ! -f "/tmp/test-image.png" ]; then
    echo "Creating test image..."
    python3 << 'PYTHON'
from PIL import Image
import random
import numpy as np

# Создаем случайное изображение 28x28 RGB
img_array = np.random.randint(0, 256, (28, 28, 3), dtype=np.uint8)
img = Image.fromarray(img_array)
img.save('/tmp/test-image.png')
PYTHON
fi

if [ -f "/tmp/test-image.png" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "http://${HOST}:${PORT}/predict_image" \
        -F "file=@/tmp/test-image.png")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | head -1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Status: 200 OK${NC}"
        echo "Response: $BODY" | head -c 100
        echo ""
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Status: $HTTP_CODE (expected 200)${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ Skipped: Could not create test image${NC}"
    ((TESTS_SKIPPED++))
fi
echo ""

# Test 5: Invalid Request Handling
echo "▶ TEST 5: Invalid request handling"
echo "─────────────────────────────────────────"

# Отправляем неправильное количество пикселей
INVALID_PAYLOAD=$(python3 << 'PYTHON'
import json
import random
pixels = [random.random() for _ in range(100)]  # Wrong size!
print(json.dumps({"pixels": pixels}))
PYTHON
)

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "http://${HOST}:${PORT}/predict" \
    -H "Content-Type: application/json" \
    -d "$INVALID_PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid input (400)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Expected 400 for invalid input, got $HTTP_CODE${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: Performance Test
echo "▶ TEST 6: Response time measurement"
echo "─────────────────────────────────────────"

echo "Measuring 5 requests to /health endpoint..."
TIMES=()
for i in {1..5}; do
    TIME=$(curl -s -o /dev/null -w '%{time_total}' "http://${HOST}:${PORT}/health")
    TIMES+=($TIME)
    echo "  Request $i: ${TIME}s"
done

# Расчет среднего времени
AVG_TIME=$(echo "${TIMES[@]}" | awk '{sum=0; for(i=1;i<=NF;i++) sum+=$i; print sum/NF}')
echo -e "${GREEN}✓ Average response time: ${AVG_TIME}s${NC}"
((TESTS_PASSED++))
echo ""

# Итоговый отчет
echo "═══════════════════════════════════════════════════════════════"
echo "                    TEST SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo -e "Passed:  ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed:  ${RED}${TESTS_FAILED}${NC}"
echo -e "Skipped: ${YELLOW}${TESTS_SKIPPED}${NC}"
echo ""

# Сохраняем результаты
REPORT_FILE="${TEST_RESULTS}/functional-tests-report.txt"
cat > "$REPORT_FILE" << EOF
═══════════════════════════════════════════════════════════════
                 FUNCTIONAL TESTS REPORT
═══════════════════════════════════════════════════════════════
Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')
Target: http://${HOST}:${PORT}

RESULTS:
  Passed:  ${TESTS_PASSED}
  Failed:  ${TESTS_FAILED}
  Skipped: ${TESTS_SKIPPED}

STATUS: $(if [ $TESTS_FAILED -eq 0 ]; then echo "✓ ALL TESTS PASSED"; else echo "✗ SOME TESTS FAILED"; fi)
═══════════════════════════════════════════════════════════════
EOF

cat "$REPORT_FILE"

# Выход с соответствующим кодом
if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All functional tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi
