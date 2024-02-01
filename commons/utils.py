from datetime import datetime


def get_current_date_str(now: int = datetime.now()):
    formatted_date = now.strftime("%Y-%m-%d")
    return formatted_date
