from services.health import check_health


def health_check():
    return check_health()
