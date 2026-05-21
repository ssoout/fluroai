"""Скрипт для диагностики проблемы с исследованиями"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("ДИАГНОСТИКА ПРОБЛЕМЫ С ИССЛЕДОВАНИЯМИ")
print("=" * 60)

# 1. Проверяем доступность backend
print("\n1. Проверка доступности backend...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=2)
    if r.status_code == 200:
        print("   ✓ Backend доступен")
    else:
        print(f"   ✗ Backend вернул статус {r.status_code}")
        exit(1)
except Exception as e:
    print(f"   ✗ Backend недоступен: {e}")
    print("\n   Убедитесь, что backend запущен!")
    exit(1)

# 2. Получаем список пациентов
print("\n2. Получение списка пациентов...")
try:
    r = requests.get(f"{BASE_URL}/patients")
    patients = r.json()
    print(f"   Найдено пациентов: {len(patients)}")
    
    if not patients:
        print("   ✗ Нет пациентов в БД")
        print("   Создайте пациента через frontend")
        exit(1)
    
    # Берем первого пациента
    test_patient = patients[0]
    patient_id = test_patient['id']
    print(f"   Тестовый пациент: ID={patient_id}, Имя={test_patient.get('full_name')}")
except Exception as e:
    print(f"   ✗ Ошибка: {e}")
    exit(1)

# 3. Проверяем endpoint для получения исследований
print(f"\n3. Проверка endpoint GET /patients/{patient_id}/studies...")
try:
    r = requests.get(f"{BASE_URL}/patients/{patient_id}/studies")
    print(f"   Статус ответа: {r.status_code}")
    
    if r.status_code == 200:
        studies = r.json()
        print(f"   ✓ Endpoint работает!")
        print(f"   Найдено исследований: {len(studies)}")
        
        if studies:
            print("   Исследования:")
            for s in studies:
                print(f"     - ID={s.get('id')}, Patient ID={s.get('patient_id')}, Дата={s.get('taken_at')}")
        else:
            print("   ⚠ У пациента нет исследований")
            print("\n   Попробуйте:")
            print("   1. Создать исследование через frontend")
            print("   2. Загрузить изображение")
            print("   3. Проверить логи backend при создании")
    elif r.status_code == 404:
        print(f"   ✗ 404 Not Found")
        print(f"   Ответ: {r.text}")
        print("\n   ПРОБЛЕМА: Endpoint не найден!")
        print("   Решение: Перезапустите backend")
    else:
        print(f"   ✗ Ошибка {r.status_code}")
        print(f"   Ответ: {r.text}")
except Exception as e:
    print(f"   ✗ Ошибка при запросе: {e}")

# 4. Проверяем все исследования в БД
print(f"\n4. Проверка всех исследований в БД...")
try:
    r = requests.get(f"{BASE_URL}/studies")
    all_studies = r.json()
    print(f"   Всего исследований в БД: {len(all_studies)}")
    
    if all_studies:
        print("   Все исследования:")
        for s in all_studies:
            print(f"     - ID={s.get('id')}, Patient ID={s.get('patient_id')}, Дата={s.get('taken_at')}")
        
        # Проверяем, есть ли исследования у тестового пациента
        patient_studies = [s for s in all_studies if s.get('patient_id') == patient_id]
        print(f"\n   Исследований у пациента ID={patient_id}: {len(patient_studies)}")
        
        if len(patient_studies) > 0:
            print("   ✓ Исследования есть в БД, но не возвращаются через endpoint!")
            print("   ПРОБЛЕМА: Endpoint /patients/{id}/studies не работает правильно")
        else:
            print("   ⚠ У пациента действительно нет исследований")
    else:
        print("   ⚠ В БД нет исследований")
except Exception as e:
    print(f"   ✗ Ошибка: {e}")

# 5. Проверяем OpenAPI схему
print(f"\n5. Проверка зарегистрированных маршрутов...")
try:
    r = requests.get(f"{BASE_URL}/openapi.json")
    openapi = r.json()
    paths = list(openapi['paths'].keys())
    
    patient_studies_route = f"/patients/{{patient_id}}/studies"
    if any('studies' in p and 'patients' in p for p in paths):
        print(f"   ✓ Маршрут для исследований пациента зарегистрирован")
        matching = [p for p in paths if 'studies' in p and 'patients' in p]
        for p in matching:
            print(f"     - {p}")
    else:
        print(f"   ✗ Маршрут {patient_studies_route} НЕ зарегистрирован!")
        print("   РЕШЕНИЕ: Перезапустите backend")
except Exception as e:
    print(f"   ✗ Ошибка: {e}")

print("\n" + "=" * 60)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 60)


