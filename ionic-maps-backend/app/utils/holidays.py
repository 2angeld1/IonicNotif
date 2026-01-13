"""
Utilidades para detectar días festivos en Panamá
"""
from datetime import date, datetime
from typing import Optional

# Festivos fijos de Panamá (mes, día)
FIXED_HOLIDAYS = [
    (1, 1),   # Año Nuevo
    (1, 9),   # Día de los Mártires
    (5, 1),   # Día del Trabajo
    (11, 3),  # Separación de Panamá de Colombia
    (11, 4),  # Día de la Bandera
    (11, 5),  # Consolidación de la Separación (Colón)
    (11, 10), # Primer Grito de Independencia (Villa de Los Santos)
    (11, 28), # Independencia de Panamá de España
    (12, 8),  # Día de las Madres
    (12, 20), # Duelo Nacional
    (12, 24), # Noche Buena
    (12, 25), # Navidad
    (12, 31), # Año Viejo
]

# Festivos variables (se actualizan cada año)
# Para 2024-2026 aproximados
VARIABLE_HOLIDAYS_BY_YEAR = {
    2024: [
        (2, 12),  # Carnaval
        (2, 13),  # Carnaval
        (3, 29),  # Viernes Santo
    ],
    2025: [
        (3, 3),   # Carnaval
        (3, 4),   # Carnaval
        (4, 18),  # Viernes Santo
    ],
    2026: [
        (2, 16),  # Carnaval
        (2, 17),  # Carnaval
        (4, 3),   # Viernes Santo
    ],
}


def is_holiday(check_date: Optional[date] = None) -> bool:
    """
    Verificar si una fecha es día festivo en Panamá
    
    Args:
        check_date: Fecha a verificar. Si es None, usa la fecha actual.
    
    Returns:
        True si es festivo, False si no
    """
    if check_date is None:
        check_date = date.today()
    
    month_day = (check_date.month, check_date.day)
    
    # Verificar festivos fijos
    if month_day in FIXED_HOLIDAYS:
        return True
    
    # Verificar festivos variables del año
    year_holidays = VARIABLE_HOLIDAYS_BY_YEAR.get(check_date.year, [])
    if month_day in year_holidays:
        return True
    
    return False


def is_holiday_from_datetime(dt: Optional[datetime] = None) -> bool:
    """Wrapper para usar con datetime en lugar de date"""
    if dt is None:
        dt = datetime.now()
    return is_holiday(dt.date())
