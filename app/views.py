from flask import render_template, flash, redirect, url_for, request
from app import app, db, models, forms
from datetime import datetime
from flask_paginate import Pagination
from app import utils
import config
from collections import namedtuple


# TODO add safe redirect

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}
    items = [
        {
            'item_type': {'item_type': 'book'},
            'date_purchase': '2016-01-26 10:00:00.000',
            'date_sold': None,
            'purchase_price': 5000,
            'sold_price': None,
            'profit': None,
            'supplier': 'SinarMas'
        },
        {
            'item_type': {'item_type': 'laptop'},
            'date_purchase': '2016-01-26 10:00:00.000',
            'date_sold': None,
            'purchase_price': 175000,
            'sold_price': None,
            'profit': None,
            'supplier': 'Toto'
        }

    ]
    return render_template('index.html', title='Home', user=user, items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        flash('Login requested for open ID= "{0}", remember_me={1}'.format(
            form.openid.data, str(form.remember_me.data)))
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form,
                           providers=app.config['OPENID_PROVIDERS'])


# ---------
# Utility Region
# ---------
def get_pagination(request, total, **kwargs):
    """
    Process pagination request by getting parameter
    and validate it, it will return the param in int type
    except 1 case if the param is equal 'ALL' it will retain it

    Then prepare the href for each link to replace/add page param to
    current url
    """
    # read request params
    page = request.args.get('page')
    page = int(page) if utils.is_int(page) else config.DEFAULT_PAGE_NUMBER

    per_page = request.args.get('per_page')

    # if this is not equal to ALL_IN_PAGE_KEYWORD
    # try convert to int
    if isinstance(per_page, str) and per_page == config.ALL_IN_PAGE_KEYWORD:
        per_page_strict_int = total
    else:
        per_page = int(per_page) if utils.is_int(per_page) else config.DEFAULT_POSTS_PER_PAGE
        per_page_strict_int = per_page

    # make redirect link for href
    # there is no parameter
    if '?' not in request.url:
        href = request.url + '?' + config.URL_PAGE_NUM + '={0}'
    # in case url ends with '?' without any parameter
    elif request.url.endswith('?'):
        href = request.url + config.URL_PAGE_NUM + '={0}'
    # there is parameter(s)
    else:
        params = request.url.split('&')
        page_param_found = False

        # for first param, it is merged with the url
        # so just replace it if it has desired parameter
        if '?' + config.URL_PAGE_NUM + '=' in params[0]:
            params[0] = params[0][:params[0].index('=') + 1] + '{0}'
            page_param_found = True

        # loop through all individual param
        going_to_be_removed = []
        for i in range(len(params)):
            # avoid index 0
            if i == 0:
                continue

            # the parameter match with description
            if params[i].startswith(config.URL_PAGE_NUM + '='):
                # if this is the first param, replace it with desired one
                if not page_param_found:
                    params[i] = config.URL_PAGE_NUM + '={0}'
                    page_param_found = True
                # if previous param has been found, remove all the next one
                else:
                    going_to_be_removed.append(params[i])

        # removing multiple same parameters
        for item in going_to_be_removed:
            params.remove(item)
        # there is no param which can be replaced, so add a new one
        if not page_param_found:
            params.append(config.URL_PAGE_NUM + '={0}')
        # put it back as complete url
        href = '&'.join(params)

    pagination = Pagination(css_framework='bootstrap3',
                            total=total,
                            href=href,
                            page=page,
                            per_page=per_page_strict_int,
                            **kwargs)

    per_page_form = forms.PerPageForm(pagination.per_page)
    returned_pagination = namedtuple('returned_pagination',
                                     ['pagination', 'page_num',
                                      'per_page', 'per_page_form'])

    return returned_pagination(pagination=pagination,
                               page_num=page,
                               per_page=per_page,
                               per_page_form=per_page_form)


def remove_table_redundancy(table, exception_index):
    """
    convert duplicated next row into ''
    enter exception_index to prevent removal of duplicate in certain column
    """
    total_clmn = len(table[0])
    data = [''] * total_clmn
    # row
    for i in range(len(table)):
        table[i] = list(table[i])
        # cell
        for j in range(len(table[i])):
            if j in exception_index:
                continue

            if table[i][j] == data[j]:
                table[i][j] = ''
            else:
                data[j] = table[i][j]

    return table


def flash_format(string, *args):
    flash(string.format(*args))


# ----------
# ADD Region
# ----------

# region Add Route
@app.route('/item-types/add', methods=['GET', 'POST'])
def add_item_type():
    form = forms.ItemTypeForm()

    if form.validate_on_submit():
        # success adding new stuff
        if models.ItemType.try_add(form.name_field.data):
            flash('Successfully added item type to database!')
        else:
            flash('Fail add new item type to database.\nError: {}' \
                  .format(models.ItemType.error))
        # prevent multiple form submission
        return redirect(url_for('add_item_type'))

    return render_template('add/add-item-type.html', form=form)


@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier():
    form = forms.ContactForm()
    if form.validate_on_submit():
        if models.Supplier.try_add(name=form.name.data,
                                   contact=form.contact.data,
                                   address=form.address.data):
            flash('Successfully added new supplier')
        else:
            flash('Fail to add new supplier to database.\nError: {}' \
                  .format(models.Supplier.error))
        # prevent multiple form submission
        return redirect(url_for('add_supplier'))

    return render_template('add/add-supplier.html', form=form)


@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    form = forms.ContactForm()
    if form.validate_on_submit():
        if models.Customer.try_add(name=form.name.data,
                                   contact=form.contact.data,
                                   address=form.address.data):
            flash('Successfully added new customer')
        else:
            flash('Fail to add new customer to database.\nError: {}' \
                  .format(models.Customer.error))

        return redirect(url_for('add_customer'))

    return render_template('add/add-customer.html', form=form)


@app.route('/couriers/add', methods=['GET', 'POST'])
def add_courier():
    form = forms.CourierForm()

    if form.validate_on_submit():
        if models.Courier.try_add(name=form.name_field.data):
            flash('Successfully added new courier')
        else:
            flash('Fail to add new courier to database.\nError: {}' \
                  .format(models.Courier.error))

        return redirect(url_for('add_courier'))

    return render_template('add/add-courier.html', form=form)


@app.route('/transaction-mediums/add', methods=['GET', 'POST'])
def add_transaction_medium():
    form = forms.TransactionMediumForm()

    if form.validate_on_submit():
        if models.TransactionMedium.try_add(name=form.name_field.data):
            flash('Successfully added new transaction medium')
        else:
            flash('Fail to add new transaction medium to database.\nError: {}' \
                  .format(models.TransactionMedium.error))

        return redirect(url_for('add_transaction_medium'))

    return render_template('add/add-transaction-medium.html', form=form)


@app.route('/purchase-transactions/add', methods=['GET', 'POST'])
def add_purchase_transaction():
    # form = forms.PurchaseTransactionForm(forms.ItemPurchaseForm, 'Purchase')
    form = forms.PurchaseTransactionForm()

    if form.validate_on_submit():
        dt = datetime(form.yyyy.data, form.MM.data, form.dd.data,
                      form.HH.data, form.mm.data, form.ss.data)

        # recreating dictionary to avoid dependency between form and models
        items = [{'purchase_price': x.purchase_price.data,
                  'item_type_id': x.item_type.data,
                  'quantity': x.quantity.data}
                 for x in form.transaction_items]

        if models.PurchaseTransaction.try_add(date=dt, supplier_id=form.supplier_id.data,
                                              notes=form.notes.data,
                                              transaction_items=items):
            flash('Successfully added a new purchase transaction')
        else:
            flash('Fail to add new purchase transaction,\nError: {}' \
                  .format(models.PurchaseTransaction.error))
        return redirect(url_for('add_purchase_transaction'))

    return render_template('add/add-purchase-transaction.html', form=form)


@app.route('/sale-transactions/add', methods=['GET', 'POST'])
def add_sale_transaction():
    form = forms.SaleTransactionForm()

    if form.validate_on_submit():
        dt = datetime(form.yyyy.data, form.MM.data, form.dd.data,
                      form.HH.data, form.mm.data, form.ss.data)

        items = [{'item_type_id': x.item_stock.data,
                  'quantity': x.quantity.data,
                  'sale_price': x.sale_price.data}
                 for x in form.transaction_items]

        if models.SaleTransaction.try_add(date=dt, delivery_fee=form.delivery_fee.data,
                                          customer_id=form.customer_id.data, courier_id=form.courier_id.data,
                                          transaction_medium_id=form.transaction_medium_id.data,
                                          notes=form.notes.data,
                                          transaction_items=items):
            flash('Successfully added new Sale Transaction')
        else:
            flash('Fail to add new sale transaction, might be internal error, \nError: {}' \
                  .format(models.SaleTransaction.error))

        return redirect(url_for('add_sale_transaction'))

    return render_template('add/add-sale-transaction.html', form=form)


# endregion

# region Edits

@app.route('/item-types/edit', methods=['GET', 'POST'])
@app.route('/item-types/edit/<id>', methods=['GET', 'POST'])
def edit_item_type(id=None):
    if not id:
        return redirect(url_for(item_types.__name__))

    item_type = models.ItemType.get(id)
    if not item_type:
        return redirect(url_for(item_types.__name__))

    # in construction, wtforms also receive input from request
    # and override the default values
    # http://stackoverflow.com/questions/16327141/why-wont-a-simple-dictionary-populate-obj-properly-for-form-myformobj-dict
    data = {'name_field': item_type.item_type}
    form = forms.ItemTypeForm(**data)

    if request.method == 'POST':
        form.check_exist = False
        if form.validate_on_submit():
            item_type.item_type = form.name_field.data
            models.ItemType.update(item_type)
            flash_format('Successfully edited {}', item_type.item_type)
            return redirect(url_for(item_types.__name__))

    return render_template('edit/edit-item-type.html', form=form)


@app.route('/suppliers/edit', methods=['GET', 'POST'])
@app.route('/suppliers/edit/<id>', methods=['GET', 'POST'])
def edit_supplier(id=None):
    if not id:
        return redirect(url_for(suppliers.__name__))

    supplier = models.Supplier.get(id)
    if not supplier:
        return redirect(url_for(suppliers.__name__))

    form = forms.ContactForm(obj=supplier)

    if request.method == 'POST':
        if form.validate_on_submit():
            supplier.name = form.name.data
            supplier.contact = form.contact.data
            supplier.address = form.address.data
            models.ItemType.update(supplier)
            flash_format('Successfully edited {}', supplier.name)
            return redirect(url_for(suppliers.__name__))

    return render_template('edit/edit-supplier.html', form=form)


@app.route('/customers/edit', methods=['GET', 'POST'])
@app.route('/customers/edit/<id>', methods=['GET', 'POST'])
def edit_customer(id=None):
    if not id:
        return redirect(url_for(customers.__name__))

    customer = models.Customer.get(id)
    if not customer:
        return redirect(url_for(customers.__name__))

    form = forms.ContactForm(obj=customer)

    if request.method == 'POST':
        if form.validate_on_submit():
            customer.name = form.name.data
            customer.contact = form.contact.data
            customer.address = form.address.data
            models.ItemType.update(customer)
            flash_format('Successfully edited {}', customer.name)
            return redirect(url_for(customers.__name__))

    return render_template('edit/edit-customer.html', form=form)


@app.route('/couriers/edit', methods=['GET', 'POST'])
@app.route('/couriers/edit/<id>', methods=['GET', 'POST'])
def edit_courier(id=None):
    if not id:
        return redirect(url_for(couriers.__name__))

    courier = models.Courier.get(id)
    if not courier:
        return redirect(url_for(couriers.__name__))

    data = {'name_field': courier.name}
    form = forms.CourierForm(**data)

    if request.method == 'POST':
        form.check_exist = False
        if form.validate_on_submit():
            courier.name = form.name_field.data
            models.Courier.update(courier)
            flash_format('Successfully edited {}', courier.name)
            return redirect(url_for(couriers.__name__))

    return render_template('edit/edit-courier.html', form=form)


@app.route('/transaction-mediums/edit', methods=['GET', 'POST'])
@app.route('/transaction-mediums/edit/<id>', methods=['GET', 'POST'])
def edit_transaction_medium(id=None):
    if not id:
        return redirect(url_for(transaction_mediums.__name__))

    tm = models.TransactionMedium.get(id)
    if not tm:
        return redirect(url_for(transaction_mediums.__name__))

    data = {'name_field': tm.name}
    form = forms.TransactionMediumForm(**data)

    if request.method == 'POST':
        form.check_exist = False
        if form.validate_on_submit():
            tm.name = form.name_field.data
            models.TransactionMedium.update(tm)
            flash_format('Successfully edited {}', tm.name)
            return redirect(url_for(transaction_mediums.__name__))

    return render_template('edit/edit-transaction-medium.html', form=form)


@app.route('/purchase-transactions/edit', methods=['GET', 'POST'])
@app.route('/purchase-transactions/edit/<id>', methods=['GET', 'POST'])
def edit_purchase_transaction(id=None):
    if not id:
        return redirect(url_for(purchase_transactions.__name__))

    pt = models.PurchaseTransaction.get(id)
    if not pt:
        return redirect(url_for(purchase_transactions.__name__))

    data = {'yyyy': pt.transaction_date.year,
            'MM': pt.transaction_date.month,
            'dd': pt.transaction_date.day,
            'HH': pt.transaction_date.hour,
            'mm': pt.transaction_date.minute,
            'ss': pt.transaction_date.second,
            'notes': pt.notes }

    form = forms.PurchaseTransactionForm(**data)

    if request.method == 'GET':
        form.supplier_id.data = pt.supplier_id
        form.transaction_items.min_entries = pt.items.count()
        form.transaction_items.pop_entry()

        for item in models.PurchaseTransaction.get_purchase_items(id):
            pt_item = forms.ItemPurchaseForm()
            pt_item.item_type = item.item_type_id
            pt_item.purchase_price = item.purchase_price
            pt_item.quantity = item.quantity
            ids = models.PurchaseTransaction.get_purchase_item_ids(id, item.item_type_id)
            pt_item.ids = ','.join((str(x) for x in ids))

            form.transaction_items.append_entry(pt_item)
    else: # POST
        if form.validate_on_submit():
            pt.transaction_date = datetime(form.yyyy.data, form.MM.data, form.dd.data,
                                           form.HH.data, form.mm.data, form.ss.data)
            pt.supplier_id = form.supplier_id.data
            pt.notes = form.notes.data

            items = [{'purchase_price': x.purchase_price.data,
                      'item_type_id': x.item_type.data,
                      'quantity': x.quantity.data,
                      'ids': x.ids.data}
                     for x in form.transaction_items]

            if models.PurchaseTransaction.try_edit_purchase_items(id, items):
                models.PurchaseTransaction.update(pt)
                flash_format('Successfully edited purchase transaction')
                return redirect(url_for(purchase_transactions.__name__))
            else:
                flash_format('Fail to edit purchase transaction: {}',
                             models.PurchaseTransaction.error)

    return render_template('edit/edit-purchase-transaction.html', form=form)


@app.route('/sale-transactions/edit', methods=['GET', 'POST'])
@app.route('/sale-transactions/edit/<id>', methods=['GET', 'POST'])
def edit_sale_transaction(id=None):
    if not id:
        return redirect(url_for(sale_transactions.__name__))

    st = models.SaleTransaction.get(id)
    if not st:
        return redirect(url_for(sale_transactions.__name__))

    data = {'yyyy': st.transaction_date.year,
            'MM': st.transaction_date.month,
            'dd': st.transaction_date.day,
            'HH': st.transaction_date.hour,
            'mm': st.transaction_date.minute,
            'ss': st.transaction_date.second,
            'delivery_fee': st.delivery_fee,
            'notes': st.notes}

    form = forms.SaleTransactionForm(**data)

    if request.method == 'GET':
        form.transaction_items.min_entries = st.items.count()
        form.transaction_items.pop_entry()

        form.customer_id.data = st.customer_id
        form.courier_id.data = st.courier_id
        form.transaction_medium_id.data = st.transaction_medium_id

        for item in models.SaleTransaction.get_sale_items(id):
            st_item = forms.ItemSaleForm()
            st_item.item_stock = item.item_type_id
            st_item.sale_price = item.sale_price
            st_item.quantity = item.quantity  # TODO include the selected one

            form.transaction_items.append_entry(st_item)
    else: # POST
        if form.validate_on_submit():
            st.transaction_date = datetime(form.yyyy.data, form.MM.data, form.dd.data,
                                           form.HH.data, form.mm.data, form.ss.data)

            st.delivery_fee = form.delivery_fee.data
            st.customer_id = form.customer_id.data

            if form.courier_id.data != config.NULL_INTEGER:
                st.courier_id = form.courier_id.data

            if form.courier_id.data != config.NULL_INTEGER:
                st.transaction_medium_id = form.transaction_medium_id.data

            st.notes = form.notes.data

            items = [{'item_type_id': x.item_stock.data,
                      'quantity': x.quantity.data,
                      'sale_price': x.sale_price.data}
                     for x in form.transaction_items]

            if models.SaleTransaction.try_edit_sale_items(id, items):
                models.SaleTransaction.update(st)
                flash_format('Successfully edited sale transaction')
                return redirect(url_for(sale_transactions.__name__))
            else:
                flash_format('Fail to edit sale transaction: {}',
                             models.SaleTransaction.error)


    return render_template('edit/edit-sale-transaction.html', form=form)


# endregion

# ----------
# VIEW Region
# ----------

# region View Route
def render_basic_table_view(request=None,
                            total=None,
                            get_table_func=None,
                            record_name=None,
                            html_path=None,
                            delete_func=None,
                            edit_func=None):
    if (not request or not get_table_func or
            not record_name or not html_path):
        # dont put total because sometimes there is no item
        raise TypeError('Missing required keyword arguments')

    pagination_set = get_pagination(request=request,
                                    total=total,
                                    record_name=record_name)

    table_list = get_table_func(page_num=pagination_set.page_num,
                                list_per_page=pagination_set.per_page)

    # if there is delete func provided,
    # add new column for delete
    if delete_func and edit_func:
        add_extra_column(table_list, delete_func, edit_func)

    # XOR operator
    if bool(delete_func) ^ bool(edit_func):
        raise ValueError('If you provide delete_func for extra column '
                         'it should be accompanied with edit_func and vice versa')

    return render_template(html_path, table=table_list,
                           pagination=pagination_set.pagination,
                           per_page_form=pagination_set.per_page_form)


def get_func_name(func):
    if isinstance(func, str):
        return func
    elif callable(func):
        return func.__name__
    else:
        raise TypeError("func param should only be function or string")


def add_extra_column(table_list, delete_func, edit_func):
    delete_func = get_func_name(delete_func)
    edit_func = get_func_name(edit_func)

    for i in range(len(table_list)):
        if (isinstance(table_list[i][0], int)):
            delete_form = forms.IdForm(table_list[i][0],
                                       url_for(delete_func))
            edit_form = forms.IdForm(table_list[i][0],
                                     url_for(edit_func))

            delete_template = render_template('form_templates/delete-form.html',
                                              delete_form=delete_form)
            edit_template = render_template('form_templates/edit-form.html',
                                            edit_form=edit_form)

            table_list[i] += (('{}{}'.format(edit_template, delete_template)),)
        else:
            table_list[i] += ('',)


@app.route('/items', methods=['GET'])
def items():
    return render_basic_table_view(request=request,
                                   total=models.Item.total,
                                   get_table_func=models.Item.get_list,
                                   record_name='Item',
                                   html_path='view/items.html')


@app.route('/item-types', methods=['GET'])
def item_types():
    return render_basic_table_view(request=request,
                                   total=models.ItemType.total,
                                   get_table_func=models.ItemType.get_list,
                                   record_name='Item Type',
                                   html_path='view/item-types.html',
                                   delete_func=delete_item_type,
                                   edit_func=edit_item_type)


@app.route('/item-stock', methods=['GET'])
def item_stock():
    return render_basic_table_view(request=request,
                                   total=models.Item.total_item_stock,
                                   get_table_func=models.Item.get_stock_list,
                                   record_name='Item Type',
                                   html_path='view/item-stock.html')


@app.route('/suppliers', methods=['GET'])
def suppliers():
    return render_basic_table_view(request=request,
                                   total=models.Supplier.total,
                                   get_table_func=models.Supplier.get_list,
                                   record_name='Supplier',
                                   html_path='view/suppliers.html',
                                   delete_func=delete_supplier,
                                   edit_func=edit_supplier)


@app.route('/customers', methods=['GET'])
def customers():
    return render_basic_table_view(request=request,
                                   total=models.Customer.total,
                                   get_table_func=models.Customer.get_list,
                                   record_name='Customer',
                                   html_path='view/customers.html',
                                   delete_func=delete_customer,
                                   edit_func=edit_customer)


@app.route('/couriers', methods=['GET'])
def couriers():
    return render_basic_table_view(request=request,
                                   total=models.Courier.total,
                                   get_table_func=models.Courier.get_list,
                                   record_name='Courier',
                                   html_path='view/couriers.html',
                                   delete_func=delete_courier,
                                   edit_func=edit_courier)


@app.route('/transaction-mediums', methods=['GET'])
def transaction_mediums():
    return render_basic_table_view(request=request,
                                   total=models.TransactionMedium.total,
                                   get_table_func=models.TransactionMedium.get_list,
                                   record_name='Transaction Medium',
                                   html_path='view/transaction-mediums.html',
                                   delete_func=delete_transaction_medium,
                                   edit_func=edit_transaction_medium)


@app.route('/purchase-transactions', methods=['GET', 'POST'])
@app.route('/purchase-transactions/<trans_id>', methods=['GET', 'POST'])
def purchase_transactions(trans_id=None):
    pagination_set = get_pagination(request=request,
                                    total=models.PurchaseTransaction.total,
                                    record_name='Transaction')

    form = forms.FilterTableForm()

    if trans_id:
        p_list = models.PurchaseTransaction \
            .get_list(ids=trans_id,
                      page_num=pagination_set.page_num,
                      list_per_page=pagination_set.per_page)
    else:
        p_list = models.PurchaseTransaction \
            .get_list(ids=request.args.getlist(config.URL_ID),
                      year=request.args.getlist(config.URL_YEAR),
                      month=request.args.getlist(config.URL_MONTH),
                      day=request.args.getlist(config.URL_DAY),
                      page_num=pagination_set.page_num,
                      list_per_page=pagination_set.per_page)

    add_extra_column(p_list, delete_purchase_transaction, edit_purchase_transaction)

    # right now filter form is using POST to do query
    # the reason I didn't use GET is because the CSRF token is on (probably need to turn it off)
    # and the submit_button value is included in the param
    # in the future if there is log in feature, this will be useful
    # if you use get this will be the url
    # http://xyz.com?csrf_token=xxx&value=xxx&year=xxx&month=xxx...
    if form.validate_on_submit():
        id_params = utils.map_csv_params(form.id.data)
        year_params = utils.map_csv_params(form.year.data)
        month_params = utils.map_csv_params(form.month.data)
        day_params = utils.map_csv_params(form.day.data)

        params = {
            config.URL_ID: id_params if any(id_params) else None,
            config.URL_YEAR: year_params if any(year_params) else None,
            config.URL_MONTH: month_params if any(month_params) else None,
            config.URL_DAY: day_params if any(day_params) else None
        }

        return redirect(url_for('purchase_transactions', **params))

    return render_template('view/purchase-transactions.html', table=p_list, form=form,
                           pagination=pagination_set.pagination,
                           per_page_form=pagination_set.per_page_form)


@app.route('/sale-transactions', methods=['GET', 'POST'])
@app.route('/sale-transactions/<sale_id>', methods=['GET', 'POST'])
def sale_transactions(sale_id=None):
    pagination_set = get_pagination(request=request,
                                    total=models.SaleTransaction.total,
                                    record_name='Transaction')

    form = forms.FilterTableForm()

    if sale_id:
        s_list = models.SaleTransaction \
            .get_list(ids=sale_id,
                      page_num=pagination_set.page_num,
                      list_per_page=pagination_set.per_page)
    else:
        s_list = models.SaleTransaction \
            .get_list(ids=request.args.getlist(config.URL_ID),
                      year=request.args.getlist(config.URL_YEAR),
                      month=request.args.getlist(config.URL_MONTH),
                      day=request.args.getlist(config.URL_DAY),
                      page_num=pagination_set.page_num,
                      list_per_page=pagination_set.per_page)

    add_extra_column(s_list, delete_sale_transaction, edit_sale_transaction)

    if form.validate_on_submit():
        id_params = utils.map_csv_params(form.id.data)
        year_params = utils.map_csv_params(form.year.data)
        month_params = utils.map_csv_params(form.month.data)
        day_params = utils.map_csv_params(form.day.data)

        params = {
            config.URL_ID: id_params if any(id_params) else None,
            config.URL_YEAR: year_params if any(year_params) else None,
            config.URL_MONTH: month_params if any(month_params) else None,
            config.URL_DAY: day_params if any(day_params) else None
        }

        return redirect(url_for('sale_transactions', **params))

    return render_template('view/sale-transactions.html', table=s_list, form=form,
                           pagination=pagination_set.pagination,
                           per_page_form=pagination_set.per_page_form)


# endregion

# ----------
# DELETE Region
# ----------

# region delete route

def view_delete(cls, redirect_func, request=None, id=None):
    """
    Delete for view URL using this generic method
    Each of route could just call this method instead
    implementing each own methods (because all the models
    share the same class, so the delete function is similar)

    Parameter id take priority over request
    """
    # in future do some validation if it can delete
    # e.g login, etc later on
    target_id = None

    if request:
        target_id = request.form.get(config.URL_ID)
    if id:
        target_id = id

    if not request and not id:
        raise TypeError("Either parameter request or id is required")

    if not target_id:
        return

    # if function
    if callable(redirect_func):
        redirect_func = redirect_func.__name__

    if not isinstance(redirect_func, str):
        raise TypeError('The redirect_func param can only be string or function')

    if cls.try_delete(target_id):
        flash('Successfully delete one {} with id: {}'.format(cls.__name__, target_id))
    else:
        flash('Fail to delete {} with id: {}'.format(cls.__name__, target_id))

    return redirect(url_for(redirect_func))


@app.route('/item-types/delete', methods=['POST'])
def delete_item_type():
    return view_delete(models.ItemType, item_types, request)


@app.route('/suppliers/delete', methods=['POST'])
def delete_supplier():
    return view_delete(models.Supplier, suppliers, request)


@app.route('/customers/delete', methods=['POST'])
def delete_customer():
    return view_delete(models.Customer, customers, request)


@app.route('/couriers/delete', methods=['POST'])
def delete_courier():
    return view_delete(models.Courier, couriers, request)


@app.route('/transaction-mediums/delete', methods=['POST'])
def delete_transaction_medium():
    return view_delete(models.TransactionMedium, transaction_mediums, request)


@app.route('/purchase-transactions/delete', methods=['POST'])
def delete_purchase_transaction():
    return view_delete(models.PurchaseTransaction, purchase_transactions, request)


@app.route('/sale-transactions/delete', methods=['POST'])
def delete_sale_transaction():
    return view_delete(models.SaleTransaction, sale_transactions, request)


# endregion

# ----------
# Errors Region
# ----------

# region delete route

@app.errorhandler(204)
def no_content_error(error):
    return render_template('errors/no-content-error.html')

# endregion
