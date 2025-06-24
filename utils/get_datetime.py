# utils/get_datetime.py

from datetime import date, datetime, timedelta

def _get_next_sunday_date(target_date: date = None) -> date:
    """
    주어진 날짜를 기준으로 가장 가까운 다가오는 일요일의 날짜를 반환합니다.
    (오늘이 일요일이면 다음 주 일요일을 반환하여, 항상 '미래의' 주일을 지향합니다.)
    """
    if target_date is None:
        target_date = date.today()

    # 요일 가져오기 (월요일=0, 일요일=6)
    days_until_sunday = (6 - target_date.weekday() + 7) % 7 # 0부터 6까지

    # target_date가 일요일이면, 다음 주 일요일 (+7일)
    # target_date가 일요일이 아니면, 이번 주 일요일 (+days_until_sunday)
    if target_date.weekday() == 6: # 오늘이 일요일이면
        return target_date + timedelta(days=7) # 다음 주 일요일
    else:
        return target_date + timedelta(days=days_until_sunday) # 이번 주 일요일


def _get_week_of_month(target_date_obj: date) -> int:
    """
    주어진 날짜가 해당 월의 몇째 주에 해당하는지 계산합니다.
    """
    first_day_of_month = target_date_obj.replace(day=1)
    
    # 해당 월 1일의 요일 (월요일=0, 일요일=6)
    # 계산의 편의를 위해 1일이 몇 번째 '주'에 속하는지 파악
    # 예: 1일이 수요일(2)이면, 첫째 주에 3일이 포함됨. 1일이 일요일(6)이면, 첫째 주에 1일이 포함됨.
    # 0일부터 시작하는 요일 인덱스를 주 단위로 맞추기 위해 0일차를 월요일로 가정하고 (target_date_obj.day -1) + first_day_of_month.weekday()
    # 즉, 1일이 월요일이면 adjusted_dom = date.day. 1일이 일요일이면 adjusted_dom = date.day + 6
    adjusted_day_of_month = target_date_obj.day + first_day_of_month.weekday()
    
    # 0부터 시작하는 주 번호를 1부터 시작하도록 조정
    return (adjusted_day_of_month - 1) // 7 + 1


def get_sunday_text(target_date: date = None) -> str:
    """
    주어진 날짜를 기준으로 가장 가까운 다가오는 일요일의 날짜를
    'YYYY년 MM월 X째주' 형식으로 반환합니다.
    """
    sunday_date = _get_next_sunday_date(target_date) # 변경된 헬퍼 함수 사용
    year = sunday_date.year
    month = sunday_date.month
    week_of_month = _get_week_of_month(sunday_date)
    
    week_texts = ["첫째주", "둘째주", "셋째주", "넷째주", "다섯째주", "여섯째주"] # 혹시 모를 6째주까지 대비
    
    # week_of_month가 1에서 6 사이의 값이라고 가정
    if 1 <= week_of_month <= len(week_texts):
        week_text = week_texts[week_of_month - 1]
    else:
        week_text = f"{week_of_month}째주" # 예외 처리

    return f"{year}년 {month}월 {week_text}"

# 기존 get_sunday_date 함수는 이제 _get_next_sunday_date로 대체됩니다.
# core/tasks.py 및 core/views.py에서 get_sunday_text만 사용하도록 변경되었으므로,
# 이 파일에서 get_sunday_date는 더 이상 노출되지 않습니다.
