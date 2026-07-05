import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator

st.set_page_config(page_title="StockPulse: 기업 정밀 분석기", layout="wide")

# 번역 함수 (안정적인 라이브러리 사용)
def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='ko').translate(text[:1000])
    except:
        return text

st.title("🔍 StockPulse : 기업 정밀 분석기")
ticker = st.text_input("기업 티커를 입력하세요 (예: TSLA, AAPL, NVDA)").upper()

if ticker:
    try:
        # 0. 실시간 환율
        usd_krw_ticker = yf.Ticker("USDKRW=X")
        usd_krw = usd_krw_ticker.info.get('regularMarketPrice', 1330)
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 1. 기업 개요
        company_name = info.get('longName', '정보 없음')
        st.header(f"{company_name} ({ticker})")
        st.caption(f"💵 적용 환율: 1 USD = {usd_krw:.1f} KRW") # 환율 표시 추가
        
        raw_summary = info.get('longBusinessSummary', '정보 없음')
        st.write(translate_text(raw_summary))
        st.divider()
        
        # 2. 핵심 지표
        market_cap_krw = (info.get('marketCap', 0) / 1e12) * usd_krw 
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("시가총액", f"약 {market_cap_krw:.1f} 조원")
        col2.metric("PER", info.get('forwardPE', 'N/A'))
        col3.metric("영업이익률", f"{info.get('operatingMargins', 0)*100:.1f}%")
        col4.metric("배당수익률", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "없음")
        st.info("💡 **PER이란?** 현재 주가가 1주당 이익의 몇 배인가를 나타냅니다. (낮을수록 저평가, 높을수록 성장 기대감)")

        # 3. 상세 재무 테이블
        st.subheader("📊 상세 재무 분석")
        total_rev_krw = (info.get('totalRevenue', 0) / 1e12) * usd_krw
        cash = (info.get('totalCash', 0) / 1e12) * usd_krw
        
        details = {
            "주당순이익 (EPS)": [f"{info.get('trailingEps', 0):.2f} USD", "1주당 순이익"],
            "총 매출액": [f"약 {total_rev_krw:.1f} 조 원", "최근 1년 매출"],
            "보유 현금": [f"약 {cash:.1f} 조 원", "현금성 자산"],
            "부채비율": [f"{info.get('debtToEquity', 'N/A')}", "자기자본 대비 부채"],
            "52주 최고/최저": [f"{info.get('fiftyTwoWeekHigh')} / {info.get('fiftyTwoWeekLow')} USD", "최근 1년 변동폭"]
        }
        st.table(pd.DataFrame(details, index=['값', '해설']).T)

        # 4. 실적 시각화
        st.subheader("📈 최근 8분기 실적 추이")
        fin = stock.quarterly_financials
        if fin is not None and not fin.empty:
            fin = fin.iloc[:, ::-1] 
            fin_krw = (fin / 1e12) * usd_krw
            
            chart_data = fin_krw.loc[['Total Revenue', 'Net Income']].T
            chart_data.columns = ['총 매출', '순이익']
            chart_data['순이익률(%)'] = (chart_data['순이익'] / chart_data['총 매출']) * 100
            
            st.bar_chart(chart_data[['총 매출', '순이익']])
            
            st.write("분기별 상세 수치 (조 원 및 순이익률 %):")
            # 에러 방지를 위해 단순 숫자로 표기
            st.table(chart_data.T.round(2))
        
        # 5. 주요 재무 항목
        st.subheader("🏢 주요 재무 항목 (최근 공시 기준)")
        mapping = {
            'Operating Revenue': '영업 매출', 'Net Income': '순이익', 
            'Gross Profit': '매출 총이익', 'Total Revenue': '총 매출'
        }
        if fin is not None:
            fin_renamed = fin_krw.rename(index=mapping)
            # map 사용 (applymap은 최신 버전에서 삭제됨)
            st.dataframe(fin_renamed.iloc[:, -4:].map(lambda x: f"{x:.2f} 조"))

        # 6. 다음 실적 발표일
        calendar = stock.calendar
        next_date = calendar.get('Earnings Date', ['정보 없음'])[0] if calendar is not None else '정보 없음'
        if isinstance(next_date, datetime): next_date = next_date.strftime('%Y-%m-%d')
        st.success(f"📅 **다음 실적 발표 예상일**: {next_date}")
            
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
