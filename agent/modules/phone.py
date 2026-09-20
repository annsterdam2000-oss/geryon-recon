# agent/modules/phone.py
import phonenumbers
from phonenumbers import (
    geocoder,
    carrier,
    timezone as pn_timezone,
    number_type,
    PhoneNumberType,
    NumberParseException,
)


NUMBER_TYPE_NAMES = {
    PhoneNumberType.MOBILE: "мобильный",
    PhoneNumberType.FIXED_LINE: "стационарный",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "стационарный или мобильный",
    PhoneNumberType.TOLL_FREE: "бесплатный (toll-free)",
    PhoneNumberType.PREMIUM_RATE: "премиум",
    PhoneNumberType.SHARED_COST: "shared cost",
    PhoneNumberType.VOIP: "VoIP",
    PhoneNumberType.PERSONAL_NUMBER: "личный",
    PhoneNumberType.PAGER: "пейджер",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "голосовая почта",
    PhoneNumberType.UNKNOWN: "неизвестно",
}


def module_phone(target: str) -> dict:
    target = target.strip()
    result = {"target": target}

    # Парсим номер. Пытаемся угадать регион, если не указан +.
    try:
        parsed = phonenumbers.parse(target, None)
    except NumberParseException as e:
        # Попробуем как российский по умолчанию — часто это самый частый кейс
        try:
            parsed = phonenumbers.parse(target, "RU")
            result["_assumed_region"] = "RU"
        except NumberParseException as e2:
            return {"error": f"не удалось распарсить номер: {e}"}

    # Валидность
    result["is_valid"] = phonenumbers.is_valid_number(parsed)
    result["is_possible"] = phonenumbers.is_possible_number(parsed)

    # Страна
    region_code = phonenumbers.region_code_for_number(parsed)
    result["country_code"] = parsed.country_code
    result["national_number"] = parsed.national_number
    result["region_code"] = region_code

    # Регион (город)
    try:
        region = geocoder.description_for_number(parsed, "ru")
        result["region"] = region or None
    except Exception:
        result["region"] = None

    # Также на английском — иногда русский пустой
    try:
        region_en = geocoder.description_for_number(parsed, "en")
        result["region_en"] = region_en or None
    except Exception:
        result["region_en"] = None

    # Оператор
    try:
        carrier_name = carrier.name_for_number(parsed, "ru")
        if not carrier_name:
            carrier_name = carrier.name_for_number(parsed, "en")
        result["carrier"] = carrier_name or None
    except Exception:
        result["carrier"] = None

    # Тип линии
    try:
        ntype = number_type(parsed)
        result["number_type"] = NUMBER_TYPE_NAMES.get(ntype, "неизвестно")
    except Exception:
        result["number_type"] = "неизвестно"

    # Часовые пояса
    try:
        tzs = pn_timezone.time_zones_for_number(parsed)
        result["timezones"] = list(tzs) if tzs else []
    except Exception:
        result["timezones"] = []

    # Форматы
    try:
        result["formats"] = {
            "international": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "national": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "e164": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            ),
            "rfc3966": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.RFC3966
            ),
        }
    except Exception:
        result["formats"] = {}

    # Геокодер иногда отдаёт "Россия" без города — попробуем ещё раз для мобильных
    if not result.get("region") and region_code:
        try:
            region2 = geocoder.description_for_valid_number(parsed, "ru")
            if region2:
                result["region"] = region2
        except Exception:
            pass

    return result