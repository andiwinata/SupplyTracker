import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

WTF_CRSF_ENABLED = True
SECRET_KEY = 'i-will-never-know'

TABLE_FOOTER_KEYWORDS = ['TOTAL', 'Total', 'total']

PARAM_SEPARATOR = ','
NULL_INTEGER = -1

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}
]

# pagination
DEFAULT_PAGE_NUMBER = 1
DEFAULT_POSTS_PER_PAGE = 25
ALL_IN_PAGE_KEYWORD = 'ALL'
PER_PAGE_DEFAULTS = [5, 10, 25, 50, 100, 200, 'ALL']

# URL parameters
URL_PAGE_NUM = 'page'
URL_PER_PAGE = 'per_page'
URL_ID = 'id'
URL_YEAR = 'year'
URL_MONTH = 'month'
URL_DAY = 'day'