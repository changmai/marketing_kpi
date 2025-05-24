import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
from datetime import datetime
import xlsxwriter

# 페이지 설정
st.set_page_config(
    page_title="광고 수익성 대시보드",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화
if 'history' not in st.session_state:
    st.session_state.history = []

# CSS 스타일
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }
    .warning {
        color: #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.title("💰 광고 수익성 동적 대시보드")


# 숫자 포맷 함수
def format_number(num):
    return f"{num:,.0f}"


def format_currency(num):
    return f"₩{num:,.0f}"


# 계산 함수
def calculate_metrics(cvr, ctr, budget, aov, cpc, cost_rate):
    cvr_decimal = cvr / 100
    ctr_decimal = ctr / 100
    cost_rate_decimal = cost_rate / 100

    # 기본 계산
    clicks = budget / cpc
    impressions = clicks / ctr_decimal
    conversions = clicks * cvr_decimal
    revenue = conversions * aov
    actual_roas = revenue / budget

    # 비용 지표
    cpa = budget / conversions if conversions > 0 else 0
    cpm = (budget / impressions) * 1000 if impressions > 0 else 0

    # 수익성 계산
    cogs = revenue * cost_rate_decimal
    gross_profit = revenue - cogs
    gross_margin = (gross_profit / revenue) * 100 if revenue > 0 else 0
    net_profit = gross_profit - budget
    net_margin = (net_profit / revenue) * 100 if revenue > 0 else 0
    roi = (net_profit / budget) * 100

    # 손익분기점
    breakeven_roas = 1 / (1 - cost_rate_decimal)
    safety_margin = ((actual_roas - breakeven_roas) / breakeven_roas) * 100

    return {
        'revenue': revenue,
        'actual_roas': actual_roas,
        'conversions': conversions,
        'clicks': clicks,
        'impressions': impressions,
        'cpa': cpa,
        'cpm': cpm,
        'gross_profit': gross_profit,
        'gross_margin': gross_margin,
        'net_profit': net_profit,
        'net_margin': net_margin,
        'roi': roi,
        'breakeven_roas': breakeven_roas,
        'safety_margin': safety_margin,
        'cogs': cogs
    }


# 입력 컨트롤 - 2열 배치
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 성과 지표 조정")

    col_a, col_b = st.columns([4, 1])
    with col_a:
        cvr = st.slider("CVR (%)", 0.1, 10.0, 2.0, 0.1, label_visibility="visible")
    with col_b:
        st.markdown(
            f"<div style='text-align: center; padding-top: 25px; font-weight: bold; color: #2196f3;'>{cvr}%</div>",
            unsafe_allow_html=True)

    col_a, col_b = st.columns([4, 1])
    with col_a:
        ctr = st.slider("CTR (%)", 0.1, 10.0, 1.5, 0.1, label_visibility="visible")
    with col_b:
        st.markdown(
            f"<div style='text-align: center; padding-top: 25px; font-weight: bold; color: #2196f3;'>{ctr}%</div>",
            unsafe_allow_html=True)

    col_a, col_b = st.columns([4, 1])
    with col_a:
        cost_rate = st.slider("원가율 (%)", 10, 90, 30, 1, label_visibility="visible")
    with col_b:
        st.markdown(
            f"<div style='text-align: center; padding-top: 25px; font-weight: bold; color: #2196f3;'>{cost_rate}%</div>",
            unsafe_allow_html=True)

with col2:
    st.subheader("💵 비용 지표 조정")

    col_a, col_b = st.columns([4, 1])
    with col_a:
        budget = st.slider("예산 (원)", 1_000_000, 20_000_000, 5_000_000, 100_000, label_visibility="visible")
    with col_b:
        st.markdown(
            f"<div style='text-align: center; padding-top: 25px; font-weight: bold; color: #2196f3;'>{format_currency(budget)}</div>",
            unsafe_allow_html=True)

    col_a, col_b = st.columns([4, 1])
    with col_a:
        aov = st.slider("객단가 (원)", 10_000, 1_000_000, 150_000, 1_000, label_visibility="visible")
    with col_b:
        st.markdown(
            f"<div style='text-align: center; padding-top: 25px; font-weight: bold; color: #2196f3;'>{format_currency(aov)}</div>",
            unsafe_allow_html=True)

    col_a, col_b = st.columns([4, 1])
    with col_a:
        cpc = st.slider("CPC (원)", 100, 5_000, 1_000, 10, label_visibility="visible")
    with col_b:
        st.markdown(
            f"<div style='text-align: center; padding-top: 25px; font-weight: bold; color: #2196f3;'>{format_currency(cpc)}</div>",
            unsafe_allow_html=True)

# 메트릭 계산
metrics = calculate_metrics(cvr, ctr, budget, aov, cpc, cost_rate)

# 시나리오 저장 버튼
st.markdown("---")
col_save, col_download, col_clear = st.columns([1, 1, 4])

with col_save:
    if st.button("💾 시나리오 저장", type="primary"):
        scenario = {
            '저장시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'CVR (%)': cvr,
            'CTR (%)': ctr,
            '예산': budget,
            '객단가': aov,
            'CPC': cpc,
            '원가율 (%)': cost_rate,
            '매출': metrics['revenue'],
            '순이익': metrics['net_profit'],
            'ROAS': metrics['actual_roas'],
            'ROI (%)': metrics['roi']
        }
        st.session_state.history.append(scenario)
        st.success("시나리오가 저장되었습니다!")

with col_download:
    if st.button("📥 엑셀 다운로드"):
        if st.session_state.history:
            # 현재 상태 데이터
            current_data = {
                '구분': ['현재 설정'],
                'CVR (%)': [cvr],
                'CTR (%)': [ctr],
                '예산': [budget],
                '객단가': [aov],
                'CPC': [cpc],
                '원가율 (%)': [cost_rate],
                '매출': [metrics['revenue']],
                '순이익': [metrics['net_profit']],
                'ROAS': [metrics['actual_roas']],
                'ROI (%)': [metrics['roi']]
            }

            # CVR별 분석 데이터
            cvr_analysis = []
            for test_cvr in np.arange(0.5, 5.5, 0.5):
                test_metrics = calculate_metrics(test_cvr, ctr, budget, aov, cpc, cost_rate)
                cvr_analysis.append({
                    'CVR (%)': test_cvr,
                    '매출': test_metrics['revenue'],
                    '순이익': test_metrics['net_profit'],
                    'ROAS': test_metrics['actual_roas'],
                    '상태': '흑자' if test_metrics['net_profit'] >= 0 else '적자'
                })

            # CPC별 분석 데이터
            cpc_analysis = []
            for test_cpc in range(500, 3250, 250):
                test_metrics = calculate_metrics(cvr, ctr, budget, aov, test_cpc, cost_rate)
                cpc_analysis.append({
                    'CPC': test_cpc,
                    '클릭수': test_metrics['clicks'],
                    '전환수': test_metrics['conversions'],
                    '순이익': test_metrics['net_profit'],
                    '상태': '흑자' if test_metrics['net_profit'] >= 0 else '적자'
                })

            # 엑셀 파일 생성
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # 현재 설정
                pd.DataFrame(current_data).to_excel(writer, sheet_name='현재설정', index=False)

                # 저장된 시나리오
                if st.session_state.history:
                    pd.DataFrame(st.session_state.history).to_excel(writer, sheet_name='저장된시나리오', index=False)

                # CVR 분석
                pd.DataFrame(cvr_analysis).to_excel(writer, sheet_name='CVR분석', index=False)

                # CPC 분석
                pd.DataFrame(cpc_analysis).to_excel(writer, sheet_name='CPC분석', index=False)

                # 포맷 적용
                workbook = writer.book
                money_format = workbook.add_format({'num_format': '#,##0'})
                percent_format = workbook.add_format({'num_format': '0.0%'})

                # 각 시트에 포맷 적용
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    worksheet.set_column('D:H', 15, money_format)

            st.download_button(
                label="💾 다운로드",
                data=buffer,
                file_name=f"광고분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.warning("저장된 시나리오가 없습니다.")

with col_clear:
    if st.button("🗑️ 기록 초기화"):
        st.session_state.history = []
        st.success("저장된 시나리오가 모두 삭제되었습니다.")

# 메인 스코어 카드
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    color = "positive" if metrics['actual_roas'] >= metrics['breakeven_roas'] else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">실제 ROAS</div>
        <div class="metric-value {color}">{metrics['actual_roas']:.2f}x</div>
        <div class="metric-label">손익분기: {metrics['breakeven_roas']:.2f}x</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    color = "positive" if metrics['net_profit'] >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">순이익</div>
        <div class="metric-value {color}">{format_currency(metrics['net_profit'])}</div>
        <div class="metric-label">이익률: {metrics['net_margin']:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "positive" if metrics['roi'] >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ROI</div>
        <div class="metric-value {color}">{metrics['roi']:.0f}%</div>
        <div class="metric-label">CPA: {format_currency(metrics['cpa'])}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if metrics['safety_margin'] >= 20:
        color = "positive"
        status = "안전"
    elif metrics['safety_margin'] >= 0:
        color = "warning"
        status = "주의"
    else:
        color = "negative"
        status = "위험"

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">안전마진</div>
        <div class="metric-value {color}">{metrics['safety_margin']:.0f}%</div>
        <div class="metric-label">{status}</div>
    </div>
    """, unsafe_allow_html=True)

# 알림 메시지
st.markdown("---")
if metrics['net_profit'] < 0:
    st.error(
        f"⚠️ 손실 발생! CVR을 높이거나 CPC를 낮추세요. (실제 ROAS: {metrics['actual_roas']:.2f}x, 필요: {metrics['breakeven_roas']:.2f}x)")
elif metrics['safety_margin'] < 20:
    st.warning("⚡ 안전마진 부족! 시장 변동에 취약합니다.")
else:
    st.success("✅ 안전한 수익 구조입니다!")

# 손익분기점 분석 테이블
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 CVR별 손익분기점 분석")

    cvr_data = []
    for test_cvr in np.arange(0.5, 5.5, 0.5):
        test_metrics = calculate_metrics(test_cvr, ctr, budget, aov, cpc, cost_rate)
        cvr_data.append({
            'CVR (%)': f"{test_cvr:.1f}",
            '매출': format_currency(test_metrics['revenue']),
            '순이익': format_currency(test_metrics['net_profit']),
            'ROAS': f"{test_metrics['actual_roas']:.2f}x",
            '상태': '흑자' if test_metrics['net_profit'] >= 0 else '적자'
        })

    cvr_df = pd.DataFrame(cvr_data)


    # 스타일 함수 정의
    def style_cvr_table(df):
        def apply_styles(row):
            # CVR 값들을 float로 변환
            row_cvr = float(row['CVR (%)'])
            cvr_values = [float(r['CVR (%)']) for r in cvr_data]

            # 현재 CVR과 가장 가까운 두 값 찾기
            differences = [(abs(v - cvr), v) for v in cvr_values]
            differences.sort()
            closest_values = [differences[0][1]]
            if len(differences) > 1:
                closest_values.append(differences[1][1])

            # 배경색 설정
            if row_cvr in closest_values:
                bg_color = 'background-color: #e0f2fe;'
            else:
                bg_color = ''

            # 순이익 값 추출 (숫자만)
            profit_str = row['순이익'].replace('₩', '').replace(',', '')
            profit_value = float(profit_str) if profit_str.replace('-', '').isdigit() else 0

            # 순이익에 따른 색상
            if profit_value >= 0:
                profit_color = 'color: #155724; font-weight: bold;'
            else:
                profit_color = 'color: #721c24; font-weight: bold;'

            # 상태에 따른 색상
            if row['상태'] == '흑자':
                status_color = 'background-color: #d4edda; color: #155724; font-weight: bold;'
            else:
                status_color = 'background-color: #f8d7da; color: #721c24; font-weight: bold;'

            # 각 컬럼별 스타일 적용
            styles = [
                bg_color,  # CVR (%)
                bg_color,  # 매출
                bg_color + profit_color,  # 순이익
                bg_color,  # ROAS
                bg_color + status_color if bg_color else status_color  # 상태
            ]

            return styles

        return df.style.apply(apply_styles, axis=1)


    st.dataframe(
        style_cvr_table(cvr_df),
        hide_index=True,
        use_container_width=True
    )

with col2:
    st.subheader("💰 CPC별 손익분기점 분석")

    cpc_data = []
    for test_cpc in range(500, 3250, 250):
        test_metrics = calculate_metrics(cvr, ctr, budget, aov, test_cpc, cost_rate)
        cpc_data.append({
            'CPC': format_currency(test_cpc),
            '클릭': format_number(test_metrics['clicks']),
            '전환': format_number(test_metrics['conversions']),
            '순이익': format_currency(test_metrics['net_profit']),
            '상태': '흑자' if test_metrics['net_profit'] >= 0 else '적자'
        })

    cpc_df = pd.DataFrame(cpc_data)


    # 스타일 함수 정의
    def style_cpc_table(df):
        def apply_styles(row):
            # CPC 값 추출 (숫자만)
            row_cpc_str = row['CPC'].replace('₩', '').replace(',', '')
            row_cpc = int(row_cpc_str) if row_cpc_str.isdigit() else 0

            # 모든 CPC 값들을 숫자로 변환
            cpc_values = []
            for r in cpc_data:
                cpc_str = r['CPC'].replace('₩', '').replace(',', '')
                cpc_values.append(int(cpc_str) if cpc_str.isdigit() else 0)

            # 현재 CPC와 가장 가까운 두 값 찾기
            differences = [(abs(v - cpc), v) for v in cpc_values]
            differences.sort()
            closest_values = [differences[0][1]]
            if len(differences) > 1:
                closest_values.append(differences[1][1])

            # 배경색 설정
            if row_cpc in closest_values:
                bg_color = 'background-color: #e0f2fe;'
            else:
                bg_color = ''

            # 순이익 값 추출 (숫자만)
            profit_str = row['순이익'].replace('₩', '').replace(',', '')
            profit_value = float(profit_str) if profit_str.replace('-', '').isdigit() else 0

            # 순이익에 따른 색상
            if profit_value >= 0:
                profit_color = 'color: #155724; font-weight: bold;'
            else:
                profit_color = 'color: #721c24; font-weight: bold;'

            # 상태에 따른 색상
            if row['상태'] == '흑자':
                status_color = 'background-color: #d4edda; color: #155724; font-weight: bold;'
            else:
                status_color = 'background-color: #f8d7da; color: #721c24; font-weight: bold;'

            # 각 컬럼별 스타일 적용
            styles = [
                bg_color,  # CPC
                bg_color,  # 클릭
                bg_color,  # 전환
                bg_color + profit_color,  # 순이익
                bg_color + status_color if bg_color else status_color  # 상태
            ]

            return styles

        return df.style.apply(apply_styles, axis=1)


    st.dataframe(
        style_cpc_table(cpc_df),
        hide_index=True,
        use_container_width=True
    )

# 차트 섹션
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("💵 수익 구조")

    # 파이 차트
    fig = go.Figure(data=[go.Pie(
        labels=['매출원가', '광고비', '순이익'],
        values=[
            metrics['cogs'],
            budget,
            max(0, metrics['net_profit'])
        ],
        marker_colors=['#ef4444', '#3b82f6', '#10b981'],
        textposition='inside',
        textinfo='label+percent',
        hovertemplate='%{label}: ₩%{value:,.0f}<extra></extra>'
    )])

    fig.update_layout(
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 상세 지표")

    detail_metrics = {
        '필요 노출수': format_number(metrics['impressions']) + '회',
        '필요 클릭수': format_number(metrics['clicks']) + '회',
        '예상 전환수': format_number(metrics['conversions']) + '건',
        '예상 매출': format_currency(metrics['revenue']),
        '매출총이익률': f"{metrics['gross_margin']:.1f}%",
        'CPM': format_currency(metrics['cpm'])
    }

    for label, value in detail_metrics.items():
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.text(label)
        with col_b:
            st.markdown(f"**{value}**")

# 저장된 시나리오 표시
if st.session_state.history:
    st.markdown("---")
    st.subheader("📋 저장된 시나리오")

    history_df = pd.DataFrame(st.session_state.history)

    # 숫자 포맷 적용
    for col in ['예산', '객단가', 'CPC', '매출', '순이익']:
        if col in history_df.columns:
            history_df[col] = history_df[col].apply(lambda x: format_currency(x))

    for col in ['ROAS']:
        if col in history_df.columns:
            history_df[col] = history_df[col].apply(lambda x: f"{x:.2f}x")

    for col in ['ROI (%)']:
        if col in history_df.columns:
            history_df[col] = history_df[col].apply(lambda x: f"{x:.0f}%")

    st.dataframe(history_df, hide_index=True, use_container_width=True)
