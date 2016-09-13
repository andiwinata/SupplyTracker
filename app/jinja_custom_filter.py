from app import app


@app.template_filter('table_data')
def table_data(s):
    try:
        if isinstance(s, int):
            return "{:,}".format(s)
        elif isinstance(s, float):
            return "{:,.2f}".format(s)
        # is digit is correct for now since there is no currency involved
        elif isinstance(s, str) and s.isdigit():
            return "{:,}".format(int(s))
        elif s is None:
            return "---"
        else:
            return s
    except:
        return s


@app.template_filter('table_head')
def table_head(s):
    if (isinstance(s, str)):
        return s.replace('_',' ').upper()
