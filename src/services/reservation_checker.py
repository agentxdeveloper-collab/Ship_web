from bs4 import BeautifulSoup, Comment
from typing import Dict, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import requests
import re
import datetime
import json

def build_query_url(base_url: str, year: int, month: int, day: int) -> str:
    """
    URL 패턴에 따라 적절한 쿼리 파라미터를 구성합니다.
    sunsang24.com 도메인(또는 기존에 schedule_fleet이 포함된 경우)은
    /ship/schedule_fleet/YYYYMM 형태로 처리합니다.
    그 외 도메인은 기존처럼 쿼리 파라미터를 추가합니다.
    """
    parsed = urlparse(base_url)
    path = parsed.path or ""
    netloc = (parsed.netloc or "").lower()
    query = parse_qs(parsed.query or "")

    # sunsang24 도메인 또는 기존 schedule_fleet 경로는 schedule_fleet 처리
    if 'sunsang24.com' in netloc or 'schedule_fleet' in path:
        scheme = parsed.scheme or "https"
        new_path = f"/ship/schedule_fleet/{year:04d}{month:02d}"
        return urlunparse((scheme, parsed.netloc, new_path, "", "", ""))

    # 일반 게시판 패턴 (예: index.php?mid=bk) — 기존 쿼리 유지 후 날짜 파라미터 추가
    query.update({
        'year': [f"{year:04d}"],
        'month': [f"{month:02d}"],
        'day': [f"{day:02d}"],
        'mode': ['list'],
        'won': ['1'],
        'PA_N_UID': ['0'],
        'sel': ['day']
    })
    query_string = urlencode({k: v[0] for k, v in query.items()})
    scheme = parsed.scheme or "https"
    return urlunparse((scheme, parsed.netloc, parsed.path, "", query_string, ""))

def _headers_for(url: str, alt: bool = False) -> dict:
    p = urlparse(url)
    scheme = p.scheme or "https"
    referer = f"{scheme}://{p.netloc}/"
    if not alt:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    else:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
    }

def _weekday_kor(year: int, month: int, day: int) -> str:
    return "월화수목금토일"[datetime.date(year, month, day).weekday()]

def _parse_tide_from_text(text: str) -> str | None:
    m = re.search(r'(\d+)\s*물', text)
    return f"{m.group(1)}물" if m else None

def check_single_boat(boat_url: str, year: int, month: int, day: int, debug_enabled: bool = False) -> Dict:
    final_url = build_query_url(boat_url, year, month, day)

    # 요일/표시 날짜(물때는 응답 후 보강)
    weekday = _weekday_kor(year, month, day)
    display_date = f"{year:04d}-{month:02d}-{day:02d}({weekday})"

    # 1차 시도: 정상 헤더 (타임아웃 10초)
    try:
        resp = requests.get(final_url, headers=_headers_for(final_url), timeout=10)
    except requests.RequestException as e:
        return {"used_url": final_url, "display_date": display_date, "entries": [], "error": f"http_error:{e}"}

    # 403이면 UA/Referer 바꿔 재시도 + http 스킴 폴백
    if resp.status_code == 403:
        try:
            resp = requests.get(final_url, headers=_headers_for(final_url, alt=True), timeout=10)
        except requests.RequestException:
            resp = None

        if (resp is None) or (resp.status_code == 403 and final_url.startswith("https://")):
            try:
                http_url = "http://" + final_url[len("https://"):]
                resp = requests.get(http_url, headers=_headers_for(http_url, alt=True), timeout=10)
                final_url = http_url  # 실제 사용 URL 갱신
            except requests.RequestException:
                pass

    # 여전히 200이 아니면 예외를 던지지 않고 빈 결과 반환 (500 방지)
    if resp is None or resp.status_code != 200:
        return {
            "used_url": final_url,
            "display_date": display_date,
            "entries": [],
            "error": f"http_status:{getattr(resp, 'status_code', 'unknown')}"
        }

    soup = BeautifulSoup(resp.text, "html.parser")

    # 판단 기준: target의 호스트가 sunsang24.com 이거나 path에 schedule_fleet가 있으면 기존 패턴 사용
    parsed_target = urlparse(final_url)
    target_netloc = (parsed_target.netloc or "").lower()
    use_schedule_pattern = ('sunsang24.com' in target_netloc) or ('schedule_fleet' in parsed_target.path)

    if use_schedule_pattern:
        date_id = f"d{year:04d}-{month:02d}-{day:02d}"
        day_block = soup.find(id=date_id) or soup.select_one('.shipsinfo_daywarp.weekday')

        if not day_block:
            # try comment-based search
            for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
                if "날자별 선단 소속 선박 리스트" in str(comment):
                    nxt = comment
                    for _ in range(8):
                        nxt = nxt.next_sibling
                        if not nxt:
                            break
                        if getattr(nxt, 'select', None):
                            found = nxt.select_one(f".shipsinfo_daywarp#{date_id}, .shipsinfo_daywarp.weekday, .shipsinfo_daywarp")
                            if found:
                                day_block = found
                                break

        if not day_block:
            return {"matched": False, "date_id": date_id, "source_url": final_url, "entries": [], "tide": None}

        # extract tide info from .date_info2
        tide = None
        date_info2_el = day_block.select_one('.date_info2')
        if date_info2_el:
            tide = date_info2_el.get_text(separator=' ', strip=True)

        # 어종 추출: div#fish 또는 .fish 우선, 없으면 '낚시종류' 라벨 주변에서 시도
        fish = None
        fish_el = day_block.select_one('div#fish') or day_block.select_one('.fish') or soup.select_one('div#fish')
        if fish_el:
            fish = fish_el.get_text(" ", strip=True)
        else:
            label_text = day_block.find(string=re.compile(r'낚시종류'))
            if label_text:
                parent = label_text.parent
                if parent and parent.name == 'td':
                    sib = parent.find_next_sibling('td')
                    if sib:
                        fish = sib.get_text(" ", strip=True)
                else:
                    nxt = label_text.find_next()
                    if nxt and getattr(nxt, 'get_text', None):
                        fish = nxt.get_text(" ", strip=True)

        # debug: schedule_fleet 패턴에서 추출된 어종 확인
        if debug_enabled:
            try:
                print(json.dumps({"DEBUG_FISH_SCHEDULE": fish, "date": display_date, "url": final_url}, ensure_ascii=False))
            except Exception:
                print("DEBUG_FISH_SCHEDULE:", fish, display_date, final_url)

        entries = []
        ship_tables = day_block.select('table.ship_unit, table[class*="ship_unit_"], table.ship_unit_ship_no_918, .ships_warp table')
        if not ship_tables:
            ship_tables = [t for t in day_block.find_all('table') if t.select_one('.title') or t.select_one('.ship_info')]

        for t in ship_tables:
            # find title
            title_el = t.select_one('.ship_info .title') or t.select_one('.title')
            ship_name = title_el.get_text(strip=True) if title_el else None

            # ship_info2 status
            status_el = t.select_one('.ship_info2 .shipping_status') or t.select_one('.ship_info2') or None
            status_text = status_el.get_text(separator=' ', strip=True) if status_el else ""
            status_code = status_el.get('data-status_code') if status_el and status_el.has_attr('data-status_code') else None

            # remaining seats
            avail = None
            num_el = t.select_one('span.number.blink_me.n_blue.f_20') or t.select_one('.ship_info2 .number') or t.select_one('.number')
            if num_el:
                mnum = re.search(r'(\d+)', num_el.get_text())
                if mnum:
                    avail = int(mnum.group(1))

            if re.search(r'점검일', status_text):
                status = 'maintenance'
                avail = 0
                display_status = "점검일"
            elif status_code == 'END' or re.search(r'(예약마감|매진|마감)', status_text):
                status = 'full'
                if avail is None:
                    avail = 0
                display_status = "예약마감"
            elif re.search(r'예약\s*완료', status_text):
                status = 'reserved'
                avail = 0
                display_status = "예약완료"
            elif avail is not None and avail > 0:
                status = 'open'
                display_status = f"남은자리 {avail}명"
            else:
                status = 'unknown'
                display_status = status_text or "알 수 없음"

            # --- changed: 배별 어종(fish) 추출 ---
            ship_fish = None
            # 1) 선박 테이블 내부에서 어종 셀렉터 우선 탐색
            ship_fish_el = (
                t.select_one('.ship_info .fish') or
                t.select_one('.ship_info2 .fish') or
                t.select_one('.fish') or
                t.select_one('div.fish') or
                t.select_one('span.fish') or
                t.select_one('.ship_kinds') or
                t.select_one('.ship_kind') or
                t.select_one('.tags') or
                t.select_one('.tag_area')
            )
            if ship_fish_el:
                ship_fish_text = ship_fish_el.get_text(" ", strip=True)
                # 라벨 제거 (낚시종류:, 어종: 등)
                ship_fish = re.sub(r'(낚시\s*종류|낚시종류|어종)\s*[:：-]?\s*', '', ship_fish_text, flags=re.I).strip()
            
            # 2) 라벨 기반 탐색 (테이블 내 "낚시종류" 또는 "어종" 라벨)
            if not ship_fish:
                lbl = t.find(string=re.compile(r'(낚시\s*종류|어종)', re.I))
                if lbl:
                    p = getattr(lbl, 'parent', None)
                    if p and getattr(p, 'name', None) == 'td':
                        sib = p.find_next_sibling('td')
                        if sib:
                            txt = sib.get_text(" ", strip=True)
                            ship_fish = re.sub(r'(낚시\s*종류|낚시종류|어종)\s*[:：-]?\s*', '', txt, flags=re.I).strip()
                    if not ship_fish:
                        nxt = lbl.find_next()
                        if nxt and getattr(nxt, 'get_text', None):
                            txt = nxt.get_text(" ", strip=True)
                            ship_fish = re.sub(r'(낚시\s*종류|낚시종류|어종)\s*[:：-]?\s*', '', txt, flags=re.I).strip()
            
            # 3) 페이지 전체(day_block) 어종을 최종 폴백
            if not ship_fish:
                ship_fish = fish
            # ---------------------------------------
            
            # debug: 파싱된 항목 콘솔 출력
            if debug_enabled:
                try:
                    print(json.dumps({
                        "DEBUG_SCHEDULE_ENTRY": {
                            "ship_name": ship_name,
                            "status": status,
                            "available": avail,
                            "display_status": display_status,
                            "raw_status_text": status_text,
                            "fish": ship_fish,  # 배별 어종
                            "query_date": display_date,
                            "row_html_len": len(str(t))
                        }
                    }, ensure_ascii=False))
                except Exception:
                    print("DEBUG_SCHEDULE_ENTRY:", ship_name, status, avail, display_status, ship_fish)
            entries.append({
                "ship_name": ship_name,
                "status": status,
                "available": avail,
                "raw_status_text": status_text,
                "display_status": display_status,
                "row_html": str(t),
                "query_date": display_date,
                "fish": ship_fish  # 배별 어종
            })

        return {"matched": True, "entries": entries, "date_id": date_id, "source_url": final_url, "tide": tide}

        # 일반 게시판 패턴
    else:
        tide = None
        # new-div-YYYYMMDD 컨테이너에서 선박별 행을 추출
        entries = []
        date8 = f"{int(year):04d}{int(month):02d}{int(day):02d}"

        # 대표 컨테이너 찾기
        container = soup.select_one(f"div#new-div-{date8}") or soup.select_one(f"div.new-divs, .new-divs")

        # 물때 정보 추출 (jeil-panel tr의 data-str 속성에서)
        if container:
            jeil_panel_tr = container.select_one('tr.jeil-panel')
            if jeil_panel_tr and jeil_panel_tr.has_attr('data-str'):
                data_str = jeil_panel_tr['data-str']
                m = re.search(r'(\d+)\s*물', data_str)
                if m:
                    tide = f"{m.group(1)}물"

        # 일반 게시판에서도 어종 추출 시도
        fish = None
        if container:
            fish_el = container.select_one('div#fish') or container.select_one('.fish') or soup.select_one('div#fish')
            if fish_el:
                fish = fish_el.get_text(" ", strip=True)
            else:
                # 텍스트 또는 img alt 속성으로 "낚시종류" 라벨 찾기
                label_tag = container.find(lambda tag: tag.name == 'div' and tag.string and tag.string.strip() == '낚시종류')
                if not label_tag:
                    label_tag = container.find('img', alt='낚시종류')
                if label_tag:
                    # 가장 가까운 'td' 부모를 찾고, 그 다음 'td' 형제를 찾음
                    label_td = label_tag.find_parent('td')
                    if label_td:
                        fish_td = label_td.find_next_sibling('td')
                        if fish_td:
                            fish = fish_td.get_text(" ", strip=True)

        # debug: 일반 게시판에서 추출된 어종 확인
        if debug_enabled:
            try:
                print(json.dumps({"DEBUG_FISH_BOARD": fish, "date": display_date, "url": final_url}, ensure_ascii=False))
            except Exception:
                print("DEBUG_FISH_BOARD:", fish, display_date, final_url)

        if container:
            rows = container.select("tr")
            exclude_keywords = {"공지사항", "입금대기", "선박명", "공지", "오늘:"}
            current_fish = fish  # 페이지 레벨 어종으로 시작

            for tr in rows:
                tds = tr.find_all("td")
                if not tds:
                    continue

                # 어종 정보 행인지 확인 (td가 2개이고 첫번째에 '낚시종류' 포함)
                first_td_text = tds[0].get_text(" ", strip=True)
                if '낚시종류' in first_td_text and len(tds) >= 2:
                    current_fish = tds[1].get_text(" ", strip=True).strip()
                    # 어종 정보 행은 보트가 아니므로 건너뜀
                    continue

                # 보트 행이 아니면 건너뜀 (td 갯수 등)
                if len(tds) < 3:
                    continue

                # 1번째 td에서 선박명 추출
                ship_name = tds[0].get_text(" ", strip=True)

                # 불필요한 행(헤더/공지 등) 제거
                if not ship_name:
                    continue
                lowered = ship_name.replace(" ", "")
                skip = False
                for kw in exclude_keywords:
                    if kw in ship_name or kw in lowered:
                        skip = True
                        break
                if skip:
                    continue

                # 3번째 td (또는 admin-right div)가 실제 상태/잔여 정보를 가지고 있는 경우 추출
                admin_div = None
                if len(tds) >= 3:
                    admin_div = tds[2].select_one('div[id^="admin-right-"]')
                if not admin_div:
                    admin_div = tr.select_one('div[id^="admin-right-"]')

                raw_status_text = ""
                available = None
                status_type = "unknown"

                if admin_div:
                    img = admin_div.find("img")
                    if img and img.has_attr("alt"):
                        raw_status_text = img["alt"].strip()
                    else:
                        raw_status_text = admin_div.get_text(" ", strip=True)

                    if re.search(r'점검일', raw_status_text):
                        status_type = "maintenance"
                        available = 0
                    else:
                        m = re.search(r'남은\s*자리\s*[:：]?\s*(\d+)', raw_status_text) or                             re.search(r'남은자리\s*(\d+)', raw_status_text) or                             re.search(r'(\d+)\s*명', raw_status_text)

                        if m:
                            try:
                                available = int(m.group(1))
                                status_type = "open"
                            except Exception:
                                available = None
                                status_type = "unknown"
                        elif re.search(r'예약완료|예약 완료', raw_status_text):
                            status_type = "reserved"
                            available = 0
                        elif re.search(r'매진|마감|예약마감', raw_status_text):
                            status_type = "full"
                            available = 0
                        else:
                            status_type = "unknown"
                else:
                    second_text = tds[1].get_text(" ", strip=True)
                    raw_status_text = second_text
                    if re.search(r'입금대기', second_text):
                        status_type = "pending"
                    elif re.search(r'예약\s*완료', raw_status_text):
                        status_type = "reserved"
                        available = 0
                    else:
                        status_type = "unknown"

                display_status = "-"
                if status_type == "maintenance":
                    display_status = "점검일"
                elif status_type == "reserved":
                    display_status = "예약마감"
                elif status_type == "open" and available is not None:
                    display_status = f"남은자리 {available}명"
                elif status_type == "full":
                    display_status = "예약마감"
                elif status_type == "pending":
                    display_status = "입금대기"
                else:
                    display_status = raw_status_text or "알 수 없음"

                # debug: 출력하여 파싱 결과 확인
                if debug_enabled:
                    try:
                        print(json.dumps({
                            "DEBUG_BOARD_ENTRY": {
                                "ship_name": ship_name,
                                "status": status_type,
                                "available": available,
                                "display_status": display_status,
                                "raw_status_text": raw_status_text,
                                "fish": current_fish,
                                "row_html_len": len(str(tr))
                            }
                        }, ensure_ascii=False))
                    except Exception:
                        print("DEBUG_BOARD_ENTRY:", ship_name, status_type, available, display_status, current_fish)

                entries.append({
                    "ship_name": ship_name,
                    "status": status_type,
                    "available": available,
                    "raw_status_text": raw_status_text,
                    "display_status": display_status,
                    "row_html": str(tr),
                    "fish": current_fish
                })

        # matched True로 반환하되 entries가 비어있을 수 있음
        return {
            "matched": True,
            "entries": entries,
            "source_url": final_url,
            "raw_html": resp.text[:1000],  # 디버깅용 요약
            "tide": tide
        }

# 예시: 조회 함수에서 지역 필터링 적용
def filter_entries_by_region(entries, selected_regions):
    # selected_regions: ["인천", "안산", ...]
    return [e for e in entries if e.get("city") in selected_regions]