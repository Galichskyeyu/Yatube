from datetime import date


def year(request):
    year = int(date.today().strftime("%Y"))
    return {'year': year}
