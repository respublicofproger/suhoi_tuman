import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from analytics import make_stats
from parser import parse_dataframe
from downloader import VendotekDownloader
import json

def money(value):
    return f"{value:,.0f}".replace(",", " ") + " ₽"

st.set_page_config(
    page_title="Vendotek Analytics - Авто",
    layout="wide"
)

st.title("💧 Сухой туман")

# Параметры загрузки
org_id = "o4890"
default_from_date = "2026-04-01"

# Создаем колонки для управления
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.write("📅 Период анализа:")
    from_date = st.text_input("Дата начала", value=default_from_date)
    
    if st.button("🔄 Обновить данные", type="secondary"):
        with st.spinner("Загрузка данных из Vendotek..."):
            downloader = VendotekDownloader()
            to_date = datetime.now().strftime('%Y-%m-%d')
            df = downloader.download_to_dataframe(org_id, from_date, to_date)
            
            if df is not None:
                st.session_state['raw_data'] = df
                st.session_state['last_update'] = datetime.now()
                st.success(f"✅ Данные загружены: {len(df)} транзакций")
            else:
                st.error("❌ Ошибка загрузки данных")

# Проверяем наличие данных
if 'raw_data' not in st.session_state or st.session_state.get('raw_data') is None:
    st.info("Нажмите кнопку 'Обновить данные' для загрузки")
    st.stop()

# Обрабатываем данные
try:
    sales = parse_dataframe(st.session_state['raw_data'])
    
    # Вычисляем статистику
    stats = make_stats(sales)
    
    # Показываем время обновления
    if 'last_update' in st.session_state:
        st.caption(f"Последнее обновление: {st.session_state['last_update'].strftime('%d.%m.%Y %H:%M:%S')}")
    
    # ========== МЕТРИКИ ==========
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
    
    # ========== ГРАФИК НА CHART.JS ЧЕРЕЗ HTML ==========
    st.subheader("👥 Динамика количества клиентов по дням")
    
    # Подготовка данных для графика
    sales_copy = sales.copy()
    
    # Находим колонку с датой
    date_col = None
    for c in sales_copy.columns:
        if "date" in c.lower():
            date_col = c
            break
    
    if date_col:
        # ПРИНУДИТЕЛЬНОЕ ПРЕОБРАЗОВАНИЕ В DATETIME
        try:
            sales_copy[date_col] = pd.to_datetime(sales_copy[date_col], errors='coerce')
            sales_copy = sales_copy.dropna(subset=[date_col])
            
            if len(sales_copy) == 0:
                st.warning("Нет корректных дат для построения графика")
                st.stop()
                
        except Exception as e:
            st.error(f"Ошибка преобразования дат: {e}")
            st.stop()
        
        # СОЗДАЕМ КОЛОНКУ ТОЛЬКО С ДАТОЙ (БЕЗ ВРЕМЕНИ)
        sales_copy['Дата_только'] = sales_copy[date_col].dt.date
        
        # Группируем по дням
        daily_sales = sales_copy.groupby('Дата_только').agg({
            'Amount': ['count', 'sum', 'mean']
        }).reset_index()
        
        daily_sales.columns = ['Дата', 'Клиенты', 'Выручка', 'Средний чек']
        daily_sales = daily_sales.sort_values('Дата')
        
        # ПРЕОБРАЗУЕМ ДАТУ ОБРАТНО В DATETIME ДЛЯ ФОРМАТИРОВАНИЯ
        daily_sales['Дата'] = pd.to_datetime(daily_sales['Дата'])
        
        if len(daily_sales) == 0:
            st.warning("Нет данных для отображения")
            st.stop()
        
        # Форматируем даты для отображения
        dates = daily_sales['Дата'].dt.strftime('%d.%m.%Y').tolist()
        clients = daily_sales['Клиенты'].tolist()
        
        # Создаем JSON-данные для JavaScript
        labels_json = json.dumps(dates)
        data_json = json.dumps(clients)
        
        # HTML-код с графиком (без кнопок)
        chart_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>График клиентов</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                }}
                .chart-container {{
                    position: relative;
                    height: 400px;
                    width: 100%;
                    padding: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="chart-container">
                <canvas id="myChart"></canvas>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                // ДАННЫЕ ДЛЯ ГРАФИКА
                const labels = {labels_json};
                const dataValues = {data_json};
                
                // СОЗДАЕМ ГРАДИЕНТ
                const ctx = document.getElementById('myChart').getContext('2d');
                const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                gradient.addColorStop(0, 'rgba(46, 204, 113, 0.3)');
                gradient.addColorStop(1, 'rgba(46, 204, 113, 0.0)');
                
                // СОЗДАЕМ ГРАФИК
                const chart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: 'Клиенты',
                            data: dataValues,
                            borderColor: '#2ecc71',
                            backgroundColor: gradient,
                            borderWidth: 3,
                            pointBackgroundColor: '#2ecc71',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 6,
                            pointHoverRadius: 10,
                            pointStyle: 'circle',
                            fill: true,
                            tension: 0.4,
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'top',
                                labels: {{
                                    font: {{ size: 14, weight: 'bold' }},
                                    color: '#2c3e50',
                                    usePointStyle: true,
                                    pointStyle: 'circle'
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0,0,0,0.8)',
                                titleFont: {{ size: 14 }},
                                bodyFont: {{ size: 13 }},
                                cornerRadius: 8,
                                padding: 12,
                                callbacks: {{
                                    label: function(context) {{
                                        return '👥 Клиентов: ' + context.parsed.y;
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                ticks: {{
                                    maxRotation: 45,
                                    minRotation: 45,
                                    font: {{ size: 11 }},
                                    color: '#666'
                                }},
                                grid: {{
                                    display: true,
                                    color: 'rgba(0,0,0,0.06)',
                                    drawBorder: true,
                                    borderColor: 'rgba(0,0,0,0.1)'
                                }}
                            }},
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    font: {{ size: 12 }},
                                    color: '#666',
                                    stepSize: 1
                                }},
                                grid: {{
                                    display: true,
                                    color: 'rgba(0,0,0,0.06)',
                                    drawBorder: true,
                                    borderColor: 'rgba(0,0,0,0.1)'
                                }}
                            }}
                        }},
                        animation: {{
                            duration: 1500,
                            easing: 'easeInOutQuart'
                        }},
                        interaction: {{
                            intersect: false,
                            mode: 'index'
                        }},
                        hover: {{
                            mode: 'index',
                            intersect: false
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        # Отображаем график
        st.components.v1.html(chart_html, height=450)
        
        # Дополнительная статистика под графиком
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📅 Дней в периоде",
                len(daily_sales)
            )
        
        with col2:
            max_clients_val = daily_sales['Клиенты'].max()
            max_date = daily_sales[daily_sales['Клиенты'] == max_clients_val]['Дата'].iloc[0]
            st.metric(
                "🏆 Макс. клиентов",
                f"{max_clients_val}",
                f"{max_date.strftime('%d.%m.%Y')}"
            )
        
        with col3:
            avg_clients = daily_sales['Клиенты'].mean()
            st.metric(
                "📊 Среднее за день",
                f"{avg_clients:.1f}"
            )
        
        with col4:
            if len(daily_sales) > 5:
                first_week = daily_sales['Клиенты'].head(3).mean()
                last_week = daily_sales['Клиенты'].tail(3).mean()
                change = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
                
                if change > 5:
                    trend_text = f"📈 Растет (+{change:.1f}%)"
                elif change < -5:
                    trend_text = f"📉 Падает ({change:.1f}%)"
                else:
                    trend_text = f"➡️ Стабильно ({change:+.1f}%)"
                
                st.metric(
                    "📈 Тренд",
                    trend_text
                )
    else:
        st.warning("Не найден столбец с датами для построения графика")
    
    st.success(f"Обработано продаж: {len(sales)}")
    
    # ========== ТАБЛИЦА ==========
    st.subheader("📋 Детальная таблица продаж")
    
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
    
    display_cols = ["Дата", "Время", "Сумма", "Номер карты"]
    available_cols = [col for col in display_cols if col in table.columns]
    
    st.dataframe(
        table[available_cols],
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
except Exception as e:
    st.error(f"Ошибка обработки данных: {e}")
    st.stop()