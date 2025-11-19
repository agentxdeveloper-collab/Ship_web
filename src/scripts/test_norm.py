import re

def _norm(text):
    if not text:
        return ''
    # \u00a0 등 non-breaking space 포함 다양한 공백/구분자 제거
    return re.sub(r"[\s\u00a0/&(),·\-]+", "", str(text))

samples = [
    "다운샷&외수질 (먼바다)",
    "광어다운샷(외수질출조)",
    "문어출조",
]

keywords = [
    '주꾸미', '쭈꾸미', '문어', '갑오징어', '우럭', '광어', '낙지', '백조기', '민어',
    '삼치', '쭈갑', '참돔', '갈치', '다운샷', '생미끼', '돌문어', '피문어', '외수질',
    '광어다운샷'
]

for s in samples:
    norm_s = _norm(s)
    print(f"\nOriginal: {s}")
    print(f"Normalized: {norm_s}")
    found = []
    for w in keywords:
        if _norm(w) in norm_s:
            found.append(w)
    print(f"Matched: {found}")
