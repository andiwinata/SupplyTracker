from wtforms import StringField, BooleanField, DateTimeField, \
    SelectField, FieldList, FormField, IntegerField, SubmitField, HiddenField
from wtforms.widgets import TextArea, HiddenInput
from . import utils
import wtforms
from flask_wtf import Form
from wtforms.validators import DataRequired, Length, InputRequired, Optional
from app import db, models
import config
from datetime import datetime
from sqlalchemy import func
from flask import flash


def int_field_convert_to_none(field):
    """
    Used for select field which has coerce=int
    because None needs to be the value, so in
    the validation, convert it into None
    """
    if field.data == config.NULL_INTEGER:
        field.data = None


class LoginForm(Form):
    openid = StringField(label='openid', validators=[DataRequired()])
    remember_me = BooleanField(label='remember_me', default=False)


class IdForm(Form):
    url = ''
    id = IntegerField(label='id',
                      validators=[InputRequired()],
                      widget=HiddenInput())

    def __init__(self, id, url, **kwargs):
        super().__init__(**kwargs)
        self.id.data = id
        self.url = url

class SingleStringForm(Form):
    name_field = StringField(validators=[InputRequired(),
                                         Length(min=1, max=models.NAME_LENGTH)])
    submit_button = SubmitField()

class ItemTypeForm(Form):
    name_field = StringField(label='Item Type',
                             validators=[InputRequired(), Length(min=1, max=models.ITEM_TYPE_LENGTH)])
    submit_button = SubmitField(label='Save item type')
    check_exist = True

    def validate(self, **kwargs):
        if not super().validate():
            return False

        item_name = models.ItemType.format_item_type(self.name_field.data)
        # check if the item exists
        if not self.check_exist or not models.ItemType.check_exist(item_name):
            return True
        else:
            self.name_field.errors += ('This Item Type has existed in database, '
                                      'please make a new unique one',)
            return False


class CourierForm(Form):
    name_field = StringField(label='Courier',
                             validators=[InputRequired(), Length(min=1, max=models.ITEM_TYPE_LENGTH)])
    submit_button = SubmitField(label='Save courier')
    check_exist = True

    def validate(self, **kwargs):
        if not super().validate():
            return False

        # check if the item exists
        if not self.check_exist or not models.Courier.check_exist(self.name_field.data):
            return True
        else:
            self.name_field.errors += ('This Courier has existed in database, '
                                      'please make a new unique one',)
            return False

class TransactionMediumForm(Form):
    name_field = StringField(label='Transaction Medium',
                             validators=[InputRequired(), Length(min=1, max=models.ITEM_TYPE_LENGTH)])
    submit_button = SubmitField(label='Save transaction medium')

    def validate(self, **kwargs):
        if not super().validate():
            return False

        # check if the item exists
        if not models.TransactionMedium.check_exist(self.name_field.data):
            return True
        else:
            self.name_field.errors += ('This Medium has existed in database, '
                                       'please make a new unique one',)
            return False

class ContactForm(Form):
    name = StringField(label='Name',
                       validators=[Length(max=models.NAME_LENGTH), InputRequired()])
    contact = StringField(label='Contact',
                          validators=[Length(max=models.CONTACT_LENGTH)])
    address = StringField(label='Address',
                          validators=[Length(max=models.ADDRESS_LENGTH)])
    submit_button = SubmitField(label='Save contact')


# ------------
# Purchase Forms
# ------------
def get_item_type_list():
    return [(i.id, i.item_type)
            for i in models.ItemType.query.order_by(models.ItemType.item_type)]
    # trying to do query only in models but seems make it complicated
    # list_item_type(list_per_page='ALL',
    #                include_header=False,
    #                order_by=models.ItemType.item_type)]


def get_supplier_list():
    return [(s.id, s.name) for s in models.Supplier.query.order_by(models.Supplier.name)]


# not derived from Form which is flask-wtforms class
# because flask-wtforms Form class is derived from SecureForm
# causing multiple CSRF token if used as FieldList
class ItemPurchaseForm(wtforms.Form):
    ids = HiddenField(label='Item Ids')
    purchase_price = IntegerField(label='Purchase Price (each): ',
                                  validators=[InputRequired()])
    # choices will be added later by __init__
    item_type = SelectField(label='Item Type: ',
                            coerce=int,
                            validators=[InputRequired()])

    quantity = IntegerField(label='Item Quantity',
                            validators=[InputRequired()])

    def validate(self, *args, **kwargs):
        if not super().validate():
            self.purchase_price.errors.append(super().errors)
            return False

        if self.quantity.data < 0:
            self.quantity.errors.append('Quantity cannot be negative')

        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type.choices = get_item_type_list()


class PurchaseTransactionForm(Form):
    yyyy = IntegerField(label='Transaction Year',
                        validators=[InputRequired()])
    MM = IntegerField(label='Transaction Month',
                      validators=[InputRequired()])
    dd = IntegerField(label='Transaction Day',
                      validators=[InputRequired()])

    HH = IntegerField(label='Transaction Hour',
                      validators=[InputRequired()])
    mm = IntegerField(label='Transaction Minute',
                      validators=[InputRequired()])
    ss = IntegerField(label='Transaction Second',
                      default=0, validators=[InputRequired()])
    # choices will be added later by __init__
    supplier_id = SelectField(label='Supplier: ',
                              coerce=int,
                              validators=[InputRequired()])

    notes = StringField(label='Notes',
                        validators=[Length(max=models.NOTES_LENGTH)],
                        widget=TextArea())

    transaction_items = FieldList(FormField(ItemPurchaseForm),
                                  label='Purchased items',
                                  min_entries=1)
    submit_button = SubmitField(label='Save purchase transaction')

    def validate(self, **kwargs):

        if not super().validate():
            self.yyyy.errors += (super().errors, 'super not validated')
            return False

        # check if the date is valid, also this has included the leap year factor
        try:
            dt = datetime(self.yyyy.data, self.MM.data, self.dd.data,
                          self.HH.data, self.mm.data, self.ss.data)
        except ValueError as ve:
            self.yyyy.errors += (ve,)
            return False

        if dt > datetime.now():
            self.yyyy.errors += ('Date time cannot be in the future',
                                 'current date: {}'.format(datetime.now()),
                                 'input date: {}'.format(dt))
            return False

        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.supplier_id.choices = get_supplier_list()


# ----------
# Sale Forms
# ----------
def get_unsold_items_dict(name_key, stock_key, sold_key):
    # get unsold items and its quantity
    unsold_items = db.session.query(models.Item.item_type_id, models.ItemType.item_type,
                                    func.count(models.Item.id), models.Item.sale_transaction_id) \
        .join(models.ItemType) \
        .group_by(models.Item.item_type_id, models.Item.sale_transaction_id)

    # flatten the dict to merge everything based on id, name, stock, sold
    flattened_sale_dict = {}

    for item in unsold_items:
        if item[0] not in flattened_sale_dict:
            # format [name, qty_available, qty_sold]
            flattened_sale_dict[item[0]] = {name_key: item[1],
                                            stock_key: 0,
                                            sold_key: 0}

        # item has been sold because
        # sale_transaction_id exists
        # change the total item sold
        if item[3]:
            flattened_sale_dict[item[0]][sold_key] = item[2]
        else:
            flattened_sale_dict[item[0]][stock_key] = item[2]

    return flattened_sale_dict


# compulsory so no None
def get_customer_list():
    return [(c.id, c.name) for c in models.Customer.query \
        .order_by(models.Customer.name)]


def get_courier_list():
    list = [(c.id, c.name) for c in models.Courier.query \
        .order_by(models.Courier.name)]
    list.insert(0, (config.NULL_INTEGER, '---'))
    return list


def get_medium_list():
    list = [(m.id, m.name) for m in models.TransactionMedium.query]
    list.insert(0, (config.NULL_INTEGER, '---'))
    return list


class ItemSaleForm(wtforms.Form):
    stock_separator = ' - stock: '
    sold_separator = ' - sold: '

    sale_price = IntegerField(label='Sale Price (each): ',
                              validators=[InputRequired()])

    # declare choice later on because wtform behaving weird not updating choices after database update
    item_stock = SelectField(label='Item Type: ',
                             coerce=int,
                             validators=[DataRequired()])
    quantity = IntegerField(label='Item Quantity',
                            validators=[InputRequired()])

    def validate(self, *args, **kwargs):
        if not super().validate():
            self.sale_price.errors += (super().errors,)
            return False

        if self.quantity.data < 0:
            self.quantity.errors.append('Quantity cannot be negative')

        # TODO include the edit sale transaction stock
        # and put back later on check qty total

        # get maximum quantity for selected item_type
        # max_qty = int(self.unsold_items_dict[self.item_stock.data]['stock'])
        #
        # if self.quantity.data > max_qty:
        #     self.quantity.errors += \
        #         ("Quantity exceeds the item's stock for {}"\
        #         .format(self.unsold_items_dict[self.item_stock.data]['name']),)
        #     return False

        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unsold_items_dict = get_unsold_items_dict('name', 'stock', 'sold')
        # convert to dict
        # cannot use dict comprehension because the scope inside dict comprehension
        # cannot access the variable class and it requires few tricks to do it
        choices = [(k, '{}{}{}{}{}'.format(v['name'], self.stock_separator,
                                           v['stock'], self.sold_separator,
                                           v['sold'])) for k, v in self.unsold_items_dict.items()]

        self.item_stock.choices = choices


class SaleTransactionForm(Form):
    yyyy = IntegerField(label='Transaction Year',
                        validators=[InputRequired()])
    MM = IntegerField(label='Transaction Month',
                      validators=[InputRequired()])
    dd = IntegerField(label='Transaction Day',
                      validators=[InputRequired()])

    HH = IntegerField(label='Transaction Hour',
                      validators=[InputRequired()])
    mm = IntegerField(label='Transaction Minute',
                      validators=[InputRequired()])
    ss = IntegerField(label='Transaction Second',
                      default=0, validators=[InputRequired()])

    delivery_fee = IntegerField(label='Delivery Fee', validators=[Optional()])
    customer_id = SelectField(label='Customer',
                              coerce=int,
                              validators=[InputRequired()])
    courier_id = SelectField(label='Courier', coerce=int, validators=[Optional()])
    transaction_medium_id = SelectField(label='Transaction Medium',
                                        coerce=int, validators=[Optional()])

    notes = StringField(label='Notes',
                        validators=[Length(max=models.NOTES_LENGTH)],
                        widget=TextArea())

    transaction_items = FieldList(FormField(ItemSaleForm),
                                  label='Sale items',
                                  min_entries=1)
    submit_button = SubmitField(label='Save Sale Transaction')

    transaction_items_choices_dict = {}

    def validate(self, **kwargs):
        if not super().validate():
            self.yyyy.errors += (super().errors, 'super not validated')
            return False

        # check if the date is valid, also this include the leap year factor
        try:
            dt = datetime(self.yyyy.data, self.MM.data, self.dd.data,
                          self.HH.data, self.mm.data, self.ss.data)
        except ValueError as ve:
            self.yyyy.errors += (ve,)
            return False

        if dt > datetime.now():
            self.yyyy.errors += ('Date time cannot be in the future',
                                 'current date: {}'.format(datetime.now()),
                                 'input date: {}'.format(dt))
            return False

        int_field_convert_to_none(self.courier_id)
        int_field_convert_to_none(self.transaction_medium_id)

        return True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer_id.choices = get_customer_list()
        self.courier_id.choices = get_courier_list()
        self.transaction_medium_id.choices = get_medium_list()


# Table form
class FilterTableForm(Form):
    id = StringField(label='ID', validators=[Optional()])
    year = StringField(label='Year', validators=[Optional()])
    month = StringField(label='Month', validators=[Optional()])
    day = StringField(label='Day', validators=[Optional()])
    submit_button = SubmitField(label='Filter')

    def validate(self, **kwargs):

        if not super().validate():
            self.id.errors += (super().errors, 'super not validated')
            return False

        if self.year.data and all(x > 9999 or x < 0 for x in utils.map_csv_params(self.year.data, int)):
            self.year.errors += ('Year is not valid', 'Check your input format')
            return False

        if self.month.data and all(x > 12 or x < 1 for x in utils.map_csv_params(self.month.data, int)):
            self.month.errors += ('Month is not valid', 'Check your input format')
            return False

        if self.day.data and all(x > 31 or x < 1 for x in utils.map_csv_params(self.day.data, int)):
            self.day.errors += ('Day is not valid', 'Check your input format')
            return False

        return True


# Pagination form
class PerPageForm(Form):
    per_page = SelectField(label='Display Per Page',
                           choices=[(x, x) for x in config.PER_PAGE_DEFAULTS])

    def __init__(self, per_page, *args, **kwargs):
        # unlike choices=..., default
        # cannot select default value by assigning self.per_page.default=...
        # alternative is https://groups.google.com/forum/#!topic/wtforms/6c656YspjRY
        if per_page in config.PER_PAGE_DEFAULTS:
            kwargs.setdefault('per_page', per_page)

        super().__init__(*args, **kwargs)  # set per page
