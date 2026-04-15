# =========================================
# DATE UTILITIES
# =========================================

from datetime import date

from frappe.utils import getdate


# =========================================
# أدوات مساعدة عامة للتواريخ
# =========================================

def convert_to_date(value):
    # تحويل أي قيمة إلى تاريخ باستخدام getdate
    if not value:
        return None

    return getdate(value)


def is_valid_date_range(start_date, end_date):
    # التحقق أن الفترة الزمنية صحيحة (تاريخ البداية قبل أو يساوي النهاية)
    if not start_date:
        return False

    if not end_date:
        return False

    if end_date < start_date:
        return False

    return True


# =========================================
# حساب عدد الأيام (شامل البداية والنهاية)
# =========================================

def inclusive_days(start_date, end_date) -> int:
    # حساب عدد الأيام بين تاريخين بشكل شامل (inclusive)
    start = convert_to_date(start_date)
    end = convert_to_date(end_date)

    if not start:
        return 0

    if not end:
        return 0

    if not is_valid_date_range(start, end):
        return 0

    difference_in_days = (end - start).days

    return difference_in_days + 1


# =========================================
# بداية الشهر
# =========================================

def month_first_day(any_date) -> date:
    # إرجاع أول يوم في الشهر للتاريخ المعطى
    current_date = convert_to_date(any_date)

    if not current_date:
        return None

    year = current_date.year
    month = current_date.month

    return date(year, month, 1)


# =========================================
# عدد أيام الشهر
# =========================================

def get_next_month_first_day(current_date):
    # إرجاع أول يوم في الشهر التالي
    year = current_date.year
    month = current_date.month

    if month == 12:
        return date(year + 1, 1, 1)

    return date(year, month + 1, 1)


def days_in_month(any_date) -> int:
    # حساب عدد أيام الشهر للتاريخ المعطى
    current_date = convert_to_date(any_date)

    if not current_date:
        return 0

    first_day_of_month = date(current_date.year, current_date.month, 1)
    first_day_of_next_month = get_next_month_first_day(current_date)

    number_of_days = (first_day_of_next_month - first_day_of_month).days

    return number_of_days


# =========================================
# حساب التداخل بين فترتين
# =========================================

def get_overlap_start_date(a_start, b_start):
    # إرجاع أكبر تاريخ بداية بين فترتين
    return max(convert_to_date(a_start), convert_to_date(b_start))


def get_overlap_end_date(a_end, b_end):
    # إرجاع أصغر تاريخ نهاية بين فترتين
    return min(convert_to_date(a_end), convert_to_date(b_end))


def overlap_inclusive_days(a_start, a_end, b_start, b_end) -> int:
    # حساب عدد الأيام المتداخلة بين فترتين بشكل شامل

    overlap_start = get_overlap_start_date(a_start, b_start)
    overlap_end = get_overlap_end_date(a_end, b_end)

    if not is_valid_date_range(overlap_start, overlap_end):
        return 0

    return inclusive_days(overlap_start, overlap_end)