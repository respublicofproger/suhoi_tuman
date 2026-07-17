import pandas as pd
import io
from cash import normalize_cash_sales

def parse_report(file):
    """
    Парсит отчет из файла (загруженного или скачанного)
    
    Args:
        file: может быть file-like object, bytes или путь к файлу
    
    Returns:
        DataFrame с обработанными данными
    """
    # Если передан путь к файлу (строка)
    if isinstance(file, str):
        df = pd.read_excel(file)
    # Если передан bytes (из скачивания)
    elif isinstance(file, bytes):
        df = pd.read_excel(io.BytesIO(file))
    # Если передан file-like object
    else:
        df = pd.read_excel(file)
    
    cols = {c.lower(): c for c in df.columns}
    
    approved = cols.get("approved")
    
    if approved is None:
        raise Exception("Не найден столбец Approved")
    
    df = df[df[approved] == True].copy()
    
    df = normalize_cash_sales(df)
    
    return df

def parse_dataframe(df):
    """
    Принимает уже загруженный DataFrame и обрабатывает его
    """
    cols = {c.lower(): c for c in df.columns}
    
    approved = cols.get("approved")
    
    if approved is None:
        raise Exception("Не найден столбец Approved")
    
    df = df[df[approved] == True].copy()
    
    df = normalize_cash_sales(df)
    
    return df