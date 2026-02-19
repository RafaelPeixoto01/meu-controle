from datetime import date
import calendar

def add_months(source_date: date, months: int) -> date:
    """
    Adiciona 'months' meses a 'source_date', preservando o dia o maximo possivel.
    Se o dia nao existir no mes destino (ex: 31/01 + 1 mes -> Fev), ajusta para o ultimo dia do mes.
    """
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
