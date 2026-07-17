import pandas as pd


def _find_column(df, names):
    """
    Ищет колонку независимо от регистра.
    """
    cols = {c.lower().strip(): c for c in df.columns}

    for name in names:
        if name.lower() in cols:
            return cols[name.lower()]

    raise Exception(f"Не найдена колонка: {names}")


def normalize_cash_sales(df: pd.DataFrame):

    cash_col = _find_column(df, [
        "Cash amount",
        "Cash Amount",
        "Cash"
    ])

    amount_col = _find_column(df, [
        "Amount",
        "amount"
    ])

    result = []

    buffer = []
    buffer_sum = 0

    for _, row in df.iterrows():

        cash = row[cash_col]

        if pd.isna(cash):
            cash = 0

        cash = float(cash)

        # Карточная операция
        if cash == 0:

            # если перед этим был незакрытый буфер —
            # сохраняем его как подозрительный
            if buffer:
                print("Не удалось разобрать наличную операцию:",
                      buffer_sum)

                buffer.clear()
                buffer_sum = 0

            result.append(row)

            continue

        # Наличная операция

        buffer.append(row)
        buffer_sum += cash

        # Попали примерно в 1000 рублей
        if 900 <= buffer_sum <= 1100:

            sale = buffer[0].copy()

            sale[cash_col] = 500
            sale[amount_col] = 500

            result.append(sale)

            buffer.clear()
            buffer_sum = 0

        # Если сумма слишком большая —
        # что-то пошло не так
        elif buffer_sum > 1100:

            print("Ошибка обработки наличных:", buffer_sum)

            buffer.clear()
            buffer_sum = 0

    # Если файл закончился,
    # а буфер не пустой
    if buffer:
        print("Необработанная наличная операция:", buffer_sum)

    return pd.DataFrame(result)