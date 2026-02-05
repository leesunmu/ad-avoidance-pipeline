import requests  # [기초] 웹사이트에 접속해 HTML 코드를 받아오는 '통신사' 역할
from bs4 import BeautifulSoup  # [기초] 받아온 HTML 코드에서 글자만 쏙쏙 뽑아주는 '요리사' 역할
import pandas as pd  # [기초] 데이터를 표(Table)로 만들고 엑셀로 저장하는 '관리자' 역할
from datetime import datetime  # [기초] "언제 수집했니?"를 기록하기 위한 '시계' 역할

# --- [설정 영역] ---
# 변수를 따로 빼두면 나중에 이것만 수정해서 다른 뉴스도 수집할 수 있습니다.
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1463580207397998727/Ds79fM32sYZ4YvYvgTvDoqMi61gPGqBs5b6HZFb2dfaXqjgWk3neZM0jacMsZ8t-1Yqv"
SEARCH_KEYWORD = "인공지능"
NAVER_URL = f"https://search.naver.com/search.naver?query={SEARCH_KEYWORD}"

# [기초] headers는 네이버에게 "저는 로봇이 아니라 사람 브라우저입니다"라고 말하는 신분증입니다.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def run_news_system():
    print(f"📡 [{SEARCH_KEYWORD}] 데이터 수집 파이프라인 가동...")

    # --- 1단계: 추출 (Extract) ---
    # requests.get: 해당 주소로 접속 요청을 보냅니다.
    response = requests.get(NAVER_URL, headers=HEADERS)
    # BeautifulSoup: 복잡한 HTML을 파이썬이 이해하기 쉬운 구조(soup)로 바꿉니다.
    soup = BeautifulSoup(response.text, "html.parser")

    # [중요] find_all("a"): 페이지 내의 모든 '링크(a 태그)'를 일단 다 긁어모읍니다.
    all_links = soup.find_all("a")
    print(f"🔎 분석 대상 링크 개수: {len(all_links)}개")

    # --- 2단계: 변환 및 정제 (Transform) ---
    news_storage = []  # 엑셀용 빈 리스트 (바구니)
    discord_text = f"📢 **[{SEARCH_KEYWORD}] 실시간 주요 뉴스**\n\n" # 디스코드용 텍스트
    
    count = 0
    for link_tag in all_links:
        # .get_text(): <a> 태그 사이에 들어있는 글자(제목)만 가져옵니다.
        title = link_tag.get_text().strip()
        # .get('href'): 링크가 이동할 실제 주소를 가져옵니다.
        link = link_tag.get('href', '')

        # [기초] if 조건문: 진짜 뉴스 기사인지 필터링합니다.
        # 1. 제목이 15자보다 길어야 함 (메뉴 버튼 제외)
        # 2. 주소가 http로 시작해야 함 (정상 링크)
        # 3. naver.com 내부 링크가 아니어야 함 (언론사 사이트 기사 타겟)
        if len(title) > 15 and link.startswith("http") and "naver.com" not in link:
            
            # [중요] 중복 제거: 같은 제목의 기사가 여러 번 들어가지 않게 검사합니다.
            if not any(item['제목'] == title for item in news_storage):
                
                # [기초] 딕셔너리: {키: 값} 형태로 데이터를 예쁘게 포장합니다.
                news_entry = {
                    "수집시간": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "제목": title,
                    "링크": link
                }
                news_storage.append(news_entry) # 바구니에 넣기
                
                # 디스코드에는 상위 5개만 보여줍니다.
                if count < 5:
                    discord_text += f"✅ **{title}**\n🔗 <{link}>\n\n"
                    count += 1

    # --- 3단계: 적재 (Load) ---
    if news_storage:
        # 3-1. 엑셀 저장 (Pandas 이용)
        # DataFrame: 리스트 데이터를 엑셀 시트 모양으로 변환합니다.
        df = pd.DataFrame(news_storage)
        # to_csv: 실제 파일로 저장합니다. utf-8-sig는 한글 깨짐 방지용입니다.
        df.to_csv("daily_news_report.csv", index=False, encoding='utf-8-sig')
        print(f"📁 {len(news_storage)}개의 뉴스를 엑셀로 저장했습니다.")
        
        # 3-2. 디스코드 알림 전송 (Requests 이용)
        # json={}: 디스코드가 이해할 수 있는 데이터 포맷으로 포장해서 보냅니다.
        requests.post(DISCORD_WEBHOOK_URL, json={"content": discord_text})
        print("✅ 디스코드 전송 완료!")
    else:
        print("❌ 유효한 데이터를 찾지 못했습니다.")

# [기초] 이 파일을 직접 실행했을 때만 run_news_system 함수를 작동시키라는 뜻입니다.
if __name__ == "__main__":
    run_news_system()