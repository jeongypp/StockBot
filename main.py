import FinanceDataReader as fdr # 주식 데이터 긁어오는 도구
import requests # 텔레그램에 HTTP 보내는 도구
import pandas as pd # like 엑셀
import time
import os # os 기능 추가

# ==========================================
# 1. 사용자 설정 (여기를 수정하세요!)
# ==========================================
# 아까 적어둔 봇 토큰과 숫자 ID를 따옴표 안에 넣으세요
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 나의 포트폴리오 (종목명: 종목코드)
MY_STOCKS = {
    "SOL 미국테크TOP10": "481190",
    "TIGER 미국S&P500": "360750",
    "TIGER 미국배당다우존스": "458730"
}

# ==========================================
# 2. 텔레그램 봇 기능 함수
# ==========================================
def send_telegram_msg(msg):
    """텔레그램으로 메시지를 보내는 함수"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"전송 실패: {e}")

def get_rsi(prices, period=14):
    """RSI(상대강도지수) 계산 함수""" # 최근 14일동안 상승한 폭과 하락한 폭의 비율을 계산
    delta = prices.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 3. 메인 실행 로직
# ==========================================
print("--- [정엽의 금융 비서] 분석 시작 ---")
alert_messages = []

for name, code in MY_STOCKS.items():
    print(f"🔎 {name} 분석 중...")
    
    # 데이터 가져오기 (2025년부터 현재까지)
    try:
        df = fdr.DataReader(code, '2025')
    except Exception as e:
        print(f"데이터 오류 ({name}): {e}")
        continue

    if df.empty:
        print(f"데이터 없음: {name}")
        continue

    # 지표 계산
    current_price = df['Close'].iloc[-1]
    high_price = df['Close'].max()
    drop_rate = (current_price - high_price) / high_price
    
    # RSI 계산 (데이터가 15일 이상 있어야 계산 가능)
    rsi = 50 # 기본값
    if len(df) > 15:
        rsi = get_rsi(df['Close']).iloc[-1]

    # 로그 출력 (PC 화면용)
    print(f"   ㄴ 현재가: {current_price:,.0f}원 / 하락률: {drop_rate*100:.2f}% / RSI: {rsi:.1f}")

    # [매수 신호 판단] 3단계
    msg = ""
    if drop_rate <= -0.20 or rsi < 30:
        msg = f"🚨 [긴급] {name} 폭락! 인생 기회! (-20%↓)\n👉 평소 3배(30만원) 매수 추천"
    elif drop_rate <= -0.10:
        msg = f"⚠️ [주의] {name} 조정장 진입 (-10%↓)\n👉 평소 2배(20만원) 매수 추천"
    elif drop_rate <= -0.05:
        msg = f"👀 [관심] {name} 세일 시작 (-5%↓)\n👉 평소 1.5배(15만원) 매수 추천"
    
    # 테스트용: 하락률이 0% 이하라면 무조건 알림 보내보기 (테스트 끝나면 주석 처리)
    # if drop_rate <= 0.0: 
    #    msg = f"🧪 [테스트] {name} 현재가 {current_price:,.0f}원 (정상 작동 중)"

    if msg:
        alert_messages.append(msg)
    time.sleep(1) # 차단 방지를 위해 1초 쉬기

# 알림 보낼 게 있으면 텔레그램 전송
if alert_messages:
    final_report = "📢 [투자 알림] 매수 신호가 포착되었습니다!\n\n" + "\n\n".join(alert_messages)
    send_telegram_msg(final_report)
    print(">>> 텔레그램 전송 완료")
else:
    # 매수 신호가 없을 때도 '생존 신고' 받기
    send_telegram_msg("✅ 특이사항 없음. 정엽님의 자산은 안전합니다.")
    print(">>> 특이사항 없음 (전송 생략)")