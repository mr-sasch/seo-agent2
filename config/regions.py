YANDEX_REGIONS = {
    157: "Минск"
}

# Функция для получения кода региона по названию
def get_region_code(city_name: str) -> int:
    city_lower = city_name.lower()
    for code, name in YANDEX_REGIONS.items():
        if city_lower in name.lower():
            return code
    return 213  # Москва по умолчанию