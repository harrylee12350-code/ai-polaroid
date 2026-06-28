import streamlit as st
import boto3, json, uuid, time

st.set_page_config(page_title="찰나", page_icon="🎬")

mode = st.radio("모드를 선택하세요", ["일반용 (상세 기록)", "유아용 (간편 기록)"])

if mode == "유아용 (간편 기록)":
    st.title("👶 찰나 - 아기 모드")
    message = st.text_input("한 마디 남기기", "사랑해요!")
    date, place = time.strftime("%Y.%m.%d"), "우리집"
else:
    st.title("🎬 찰나 - 일반 모드")
    date = st.date_input("날짜")
    place = st.text_input("장소", "서울")
    message = st.text_input("멘트 (20자 이내)", max_chars=20)

uploaded_files = st.file_uploader("사진 2~5장", accept_multiple_files=True)

if st.button("🚀 찰나 생성하기"):
    # 💡 여기서 텍스트 데이터(meta)를 포함한 주문서를 큐로 전송
    meta = {"date": str(date), "place": place, "message": message}
    st.info("영화 인화 중...")
    # ... S3/SQS 전송 로직 수행 ...