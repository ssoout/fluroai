"""Скрипт для проверки endpoint /patients/{patient_id}/studies"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("ПРОВЕРКА ENDPOINT /patients/{patient_id}/studies")
print("=" * 60)

# 1. Проверяем доступность backend
print("\n1. Проверка доступности backend...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=2)
    if r.status_code == 200:
        print("   ✓ Backend доступен")
    else:
        print(f"   ✗ Backend вернул статус {r.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Backend недоступен: {e}")
    print("\n   ВАЖНО: Убедитесь, что backend запущен!")
    print("   Запустите: python -m uvicorn backend.app:app --reload")
    sys.exit(1)

# 2. Проверяем OpenAPI схему
print("\n2. Проверка зарегистрированных маршрутов...")
try:
    r = requests.get(f"{BASE_URL}/openapi.json")
    openapi = r.json()
    paths = list(openapi['paths'].keys())
    
    patient_routes = [p for p in paths if 'patients' in p]
    print(f"   Всего маршрутов с 'patients': {len(patient_routes)}")
    for route in patient_routes:
        print(f"     - {route}")
    
    studies_route = "/patients/{patient_id}/studies"
    if any('studies' in p and 'patients' in p for p in paths):
        print(f"\n   ✓ Маршрут {studies_route} ЗАРЕГИСТРИРОВАН")
    else:
        print(f"\n   ✗ Маршрут {studies_route} НЕ ЗАРЕГИСТРИРОВАН")
        print("\n   ПРОБЛЕМА: Backend не видит маршрут из кода!")
        print("   РЕШЕНИЕ: Перезапустите backend:")
        print("   1. Остановите текущий backend (Ctrl+C)")
        print("   2. Запустите: python -m uvicorn backend.app:app --reload")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Ошибка при проверке OpenAPI: {e}")
    sys.exit(1)

# 3. Проверяем существование пациента
print("\n3. Проверка существования пациентов...")
try:
    r = requests.get(f"{BASE_URL}/patients")
    patients = r.json()
    print(f"   Найдено пациентов: {len(patients)}")
    if patients:
        test_patient_id = patients[0]['id']
        print(f"   Тестируем с patient_id={test_patient_id}")
    else:
        print("   ✗ Нет пациентов в БД")
        print("   Создайте пациента через frontend")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Ошибка при получении пациентов: {e}")
    sys.exit(1)

# 4. Тестируем endpoint
print(f"\n4. Тестирование GET /patients/{test_patient_id}/studies...")
try:
    r = requests.get(f"{BASE_URL}/patients/{test_patient_id}/studies")
    print(f"   Статус: {r.status_code}")
    
    if r.status_code == 200:
        studies = r.json()
        print(f"   ✓ УСПЕХ! Найдено исследований: {len(studies)}")
        for study in studies:
            print(f"     - ID={study.get('id')}, Дата={study.get('taken_at')}")
    elif r.status_code == 404:
        print(f"   ✗ 404 Not Found")
        print(f"   Ответ: {r.text[:200]}")
        print("\n   Возможные причины:")
        print("   1. Маршрут не зарегистрирован (перезапустите backend)")
        print("   2. Пациент не найден")
    else:
        print(f"   ✗ Ошибка {r.status_code}")
        print(f"   Ответ: {r.text[:200]}")
except Exception as e:
    print(f"   ✗ Ошибка при запросе: {e}")

print("\n" + "=" * 60)


