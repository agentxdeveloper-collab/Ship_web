import requests
from bs4 import BeautifulSoup

def fetch_sea_temp_content():
    """바다타임에서 수온 정보의 middle-container 내부 content 영역만 가져오기"""
    url = "https://www.badatime.com/443/sea-temp"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # middle-container 찾기
        middle_container = soup.select_one('.middle-container')
        if middle_container:
            # content 영역 찾기
            content = middle_container.select_one('.content')
            if content:
                print("=== Content 영역 ===")
                print(content.prettify())
                return content
            else:
                print("Content 영역을 찾을 수 없습니다.")
                print("\n=== Middle Container 구조 ===")
                print(middle_container.prettify()[:1000])  # 처음 1000자만 출력
        else:
            print("Middle-container를 찾을 수 없습니다.")
            print("\n=== 페이지 구조 확인 (body 일부) ===")
            body = soup.find('body')
            if body:
                print(str(body)[:1000])  # 처음 1000자만 출력
        
        return None
        
    except requests.RequestException as e:
        print(f"요청 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    fetch_sea_temp_content()
