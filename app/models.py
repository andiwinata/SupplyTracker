from app import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, extract, distinct, exists
from flask import flash
from config import DEFAULT_PAGE_NUMBER, DEFAULT_POSTS_PER_PAGE, ALL_IN_PAGE_KEYWORD
from app import utils

ITEM_TYPE_LENGTH = 120
NAME_LENGTH = 120
CONTACT_LENGTH = 120
ADDRESS_LENGTH = 200
NOTES_LENGTH = 250

# TODO: Note? Maybe using 'try' approach is not the best way?
# Need to find a way to handle exception better without throwing
# destroying front-end appearance

def paginate_query(query, page_num, per_page):
    # page num check
    if utils.is_int(page_num):
        page_num = int(page_num)
    else:
        page_num = DEFAULT_PAGE_NUMBER

    # per page check
    if isinstance(per_page, str) and per_page.upper() == ALL_IN_PAGE_KEYWORD:
        return query
    elif utils.is_int(per_page):
        per_page = int(per_page)
    else:
        per_page = DEFAULT_POSTS_PER_PAGE

    # index starts with 0
    start_offset = (page_num - 1) * per_page
    return query.slice(start_offset, start_offset + per_page)


def validate_transactions(cls, purchase_trans=False, sale_trans=False):
    """
    Validating transactions
    Will delete transaction record if there is no items inside it
    This caused by deletion of Item from ItemType
    or Item from PurchaseTransaction which breaching the integrity
    of Sale Transaction
    """
    # Not using try_delete because purchase trans will also call this
    # function

    if purchase_trans:
        # purchase trans without any of items referencing
        pq = db.session.query(PurchaseTransaction.id).filter(
            ~exists().where(PurchaseTransaction.id == Item.purchase_transaction_id))

        print("Going to be deleted purchase trans: {}".format(pq.all()))

        for p in pq:
            pt = PurchaseTransaction.query.get(p)
            db.session.delete(pt)

        try:
            db.session.commit()
        except Exception as e:
            cls.add_error(e)
            return False

    if sale_trans:
        # sale trans without any of items referencing
        sq = db.session.query(SaleTransaction.id).filter(
            ~exists().where(SaleTransaction.id == Item.sale_transaction_id))

        print("Going to be deleted sale trans: {}".format(sq.all()))

        for s in sq:
            st = SaleTransaction.query.get(s)
            db.session.delete(st)

        try:
            db.session.commit()
        except Exception as e:
            cls.add_error(e)
            return False

    return True


class STModel(db.Model):
    __abstract__ = True

    errors = []

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, vars(self))

    @classmethod
    def add_error(cls, error):
        # limit to only 10 errors
        cls.errors.insert(0, error)
        cls.errors = cls.errors[:10]

    @utils.classproperty
    def error(cls):
        return cls.errors[0]

    @utils.classproperty
    def total(cls):
        q = db.session.query(func.count(cls.id))
        return q.scalar()

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        raise NotImplementedError("Please implement this base method class")

    @classmethod
    def try_delete(cls, id, **kwargs):
        item = cls.query.get(id)
        if item is None:
            cls.add_error('No data found')
            return False

        try:
            db.session.delete(item)
            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    @classmethod
    def update(cls, item):
        if not isinstance(item, db.Model):
            raise TypeError('Updated model must derive from Model')

        db.session.add(item)
        db.session.commit()


class Item(STModel):
    id = db.Column(db.Integer, primary_key=True)

    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)

    purchase_price = db.Column(db.Integer, index=True, nullable=False)
    sale_price = db.Column(db.Integer, index=True)

    purchase_transaction_id = db.Column(db.Integer,
                                        db.ForeignKey('purchase_transaction.id'),
                                        nullable=False)
    sale_transaction_id = db.Column(db.Integer, db.ForeignKey('sale_transaction.id'))

    @hybrid_property
    def profit(self):
        if self.sale_price and self.sale_transaction_id is not None:
            return self.sale_price - self.purchase_price
        else:
            return None

    @utils.classproperty
    def total_item_stock(cls):
        q = db.session.query(func.count(Item.id)) \
            .group_by(Item.item_type_id)
        return len(q.all())

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        purchase_price_label = 'purchase_price'
        sale_price_label = 'sale_price'
        purchase_transaction_label = 'purchase_transaction_date'
        sale_transaction_label = 'sale_transaction_date'

        q = db.session.query(Item.id,
                             ItemType.item_type,
                             Item.purchase_price.label(purchase_price_label),
                             Item.sale_price.label(sale_price_label),
                             PurchaseTransaction.transaction_date.label(purchase_transaction_label),
                             SaleTransaction.transaction_date.label(sale_transaction_label),
                             Supplier.name.label('supplier')) \
            .outerjoin(ItemType, PurchaseTransaction, SaleTransaction, Supplier) \
            .order_by(Item.id.desc())

        q = paginate_query(q, page_num, list_per_page)
        at_list = q.all()

        column_names = tuple(x['name'] for x in q.column_descriptions)

        purchase_price_id = column_names.index(purchase_price_label)
        sale_price_id = column_names.index(sale_price_label)

        total_row = [''] * len(column_names)
        total_row[0] = 'TOTAL'

        total_row[purchase_price_id] = sum(x[purchase_price_id] for x in at_list if x[purchase_price_id] is not None)
        total_row[sale_price_id] = sum(x[sale_price_id] for x in at_list if x[sale_price_id] is not None)

        at_list.append(tuple(total_row))
        at_list.insert(0, column_names)

        return at_list

    @classmethod
    def get_stock_list(cls, page_num=DEFAULT_PAGE_NUMBER, list_per_page=DEFAULT_POSTS_PER_PAGE):
        q = db.session.query(Item.item_type_id,
                             ItemType.item_type,
                             (func.count(Item.purchase_transaction_id) - func.count(Item.sale_transaction_id)).label(
                                 'stock_qty'),
                             func.count(Item.sale_transaction_id).label('sold_qty'),
                             func.count(Item.id).label('total_qty'),
                             func.sum(Item.profit).label('total_proft_from_sold')) \
            .join(ItemType) \
            .group_by(Item.item_type_id) \
            .order_by(Item.item_type_id)

        q = paginate_query(q, page_num, list_per_page)

        is_list = q.all()
        is_list.insert(0, tuple(x['name'] for x in q.column_descriptions))
        return is_list


class ItemType(STModel):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(NAME_LENGTH), index=True,
                          unique=True, nullable=False)
    items = db.relationship('Item', backref='item_type', lazy='dynamic',
                            cascade='save-update, merge, delete')

    @classmethod
    def format_item_type(cls, text):
        return '_'.join(text.strip().upper().split())

    @classmethod
    def check_exist(cls, item_type):
        return db.session.query(exists().where(ItemType.item_type == ItemType.format_item_type(item_type))).scalar()

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        q = ItemType.query.with_entities(ItemType.id, ItemType.item_type)
        q = paginate_query(q, page_num, list_per_page)

        if order_by:
            q = q.order_by(order_by)

        it_list = q.all()

        if include_header:
            it_list.insert(0, tuple(x['name'] for x in q.column_descriptions))
        return it_list

    @classmethod
    def try_add(cls, item_type):
        # convert name to correct one
        # if item exists in db already -> it has been checked by
        # the model and form
        item_type = ItemType.format_item_type(item_type)
        new = ItemType(item_type=item_type)
        try:
            db.session.add(new)
            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def try_delete(cls, id, **kwargs):
        if super().try_delete(id, **kwargs):
            if not validate_transactions(cls, True, True):
                cls.add_error('Fail to validate transaction, item type is '
                              'deleted but some transactions does not have '
                              'items referenced into it')
                return False
            return True
        else:
            return False


class Supplier(STModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_LENGTH), index=True, nullable=False)
    contact = db.Column(db.String(CONTACT_LENGTH))
    address = db.Column(db.String(ADDRESS_LENGTH))
    purchase_transactions = db.relationship('PurchaseTransaction', backref='supplier',
                                            lazy='dynamic',
                                            cascade='save-update, merge, delete')

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        q = Supplier.query.with_entities(Supplier.id,
                                         Supplier.name,
                                         Supplier.contact,
                                         Supplier.address)
        q = paginate_query(q, page_num, list_per_page)

        s_list = q.all()
        s_list.insert(0, tuple(x['name'] for x in q.column_descriptions))
        return s_list

    @classmethod
    def try_add(cls, name, contact, address):
        new = Supplier(name=name, contact=contact, address=address)
        try:
            db.session.add(new)
            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False


class Customer(STModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_LENGTH), index=True, nullable=False)
    contact = db.Column(db.String(CONTACT_LENGTH))
    address = db.Column(db.String(ADDRESS_LENGTH))
    sale_transactions = db.relationship('SaleTransaction',
                                        backref='customer', lazy='dynamic',
                                        cascade='save-update, merge, delete')

    @classmethod
    def check_exist(cls, name):
        return db.session.query(exists().where(Customer.name == name)).scalar()

    @classmethod
    def try_add(cls, name, contact=None, address=None):
        # no need to check exists in here because
        # the form has handled it and the model fields has unique=True
        new_cou = Customer(name=name, contact=contact, address=address)
        try:
            db.session.add(new_cou)
            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        q = Customer.query.with_entities(Customer.id,
                                         Customer.name,
                                         Customer.address,
                                         Customer.contact)
        q = paginate_query(q, page_num, list_per_page)

        if order_by:
            q = q.order_by(order_by)

        c_list = q.all()

        if include_header:
            c_list.insert(0, tuple(x['name'] for x in q.column_descriptions))
        return c_list


class Courier(STModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_LENGTH), index=True, nullable=False, unique=True)
    sale_transactions = db.relationship('SaleTransaction', backref='courier', lazy='dynamic')

    @classmethod
    def check_exist(cls, name):
        return db.session.query(exists().where(Courier.name == name)).scalar()

    @classmethod
    def try_add(cls, name):
        # no need to check exists in here because
        # the form has handled it and the model fields has unique=True
        new_cou = Courier(name=name)
        try:
            db.session.add(new_cou)
            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        q = Courier.query.with_entities(Courier.id, Courier.name)
        q = paginate_query(q, page_num, list_per_page)

        if order_by:
            q = q.order_by(order_by)

        c_list = q.all()

        if include_header:
            c_list.insert(0, tuple(x['name'] for x in q.column_descriptions))
        return c_list


class TransactionMedium(STModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_LENGTH), index=True, nullable=False, unique=True)
    sale_transactions = db.relationship('SaleTransaction', backref='transaction_medium', lazy='dynamic')

    @classmethod
    def check_exist(cls, name):
        return db.session.query(exists().where(TransactionMedium.name == name)).scalar()

    @classmethod
    def try_add(cls, name):
        new_tm = TransactionMedium(name=name)
        try:
            db.session.add(new_tm)
            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, **kwargs):
        q = TransactionMedium.query.with_entities(TransactionMedium.id, TransactionMedium.name)
        q = paginate_query(q, page_num, list_per_page)

        if order_by:
            q = q.order_by(order_by)

        tm_list = q.all()

        if include_header:
            tm_list.insert(0, tuple(x['name'] for x in q.column_descriptions))
        return tm_list


class PurchaseTransaction(STModel):
    id = db.Column(db.Integer, primary_key=True)
    items = db.relationship('Item', backref='purchase_transaction', lazy='dynamic',
                            cascade='save-update, merge, delete')
    transaction_date = db.Column(db.DateTime, index=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    notes = db.Column(db.String(NOTES_LENGTH))

    def __init__(self, transaction_date=None, supplier_id=None, notes=None):
        if transaction_date is None:
            self.transaction_date = datetime.now()
        else:
            self.transaction_date = transaction_date

        if not supplier_id:
            raise TypeError('supplier id cannot be empty for new purchase transaction')
        else:
            self.supplier_id = supplier_id

        self.notes = notes

    @utils.classproperty
    def total(cls):
        # there are two ways doing this
        q = db.session.query(func.count(Item.id)) \
            .filter(Item.purchase_transaction_id != None) \
            .group_by(Item.purchase_transaction_id, Item.item_type_id)
        # in here can use q.count() but apparently it is slower
        return len(q.all())
        # OR
        # q = db.session.query(func.count(distinct(Item.item_type_id)))\
        #     .filter(Item.purchase_transaction_id != None)\
        #     .group_by(Item.purchase_transaction_id)
        # return sum(x[0] for x in q.all())

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, ids=None, year=None, month=None, day=None):

        qty_label = 'quantity'
        individual_price_label = 'price_(each)'
        total_price_label = 'total_price'

        # initial query
        q = db.session.query(Item.purchase_transaction_id.label('id'),
                             ItemType.item_type,
                             PurchaseTransaction.transaction_date,
                             func.count(Item.id).label(qty_label),
                             Item.purchase_price.label(individual_price_label),
                             func.sum(Item.purchase_price).label(total_price_label),
                             Supplier.name.label('supplier'),
                             PurchaseTransaction.notes)

        # filter based on param
        # id is only 1, so if it is not None just skip other filters
        if ids:
            q = q.filter(Item.purchase_transaction_id.in_(ids))
        else:
            # any is useful for checking ['']
            # http://stackoverflow.com/questions/11191264/python-how-to-check-list-doest-contain-any-value

            if year and any(year):
                q = q.filter(extract('year', PurchaseTransaction.transaction_date).in_(year))

            if month and any(month):
                q = q.filter(extract('month', PurchaseTransaction.transaction_date).in_(month))

            if day and any(day):
                q = q.filter(extract('day', PurchaseTransaction.transaction_date).in_(day))

        # finishing query
        q = q.join(ItemType, PurchaseTransaction, Supplier) \
            .group_by(Item.purchase_transaction_id, Item.item_type_id)

        # I can use this to add the total row, but one problem is the date_time field needs to have valid date
        # also the order by needs to be placed last, so maybe it is better to just use python?
        # q = q.union_all(
        #     db.session.query(func.count(distinct(Item.purchase_transaction_id)),
        #                      func.count(distinct(Item.item_type_id)),
        #                      "'{}'".format(str(datetime.now())),
        #                      func.count(Item.id),
        #                      "'test2'",
        #                      func.sum(Item.purchase_price),
        #                      "'test3'").join(ItemType, PurchaseTransaction))

        q = q.order_by(PurchaseTransaction.transaction_date.desc())
        q = paginate_query(q, page_num, list_per_page)

        p_list = q.all()
        column_names = tuple(x['name'] for x in q.column_descriptions)

        # dynamically check where is total_price column is from column_names
        # add first column name 'TOTAL'
        # and the total_price_id in its respective column
        total_price_id = column_names.index(total_price_label)
        total_row = [''] * len(column_names)
        total_row[0] = 'TOTAL'
        total_row[total_price_id] = sum(x[total_price_id] for x in p_list)

        p_list.append(tuple(total_row))
        # append description last because there is sum previously in total_row
        p_list.insert(0, column_names)

        return p_list

    @classmethod
    def try_add(cls, date=None, supplier_id=None, notes=None, transaction_items=None):
        """
        Adding new transaction with date, notes and collections of items
        the expected format for the items should be dictionary
        with keys: purchase_price, item_type_id, supplier_id, quantity)
        """
        new_trans = PurchaseTransaction(transaction_date=date,
                                        supplier_id=supplier_id,
                                        notes=notes)

        try:
            db.session.add(new_trans)
            db.session.flush()

            if not cls.try_add_purchase_items(new_trans.id, transaction_items, False):
                return False

            db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False


    @classmethod
    def try_delete(cls, id, **kwargs):
        if super().try_delete(id, **kwargs):
            if not validate_transactions(cls, purchase_trans=True):
                cls.add_error('Transaction is deleted but fail to'
                              'validate transactions, there might be'
                              'transaction without items')
                return False
            return True
        else:
            return False

    @classmethod
    def get_purchase_items(cls, id):
        return db.session.query(func.count(Item.id).label('quantity'),
                                Item.item_type_id,
                                Item.purchase_price) \
            .filter(Item.purchase_transaction_id == id) \
            .group_by(Item.item_type_id)

    @classmethod
    def get_purchase_item_ids(cls, trans_id, item_type_id):
        return [i[0] for i in db.session.query(Item.id) \
            .filter(Item.purchase_transaction_id == trans_id) \
            .filter(Item.item_type_id == item_type_id).all()]

    @classmethod
    def try_delete_all_purchase_items(cls, trans_id, commit=False):
        items = cls.get(trans_id).items
        try:
            for item in items:
                db.session.delete(item)
                db.session.flush()

            if commit:
                db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False


    @classmethod
    def try_add_purchase_items(cls, trans_id,
                               transaction_items, commit=False):
        try:
            for trans_item in transaction_items:
                # check if it contains all the data needed
                # this is mainly for internal error from views to models
                if not ('quantity' in trans_item and
                        'purchase_price' in trans_item and
                        'item_type_id' in trans_item):
                    cls.add_error('transaction item missing required keys')
                    raise Exception('transaction item missing required keys')

                for i in range(trans_item['quantity']):
                    item = Item(purchase_price=trans_item['purchase_price'],
                                item_type_id=trans_item['item_type_id'],
                                purchase_transaction_id=trans_id)
                    db.session.add(item)
                    db.session.flush()

            if commit:
                db.session.commit()
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    # problem, if you delete everything and add everything
    # it will affect the sale transaction
    # that's why now it is going to check whether it should add
    # or delete item for the existing transaction
    @classmethod
    def try_edit_purchase_items(cls, trans_id, transaction_items, commit=False):
        for transaction_item in transaction_items:
            ids = list(map(int, transaction_item['ids'].split(',')))

            # update every ids until reaches total of new qty
            update_ids = ids[:transaction_item['quantity']]
            for id in update_ids:
                item = Item.get(id)
                item.item_type_id = transaction_item['item_type_id']
                item.purchase_price = transaction_item['purchase_price']
                db.session.add(item)
                db.session.flush()
                # flash('updated ids: {}'.format(id))

            # discard extra id after new qty in case new qty < old qty
            delete_ids = ids[transaction_item['quantity']:]
            for id in delete_ids:
                item = Item.get(id)
                db.session.delete(item)
                db.session.flush()
                # flash('deleted ids: {}'.format(id))

            # get new qty if total new qty is more than previous item
            new_qty = max(0, transaction_item['quantity'] - len(ids))
            if new_qty > 0:
                # flash('new qty: {}'.format(new_qty))
                items = transaction_item.copy()
                items['quantity'] = new_qty
                if not cls.try_add_purchase_items(trans_id, [items]):
                    return False

        if commit:
            db.session.commit()
        return True

        #     cls.add_error('testing editing purchase items')
        #     return False
        #
        # if cls.try_delete_all_purchase_items(trans_id, False) and \
        #     cls.try_add_purchase_items(trans_id, transaction_items, False):
        #     if commit:
        #         db.session.commit()
        #     return True
        # else:
        #     db.session.rollback()
        #     return False


class SaleTransaction(STModel):
    id = db.Column(db.Integer, primary_key=True)
    items = db.relationship('Item', backref='sale_transaction', lazy='dynamic')
    transaction_date = db.Column(db.DateTime, index=True, nullable=False)
    delivery_fee = db.Column(db.Integer, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))
    transaction_medium_id = db.Column(db.Integer, db.ForeignKey('transaction_medium.id'))
    notes = db.Column(db.String(NOTES_LENGTH))

    def __init__(self, transaction_date=None, customer_id=None,
                 courier_id=None, delivery_fee=None,
                 transaction_medium_id=None, notes=None):
        if transaction_date is None:
            self.transaction_date = datetime.now()
        else:
            self.transaction_date = transaction_date

        if customer_id is None:
            raise TypeError('customer_id is required')

        self.delivery_fee = delivery_fee
        self.customer_id = customer_id
        self.courier_id = courier_id
        self.transaction_medium_id = transaction_medium_id
        self.notes = notes

    @utils.classproperty
    def total(cls):
        # there are two ways doing this same as purchase transaction
        q = db.session.query(func.count(Item.id)) \
            .filter(Item.sale_transaction_id != None) \
            .group_by(Item.sale_transaction_id, Item.item_type_id)
        return len(q.all())

    @classmethod
    def get_list(cls, page_num=DEFAULT_PAGE_NUMBER,
                 list_per_page=DEFAULT_POSTS_PER_PAGE,
                 include_header=True,
                 order_by=None, ids=None, year=None, month=None, day=None):

        qty_label = 'quantity'
        individual_price_label = 'sale_price_(each)'
        total_sale_price_label = 'total_sale_price'
        total_purchase_price_label = 'total_purchase_price'
        profit_label = 'profit'
        delivery_fee_label = 'delivery_fee'

        # initial query
        q = db.session.query(Item.sale_transaction_id.label('sale_id'),
                             ItemType.item_type,
                             SaleTransaction.transaction_date,
                             func.count(Item.id).label(qty_label),
                             Item.sale_price.label(individual_price_label),
                             func.sum(Item.sale_price).label(total_sale_price_label),
                             func.sum(Item.purchase_price).label(total_purchase_price_label),
                             func.sum(Item.profit).label(profit_label),
                             Customer.name.label('customer'),
                             TransactionMedium.name.label('medium'),
                             Courier.name.label('courier'),
                             SaleTransaction.delivery_fee.label(delivery_fee_label),
                             SaleTransaction.notes
                             )

        # filter based on param
        # id is only 1, so if it is not None just skip other filters
        if ids:
            q = q.filter(Item.sale_transaction_id.in_(ids))
        else:
            # any is useful for checking ['']
            # http://stackoverflow.com/questions/11191264/python-how-to-check-list-doest-contain-any-value

            if year and any(year):
                q = q.filter(extract('year', SaleTransaction.transaction_date).in_(year))

            if month and any(month):
                q = q.filter(extract('month', SaleTransaction.transaction_date).in_(month))

            if day and any(day):
                q = q.filter(extract('day', SaleTransaction.transaction_date).in_(day))

        # finishing query
        # outer join for optional
        q = q.join(ItemType, SaleTransaction, PurchaseTransaction,
                   Customer) \
            .outerjoin(Courier, TransactionMedium) \
            .group_by(Item.sale_transaction_id, Item.item_type_id)

        q = q.order_by(SaleTransaction.transaction_date.desc())
        q = paginate_query(q, page_num, list_per_page)

        s_list = q.all()
        column_names = tuple(x['name'] for x in q.column_descriptions)

        # dynamically check where is total_price column is from column_names
        # add first column name 'TOTAL'
        # and the total_price_id in its respective column
        total_sale_price_id = column_names.index(total_sale_price_label)
        total_purchase_price_id = column_names.index(total_purchase_price_label)
        profit_id = column_names.index(profit_label)
        delivery_fee_id = column_names.index(delivery_fee_label)

        total_row = [''] * len(column_names)
        total_row[0] = 'TOTAL'
        total_row[total_sale_price_id] = sum(x[total_sale_price_id] for x in s_list)
        total_row[total_purchase_price_id] = sum(x[total_purchase_price_id] for x in s_list)
        total_row[profit_id] = sum(x[profit_id] for x in s_list)
        total_row[delivery_fee_id] = db.session.query(
            func.sum(SaleTransaction.delivery_fee))\
            .scalar()

        s_list.append(tuple(total_row))
        # append description last because there is sum previously in total_row
        s_list.insert(0, column_names)
        return s_list

    @classmethod
    def try_add(cls, date=None, customer_id=None,
                courier_id=None, delivery_fee=None,
                transaction_medium_id=None, notes=None,
                transaction_items=None):
        """
        transaction_items should be a list of dict
        containing item_type_id, quantity
        """
        new = SaleTransaction(transaction_date=date, customer_id=customer_id,
                              courier_id=courier_id, delivery_fee=delivery_fee,
                              transaction_medium_id=transaction_medium_id, notes=notes)
        try:
            db.session.add(new)
            db.session.flush()
            if cls.try_add_sale_items(new.id, transaction_items, False):
                db.session.commit()
                return True

        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def get_sale_items(cls, id):
        return db.session.query(func.count(Item.id).label('quantity'),
                                Item.item_type_id,
                                Item.sale_price) \
            .filter(Item.sale_transaction_id == id) \
            .group_by(Item.item_type_id)

    @classmethod
    def try_delete_sale_items(cls, trans_id, commit=False):
        items = cls.get(trans_id).items
        try:
            # remove sale transaction id for the item
            for item in items:
                item.sale_transaction_id = None
                db.session.add(item)
                db.session.flush()

            if commit:
                db.session.commit()
                flash('commit deleting transaction item')
            return True
        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    @classmethod
    def try_add_sale_items(cls, trans_id, transaction_items, commit=False):
        try:
            for trans_item in transaction_items:
                if not ('item_type_id' in trans_item or
                                'quantity' in trans_item or
                                'sale_price' in trans_item):
                    cls.add_error('transaction item missing required keys')
                    raise Exception('transaction item missing required keys')

                # get items FIFO models
                items = Item.query.join(PurchaseTransaction) \
                    .filter(Item.sale_transaction_id == None) \
                    .filter(Item.item_type_id == trans_item['item_type_id']) \
                    .order_by(PurchaseTransaction.transaction_date, Item.id) \
                    .limit(trans_item['quantity'])

                # the quantity input is more than available items
                # this one is internal error
                if trans_item['quantity'] > items.count():
                    cls.add_error('The total input is exceeding total stock')
                    raise Exception('The total input is exceeding total stock')

                # for each item add sale transaction field
                for it in items:
                    it.sale_price = trans_item['sale_price']
                    it.sale_transaction_id = trans_id
                    db.session.add(it)
                    db.session.flush()

            if commit:
                db.session.commit()
            return True

        except Exception as e:
            cls.add_error(e)
            db.session.rollback()
            return False

    # TODO: Problem with total stock in the form
    @classmethod
    def try_edit_sale_items(cls, trans_id, transaction_items, commit=False):
        if cls.try_delete_sale_items(trans_id, False) and \
                cls.try_add_sale_items(trans_id, transaction_items, False):
            if commit:
                db.session.commit()
            return True
        else:
            db.session.rollback()
            return False