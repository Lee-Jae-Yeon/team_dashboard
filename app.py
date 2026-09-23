import pandas as pd
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="부산항 노선별 항만물류지표 분석 대시보드",
    page_icon='📊',
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent

# 데이터 로드
DATA_PATH1 = BASE_DIR / 'data' / 'data.csv'
DATA_PATH2 = BASE_DIR / 'data' / 'data3.csv'

kpli_df = pd.read_csv(DATA_PATH1, encoding='utf-8')
volume_df = pd.read_csv(DATA_PATH2, encoding='cp949')

# KPI 화면 표시용 도착항명
KPI_ROUTE_COL = '도착항명_표시'
kpli_df[KPI_ROUTE_COL] = kpli_df['도착항명(DEST_PORT_NAME)'].replace({
    'KOBC PORT&LOGISTICS INDICATOR (종합)': '종합'
})

# 지역별 그룹핑
region_map = {
    '상하이항': '극동아시아 지역',
    '칭다오항': '극동아시아 지역',
    '홍콩항': '극동아시아 지역',

    '싱가포르항': '동남아시아 지역',
    '램차방항': '동남아시아 지역',
    '호치민항': '동남아시아 지역',

    '로스앤젤레스항': '북미주 지역',
    '뉴욕항': '북미주 지역',

    '함부르크항': '유럽 지역',
    '로테르담항': '유럽 지역',
    '안트베르펜항': '유럽 지역',

    '제벨알리항': '중동 지역',

    'KOBC PORT&LOGISTICS INDICATOR (종합)': '종합'
}

kpli_df['지역'] = kpli_df['도착항명(DEST_PORT_NAME)'].map(region_map)

# 날짜 형식 변환
kpli_df['기준일자(DATE)'] = pd.to_datetime(kpli_df['기준일자(DATE)'])

# 연월 컬럼 만들기
kpli_df['연월'] = kpli_df['기준일자(DATE)'].dt.strftime('%Y년 %m월')

regional_efficiency = kpli_df.groupby(['지역','연월'])['항만효율성(PORT_EFFICIENCY)'].mean().round(2).reset_index()

# 2025년 5월 데이터 제외
regional_efficiency = regional_efficiency[regional_efficiency['연월'] != '2025년 05월']

regional_efficiency = regional_efficiency[regional_efficiency['지역'] != '종합']

volume_long = volume_df.melt(
    id_vars='지역',
    var_name='연월',
    value_name='물동량'
)

regional_analysis_df = pd.merge(
    regional_efficiency,
    volume_long,
    on=['지역', '연월'],
    how='left'
)

def region_graph(region):

    if region == '종합':
        temp = regional_analysis_df.copy()
    else:
        temp = regional_analysis_df[regional_analysis_df['지역'] == region]

    fig = make_subplots(
        specs=[[{'secondary_y': True}]]
    )

    color_map = {
        '극동아시아 지역': '#2563EB',
        '동남아시아 지역': '#14B8A6',
        '북미주 지역': '#F59E0B',
        '유럽 지역': '#8B5CF6',
        '중동 지역': '#EF4444'
    }

    # 지역별 물동량
    for r in temp['지역'].unique():

        region_temp = temp[temp['지역'] == r]

        fig.add_trace(
            go.Bar(
                x=region_temp['연월'],
                y=region_temp['물동량'],
                name=f'{r} 물동량',
                marker_color=color_map.get(r, '#64748B'),
                opacity=0.8,
                legendgroup=r
            ),
            secondary_y=False
        )

    # 지역별 항만효율성
    for r in temp['지역'].unique():

        region_temp = temp[temp['지역'] == r]

        fig.add_trace(
            go.Scatter(
                x=region_temp['연월'],
                y=region_temp['항만효율성(PORT_EFFICIENCY)'],
                mode='lines+markers',
                name=f'{r} 항만효율성',
                line=dict(
                    color=color_map.get(r, '#64748B'),
                    width=3
                ),
                marker=dict(size=7),
                legendgroup=r
            ),
            secondary_y=True
        )

    fig.update_layout(
        height=700,
        barmode='group',

        plot_bgcolor='white',
        paper_bgcolor='white',

        font=dict(
            size=13,
            color='#334155'
        ),
        title= f'{region} 물동량 및 항만효율성',
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02
        ),
        margin=dict(
            l=40,
            r=250,
            t=70,
            b=40
        )
    )

    fig.update_xaxes(
        title_text='연월',
        showgrid=False,
        linecolor='#CBD5E1'
    )

    fig.update_yaxes(
        title_text='물동량',
        gridcolor='#E2E8F0',
        zeroline=False,
        secondary_y=False
    )

    fig.update_yaxes(
        title_text='항만효율성',
        showgrid=False,
        zeroline=False,
        secondary_y=True
    )

    return fig


# 지역 목록 만들기
region_list = ['종합'] + sorted(
    regional_analysis_df['지역'].dropna().unique()
)


kpi_df = kpli_df.copy()


kpi_df['기준일자(DATE)'] = pd.to_datetime(
    kpi_df['기준일자(DATE)']
)

kpi_df['연월'] = (
    kpi_df['기준일자(DATE)']
    .dt.to_period('M')
    .astype(str)
)


route_kpi_df = kpi_df.groupby(KPI_ROUTE_COL).agg(
    대기시간=('대기시간(WAITING_TIME)', 'mean'),
    정시성=('항만정시성(ON_TIME_PERFORMANCE)', 'mean'),
    항만효율성=('항만효율성(PORT_EFFICIENCY)', 'mean')
)


# ==================================================

port_mean = kpi_df['항만효율성(PORT_EFFICIENCY)'].mean()

waiting_mean = kpi_df['대기시간(WAITING_TIME)'].mean()

on_time_mean = kpi_df['항만정시성(ON_TIME_PERFORMANCE)'].mean()

# 총항해시간 이상치 분석용 데이터
route_df = kpli_df.copy()

route_df['기준일자(DATE)'] = pd.to_datetime(
    route_df['기준일자(DATE)']
)

# 총항해시간 이상치는 노선별 분석이므로 종합 제외
sailing_route_df = route_df[
    route_df['도착항명(DEST_PORT_NAME)']
    != 'KOBC PORT&LOGISTICS INDICATOR (종합)'
].copy()


# 조회 조건
with st.sidebar:
    st.header('조회 조건')

    st.subheader('지역별 분석')
    selected_region = st.selectbox(
        '지역',
        region_list,
        key='region'
    )

    st.divider()

    st.subheader('노선별 KPI')
    selected_kpi_route = st.selectbox(
        '도착항',
        route_kpi_df.index.tolist(),
        key='kpi_route'
    )

    selected_month_range = st.slider(
        '월 범위',
        min_value=1,
        max_value=12,
        value=(1, 12),
        key='kpi_month'
    )

    st.divider()

    st.subheader('총항해시간 이상치')
    selected_sailing_route = st.selectbox(
        '도착항',
        sailing_route_df['도착항명(DEST_PORT_NAME)'].unique(),
        key='sailing_route'
    )


selected_port_efficiency = route_kpi_df.loc[
    selected_kpi_route,
    '항만효율성'
]

selected_waiting_time = route_kpi_df.loc[
    selected_kpi_route,
    '대기시간'
]

selected_on_time_performance = route_kpi_df.loc[
    selected_kpi_route,
    '정시성'
]

# 대시보드 상단
st.title('부산항 항만물류지표 분석 대시보드')

st.caption(
    '부산항에서 출발하는 주요 컨테이너선 노선의 종합 물류 지표 KPI, 노선별 KPI 및 총항해시간 이상치, 지역별 항만 효율성을 분석합니다.  \n'
    'Data: 부산항만공사_외내항컨테이너통합집계정보, 2024년'
)

# 기존 전체 평균 계산값을 종합 KPI로 표시
st.write("")
st.header('종합 KPI')
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        '항만효율성',
        value=f'{port_mean:.2f}',
        border=True,
        height=120
    )

with col2:
    st.metric(
        '대기시간',
        value=f'{waiting_mean:.2f}',
        border=True,
        height=120
    )

with col3:
    st.metric(
        '정시성',
        value=f'{on_time_mean:.2f}',
        border=True,
        height=120
    )


# 지역별 분석
st.divider()
st.header('지역별 분석')

st.plotly_chart(
    region_graph(selected_region),
    use_container_width=True
)

st.subheader('📌 주요 분석 결과')
st.markdown(
    '극동아시아는 물동량이 가장 많지만 항만효율성은 상대적으로 낮았으며, 유럽은 물동량이 적음에도 높은 항만효율성을 보였다.   \n 전체적으로 물동량과 항만효율성이 반드시 비례하지 않으며, 지역별로 서로 다른 흐름이 나타났다.'
)

# 노선별 KPI 분석
st.divider()
st.header('노선별 KPI 분석')

st.subheader(f'{selected_kpi_route} KPI')

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        '항만효율성',
        value=f'{selected_port_efficiency:.2f}',
        border=True,
        height=120
    )

with col2:
    st.metric(
        '대기시간',
        value=f'{selected_waiting_time:.2f}',
        border=True,
        height=120
    )

with col3:
    st.metric(
        '정시성',
        value=f'{selected_on_time_performance:.2f}',
        border=True,
        height=120
    )

st.subheader('월별 KPI')


# 선택한 노선
monthly_kpi_df = kpi_df[
    kpi_df[KPI_ROUTE_COL] == selected_kpi_route
].copy()


# 선택한 월 범위
monthly_kpi_df['월'] = (
    monthly_kpi_df['기준일자(DATE)'].dt.month
)

monthly_kpi_df = monthly_kpi_df[
    monthly_kpi_df['월'].between(
        selected_month_range[0],
        selected_month_range[1]
    )
]

monthly_port = (
    monthly_kpi_df
    .groupby('연월')['항만효율성(PORT_EFFICIENCY)']
    .mean()
    .reset_index()
)

monthly_waiting = (
    monthly_kpi_df
    .groupby('연월')['대기시간(WAITING_TIME)']
    .mean()
    .reset_index()
)

monthly_on_time = (
    monthly_kpi_df
    .groupby('연월')['항만정시성(ON_TIME_PERFORMANCE)']
    .mean()
    .reset_index()
)

col1, col2, col3 = st.columns(3)


with col1:

    fig_port = px.line(
        monthly_port,
        x='연월',
        y='항만효율성(PORT_EFFICIENCY)',
        markers=True,
        title='항만효율성'
    )

    fig_port.update_layout(
        xaxis_title='월',
        yaxis_title='항만효율성'
    )

    st.plotly_chart(
        fig_port,
        width='stretch'
    )


with col2:

    fig_waiting = px.line(
        monthly_waiting,
        x='연월',
        y='대기시간(WAITING_TIME)',
        markers=True,
        title='대기시간'
    )

    fig_waiting.update_layout(
        xaxis_title='월',
        yaxis_title='대기시간'
    )

    st.plotly_chart(
        fig_waiting,
        width='stretch'
    )


with col3:

    fig_on_time = px.line(
        monthly_on_time,
        x='연월',
        y='항만정시성(ON_TIME_PERFORMANCE)',
        markers=True,
        title='정시성'
    )

    fig_on_time.update_layout(
        xaxis_title='월',
        yaxis_title='정시성'
    )

    st.plotly_chart(
        fig_on_time,
        width='stretch'
    )


selected_route = sailing_route_df[
    sailing_route_df['도착항명(DEST_PORT_NAME)'] == selected_sailing_route
]

st.divider()
st.header('노선별 총항해시간 이상치 분석')
st.write("")
st.subheader('전체 노선 총항해시간 분포')


fig1 = px.box(
    sailing_route_df,
    x='도착항명(DEST_PORT_NAME)',
    y='총항해시간(TOTAL_SAILING_TIME)',
    points='outliers'
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

col = '총항해시간(TOTAL_SAILING_TIME)'

q1 = selected_route[col].quantile(0.25)
q3 = selected_route[col].quantile(0.75)

iqr = q3 - q1

lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr


sailing_outliers = selected_route[
    (selected_route[col] < lower) |
    (selected_route[col] > upper)
].copy()

st.subheader(f'{selected_sailing_route} 항해시간 상세정보')

mean_sailing_time = selected_route[
    '총항해시간(TOTAL_SAILING_TIME)'
].mean()

col1, col2, col3 = st.columns(3)

col1.metric(
    '평균 총항해시간',
    f'{mean_sailing_time:.2f}',
    border=True,
    height=120
)

col2.metric(
    '전체 항해 건수',
    len(selected_route),
    border=True,
    height=120
)

col3.metric(
    '이상치 건수',
    len(sailing_outliers),
    border=True,
    height=120
)

fig_detail_box = px.box(
    selected_route,
    y='총항해시간(TOTAL_SAILING_TIME)',
    points='all',
    hover_data=[
        '기준일자(DATE)',
        '도착항코드(DEST_PORT_CODE)'
    ],
    labels={
        '총항해시간(TOTAL_SAILING_TIME)': '총항해시간',
        '기준일자(DATE)': '기준일자',
        '도착항코드(DEST_PORT_CODE)': '도착항코드'
    },
    height=400
)

st.plotly_chart(
    fig_detail_box,
    use_container_width=True
)


# 총항해시간
fig2 = px.line(
    selected_route,
    x='기준일자(DATE)',
    y='총항해시간(TOTAL_SAILING_TIME)',
    markers=True,
    title='날짜별 총항해시간'
)


# 이상치 빨간 점
fig2.add_scatter(
    x=sailing_outliers['기준일자(DATE)'],
    y=sailing_outliers['총항해시간(TOTAL_SAILING_TIME)'],
    mode='markers',
    marker=dict(
        color='red',
        size=12
    ),
    name='이상치'
)


st.plotly_chart(
    fig2,
    use_container_width=True
)

