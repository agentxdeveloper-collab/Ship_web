import requests
from bs4 import BeautifulSoup

url = 'https://teammansu.kr/index.php?mid=bk'
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(resp.content, 'html.parser')

all_trs = soup.find_all('tr')
print(f'Total TRs: {len(all_trs)}')
print()

# Find TRs containing notice images or text
for i, tr in enumerate(all_trs):
    tr_str = str(tr)
    imgs = tr.find_all('img')
    
    # Check for notice patterns
    has_notice_text = '공지' in tr_str
    has_notice_img = any('myfishmap.kr' in img.get('src', '') and '20190709' in img.get('src', '') for img in imgs)
    
    if has_notice_text or has_notice_img:
        tds = tr.find_all('td')
        print(f'TR {i}: tds={len(tds)}, imgs={len(imgs)}')
        for img in imgs:
            print(f'  IMG: alt={img.get("alt")}, src={img.get("src", "")[:80]}')
        
        # Show text content
        text = tr.get_text(strip=True)[:200]
        print(f'  Text: {text}')
        print()
