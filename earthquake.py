import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. 페이지 레이아웃 및 탭 제목 설정
st.set_page_config(
    page_title="세계 지진 위험도 분석 시스템",
    layout="wide"
)

# 2. 데이터 로드 함수 (캐싱 적용으로 페이지 새로고침 시 속도 저하 방지)
@st.cache_data
def load_data():
    df = pd.read_csv("earthquake.csv")
    # 딕셔너리 키(Key) 매핑 에러 방지를 위해 cluster 타입을 정수형으로 강제 변환
    df['cluster'] = df['cluster'].astype(int)
    return df

try:
    df_new = load_data()
except FileNotFoundError:
    st.error("데이터 파일('earthquake.csv')을 찾을 수 없습니다. 'earthquake.py'와 같은 폴더에 위치해 있는지 확인해 주세요.")
    st.stop()

# 3. K=3 기준 사전(Dictionary) 정의
risk_dict = {0: '높음', 1: '낮음', 2: '중간'}
colors = {0: 'red', 1: 'blue', 2: 'green'}

# 4. UI 및 상단 타이틀
st.title("🌍 세계 지진 위험도 분석 시스템")
st.write("위도와 경도를 입력하면 주변 지진 데이터를 기반으로 위험도를 예측하고 지도에 시각화합니다.")

# 화면을 좌우로 분할 (좌측: 입력창 / 우측: 결과창 및 지도)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📍 분석 위치 입력")
    lat = st.number_input("위도 입력", value=37.5, min_value=-90.0, max_value=90.0, step=0.1)
    lon = st.number_input("경도 입력", value=127.0, min_value=-180.0, max_value=180.0, step=0.1)
    
    # 버튼 너비를 사이드 바 크기에 맞춤
    analyze_btn = st.button("🚀 위험도 분석 시작", use_container_width=True)

with col2:
    if analyze_btn:
        # 5. 주변 지진 필터링 (사용자 입력 기준 위경도 각 ±5도 범위)
        near_df = df_new[
            (df_new['위도'] >= lat - 5) &
            (df_new['위도'] <= lat + 5) &
            (df_new['경도'] >= lon - 5) &
            (df_new['경도'] <= lon + 5)
        ]

        # 주변 데이터가 비어있을 때의 예외 처리
        if len(near_df) == 0:
            st.warning("입력하신 좌표 주변 5도 이내에 기록된 과거 지진 데이터가 없습니다.")
        else:
            # 군집 빈도 비율 계산 후 가장 높은 비율의 군집 추출
            cluster_ratio = near_df['cluster'].value_counts(normalize=True)
            main_cluster = int(cluster_ratio.idxmax())

            # 위험도 분석 결과 띄우기
            st.success(f"### 📊 예상 위험도 결과: **{risk_dict[main_cluster]}**")

            # 6. Folium 지도 초기화 (사용자가 입력한 위경도 중심)
            m = folium.Map(location=[lat, lon], zoom_start=4, tiles="CartoDB positron")

            # 7. 과거 데이터 샘플링 (★요청하신 대로 5,000개에서 500개로 축소★)
            df_sample = df_new.sample(n=min(500, len(df_new)), random_state=42)

            # 8. 지도에 샘플링된 지진 점 찍기 (속도가 훨씬 빨라집니다)
            for i in range(len(df_sample)):
                cluster = df_sample.iloc[i]['cluster']
                marker_color = colors.get(cluster, 'gray')

                folium.CircleMarker(
                    location=[df_sample.iloc[i]['위도'], df_sample.iloc[i]['경도']],
                    radius=3, 
                    color=marker_color,
                    fill=True, 
                    fill_color=marker_color,
                    fill_opacity=0.6
                ).add_to(m)

            # 9. 사용자가 입력한 현재 타겟 위치에 검은색 별(Star) 마커 찍기
            folium.Marker(
                location=[lat, lon],
                popup="분석 요청 위치",
                icon=folium.Icon(color='black', icon='star')
            ).add_to(m)

            # 10. 스트림릿 컴포넌트로 화면에 지도 출력
            st_folium(m, width=800, height=500, returned_objects=[])
    else:
        st.info("← 왼쪽 입력창에서 분석을 원하는 좌표를 지정한 후 버튼을 클릭해 주세요.")
