from datetime import datetime


def convert_string_to_datetime(date_string: str) -> datetime:
    return datetime.strptime(date_string, "%d/%m/%Y %H:%M:%S")
