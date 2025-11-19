import requests
from bs4 import BeautifulSoup

def parse_fish_info(url):
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'lxml')
    fish_list = []
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 2:
            continue
        # 공지 아이콘 또는 div로 구분
        is_notice = False
        # 1. <img alt="공지">
        img = tds[0].find('img', alt='공지')
        if img:
            is_notice = True
        # 2. <div>공지</div>
        div = tds[0].find('div')
        if div and '공지' in div.get_text(strip=True):
            is_notice = True
        if not is_notice:
            continue
        # 어종 정보 추출: 두 번째 <td>의 텍스트(HTML 태그 제거)
        fish_text = tds[1].get_text(separator=' ', strip=True)
        # 불필요한 기호/공백 정리
        fish_text = fish_text.replace('\n', ' ').replace('\r', ' ')
        fish_text = ' '.join(fish_text.split())
        if fish_text:
            fish_list.append(fish_text)
    return fish_list

if __name__ == '__main__':
    url = "http://xn--hq1b31ko5fzpfdsxrtb.com/index.php?mid=bk&year=2025&month=12&day=14&mode=list&won=1&PA_N_UID=0&sel=day"
    fish = parse_fish_info(url)
    print(fish)
