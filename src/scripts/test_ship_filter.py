"""배 이름 필터링 및 정리 테스트"""
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.reservation_checker import _is_valid_ship_name, _clean_ship_name

# 필터링 테스트 케이스
filter_test_cases = [
    # (이름, 예상 결과)
    ("팀만수", True),
    ("금강7호", True),
    ("조커호", True),
    ("힐링피싱", True),
    ("레드헌터", True),
    ("레드히어로", True),
    ("공지사항", False),
    ("알림", False),
    ("협력선박알림", False),
    ("협력선단", False),
    ("카라반 캠핑카 예약하기", False),
    ("우리좌대 우리좌대 예약하기", False),
    ("우리좌대 1번 독좌대 예약하기", False),
    ("우리좌대 2번 독좌대 예약하기", False),
    ("해변팬션예약 예약하기", False),
]

# 정리 테스트 케이스
clean_test_cases = [
    # (입력, 예상 출력)
    ("조커호 예약하기", "조커호"),
    ("예약하기 조커호", "조커호"),
    ("금강7호 예약하기", "금강7호"),
    ("팀만수", "팀만수"),
    ("카라반 캠핑카 예약하기", "카라반 캠핑카"),
]

print("=" * 60)
print("배 이름 필터링 테스트:\n")
all_passed = True

for name, expected in filter_test_cases:
    result = _is_valid_ship_name(name)
    status = "✓" if result == expected else "✗"
    if result != expected:
        all_passed = False
    print(f"{status} '{name}': {result} (예상: {expected})")

print("\n" + ("=" * 60))
print("배 이름 정리 테스트:\n")

for input_name, expected_output in clean_test_cases:
    result = _clean_ship_name(input_name)
    status = "✓" if result == expected_output else "✗"
    if result != expected_output:
        all_passed = False
    print(f"{status} '{input_name}' → '{result}' (예상: '{expected_output}')")

print("\n" + ("=" * 60))
if all_passed:
    print("✓ 모든 테스트 통과!")
else:
    print("✗ 일부 테스트 실패")
