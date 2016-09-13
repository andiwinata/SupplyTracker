import config
from flask import flash


def remove_multi_spaces(text):
    return ' '.join(text.strip().split())


def map_csv_params(csv, map_type=str):
    try:
        map_obj = map(map_type, [remove_multi_spaces(x) for x in csv.split(config.PARAM_SEPARATOR)])
        return list(map_obj)
    except Exception as e:
        raise ValueError('Cannot convert into list of {} from your input\n{}'.format(map_type, e))


def is_int(s):
    try:
        int(s)
        return True
    except:
        return False


class classproperty(property):
    """
    Property for class (static property)
    http://stackoverflow.com/questions/1697501/python-staticmethod-with-property
    """
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()