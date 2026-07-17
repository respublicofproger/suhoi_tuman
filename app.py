import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from analytics import make_stats
from parser import parse_dataframe
from downloader import VendotekDownloader

def money(value):
    return f"{value:,.0f}".replace(",", " ") + " ₽"

st.set_page_config(
    page_title="Vendotek Analytics - Авто",
    layout="wide"
)

st.title("💧 Сухой туман - Автоматическая аналитика")

# Параметры загрузки
org_id = "o4890"

# Дата с которой начинаем (можно менять)
default_from_date = "2026-04-01"

# Создаем колонки для управления
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.write("📅 Период анализа:")
    from_date = st.text_input("Дата начала", value=default_from_date)
    
    # Кнопка загрузки
    if st.button("🔄 Обновить данные", type="primary"):
        with st.spinner("Загрузка данных из Vendotek..."):
            # Создаем загрузчик
            downloader = VendotekDownloader()
            
            # Сегодняшняя дата
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            # Скачиваем данные
            df = downloader.download_to_dataframe(org_id, from_date, to_date)
            
            if df is not None:
                # Сохраняем в сессию
                st.session_state['raw_data'] = df
                st.session_state['last_update'] = datetime.now()
                st.success(f"✅ Данные загружены: {len(df)} транзакций")
            else:
                st.error("❌ Ошибка загрузки данных")

# Проверяем наличие данных в сессии
if 'raw_data' not in st.session_state or st.session_state.get('raw_data') is None:
    st.info("Нажмите кнопку 'Обновить данные' для загрузки")
    st.stop()

# Обрабатываем данные
try:
    sales = parse_dataframe(st.session_state['raw_data'])
    
    # Вычисляем статистику
    stats = make_stats(sales)
    
    # Показываем время последнего обновления
    if 'last_update' in st.session_state:
        st.caption(f"Последнее обновление: {st.session_state['last_update'].strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Отображаем метрики
    st.subheader("💰 Заработано")
    
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("Сегодня", money(stats["today"]["revenue"]))
    c2.metric("Неделя", money(stats["week"]["revenue"]))
    c3.metric("Месяц", money(stats["month"]["revenue"]))
    c4.metric("Всего", money(stats["total"]["revenue"]))
    
    st.subheader("👥 Количество клиентов")
    
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("Сегодня", stats["today"]["sales"])
    c2.metric("Неделя", stats["week"]["sales"])
    c3.metric("Месяц", stats["month"]["sales"])
    c4.metric("Всего", stats["total"]["sales"])
    
    st.success(f"Обработано продаж: {len(sales)}")
    
    # Показываем таблицу
    table = sales.copy()
    
    datetime_col = None
    for c in table.columns:
        if "date" in c.lower():
            datetime_col = c
            break
    
    if datetime_col:
        table[datetime_col] = pd.to_datetime(table[datetime_col])
        
        table["Дата"] = table[datetime_col].dt.strftime("%d.%m.%Y")
        table["Время"] = table[datetime_col].dt.strftime("%H:%M:%S")
    
    table["Сумма"] = table["Amount"]
    
    if "PAN" in table.columns:
        table["Номер карты"] = table["PAN"].fillna("Наличные")
    else:
        table["Номер карты"] = "Наличные"
    
    table = table.sort_values(by=datetime_col, ascending=False) if datetime_col else table
    
    # Выбираем колонки для отображения
    display_cols = ["Дата", "Время", "Сумма", "Номер карты"]
    available_cols = [col for col in display_cols if col in table.columns]
    
    st.dataframe(
        table[available_cols],
        use_container_width=True,
        hide_index=True
    )
    
except Exception as e:
    st.error(f"Ошибка обработки данных: {e}")
    st.stop()