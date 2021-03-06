
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os

# For password hashing
import hashlib
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, flash, request, render_template, g, redirect, Response, session, url_for
from random import randint
from sqlalchemy.sql.selectable import Select
from wtforms import Form, StringField, SubmitField, DecimalField, DateField, PasswordField, SelectField

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
DATABASEURI = "postgresql://fc2679:lucas123@34.73.36.248/project1" # Modify this with your own credentials you received from Joseph!


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request 
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
      g.conn = engine.connect()
    except:
      print("uh oh, problem connecting to database")
      import traceback; traceback.print_exc()
      g.conn = None

@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
      g.conn.close()
    except Exception as e:
      pass


def initialize_cart():
    if 'cart' not in session:
        session['cart'] = dict()
        session['itemcount'] = 0


def get_login():
    if 'username' in session:
        return session['username']
    else:
        None

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
    """
    initialize_cart()
    cursor = g.conn.execute("SELECT DISTINCT product_category FROM product")
    category = []
    for result in cursor:
      category.append(result['product_category'])  # can also be accessed using result[0]
    cursor.close()

    cursor = g.conn.execute("SELECT brand_name FROM brand")
    brand = []
    for result in cursor:
      brand.append(result['brand_name'])  # can also be accessed using result[0]
    cursor.close()

    context = dict(category=category, brand=brand, itemcount=session['itemcount'], login=get_login())

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


@app.route('/loginpost', methods=['POST'])
def loginpost():
    username = request.form['username']
    password = "md5" + hashlib.md5(request.form['password'].encode()).hexdigest()
    cursor = g.conn.execute("SELECT * FROM customer WHERE email = '{}' AND password = '{}'".format(username, password))
    if cursor.rowcount:
      cursor.close()
      session['username'] = username
      session['is_admin'] = False
      flash('Welcome to Booze.io!')
      return redirect(url_for('index'))
    else:
      cursor.close()
      cursor = g.conn.execute("SELECT * FROM employee WHERE email = '{}' AND password = '{}'".format(username, password))
      if cursor.rowcount:
        cursor.close()
        session['username'] = username
        session['is_admin'] = True
        flash('Welcome to Booze.io admin!')
        return redirect(url_for('admin_product'))
    cursor.close()
    flash('Wrong email or password. Click on signup to signup.')
    return redirect(url_for('login'))


# Signup and edit
class SignupForm(Form):
      email = StringField('Email (this is your username): ')
      password = PasswordField('Password: ')
      reenterpassword = PasswordField('Re-enter password')
      firstname = StringField('First name: ')
      lastname = StringField('Last name: ')
      dob = StringField('Date of Birth yyyy-mm-dd (you certify that you are 21 years or older): ')
      submit = SubmitField('Submit')    


@app.route('/signuppost', methods=['POST'])
def signuppost():
    username = request.form['email']
    password1 = request.form['password']
    password2 = request.form['reenterpassword']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    dob = request.form['dob']
    if ((password1 != password2) or ('@' not in username or '.' not in username) or
        (len(dob) != 10 or dob[4] != '-' or dob[7] != '-') or (dob[:4] > '2000')):
      flash('One of your details is incorrect. Try again.')
      return redirect(url_for('signup'))
    passhash = hashlib.md5(password1.encode()).hexdigest()
    details = g.conn.execute("select * from customer where email = '{}'".format(get_login())).fetchone()
    if details is not None:
      g.conn.execute("UPDATE customer SET first_name = '{}', last_name = '{}', email = '{}', dob = '{}', password = '{}' WHERE customer_id = {}"
        .format(firstname, lastname, username, dob, passhash, details['customer_id']))
      flash('Update successful')
    else:
      g.conn.execute("INSERT INTO customer (first_name, last_name, email, dob, password) VALUES ('{}', '{}', '{}', {}, '{}')"
        .format(firstname, lastname, username, dob, passhash))
      flash('Welcome to Booze.io')
    session['username'] = username
    session['is_admin'] = False
    return redirect(url_for('index'))


@app.route('/logoutpost', methods=['POST'])
def logoutpost():
    keys = list(session.keys())
    for k in keys:
        del session[k]
    flash('You\'ve successfully signed out.')
    return redirect(url_for('index'))


@app.route('/login')
def login():
    initialize_cart()
    if get_login():
        flash('You\'re already logged in')
        return redirect(url_for('index'))
    return render_template('login.html', itemcount=session['itemcount'], login=get_login())


@app.route('/signup')
def signup():
    initialize_cart()
    form = SignupForm(request.form)
    edit = False
    if get_login():
        details = g.conn.execute("select * from customer where email = '{}'".format(get_login())).fetchone()
        form.email.data = details['email']
        form.firstname.data = details['first_name']
        form.lastname.data = details['last_name']
        form.dob.data = details['dob']
        edit = True
    return render_template('signup.html', itemcount=session['itemcount'], edit=edit, form=form)


@app.route('/cart', methods=['POST', 'GET'])
def cart():
    initialize_cart()
    if not get_login():
        flash('Login/Signup to access cart')
        return redirect(url_for('login'))
    if 'product_id' in request.args:
        product_id = request.args['product_id']
        session['cart'][product_id] -= 1
        if session['cart'][product_id] == 0:
            del session['cart'][product_id]
        session['itemcount'] -= 1
    products = []
    total, discount = 0., 0.
    for k, v in session['cart'].items():
        row = g.conn.execute(
            "select p.product_id, p.product_name, p.unit_of_measure, p.item_price, p.package_quantity, p.region, p.country, p.color, p.description, b.brand_name, b.description as brand_description from product p left join brand b on b.brand_id = p.brand_id where p.product_id = {}".format(k)
        ).fetchall()
        row = dict(row[0])
        row['count'] = v
        row['init_price'] = round(float(row['item_price']) * int(v), 2)
        row['discount'] = 0.0
        if int(v) >= 3:
            row['discount'] = round(int(v)//3., 2)
        discount += row['discount']
        row['final_price'] = row['init_price'] - row['discount']
        products.append(row)
        total += row['final_price']
    session['discount'] = round(discount, 2)
    session['total'] = total = round(total, 2)
    session['tax'] = tax = round(0.04 * total, 2)
    session['total_post_tax'] = total_post_tax = round(total + tax, 2)
    return render_template('cart.html', products=products, total=total, 
                                        tax=tax, total_post_tax=total_post_tax)


# Signup and edit
class AddressForm(Form):
      addressid = StringField('Address ID: ')
      firstname = StringField('First name: ')
      lastname = StringField('Last name: ')
      address1 = StringField('Address Line 1: ')
      address2 = StringField('Address Line 2: ')
      city = StringField('City: ')
      state = StringField('State (XX): ')
      zips = StringField('Zip: ')
      phone = StringField('Phone (xxx-xxx-xxxx): ')
      company = StringField('Company: ')
      shipping = StringField('Shipping: ')
      billing = StringField('Billing: ')

@app.route('/address', methods=['POST', 'GET'])
def address():
      if not get_login():
          return redirect(url_for('index'))
    
      if request.method == 'POST':
          if 'billing' in request.form :
              if request.form['billing'] != "None":
                  session['bills'] = int(request.form['billing'])
                  flash("Billing address updated")
          elif 'shipping' in request.form:
              if request.form['shipping'] != "None":
                  session['ships'] = int(request.form['shipping'])
                  flash("Shipping address updated")
          elif 'address_id' in request.form:
              if request.form['address_id'] != "None":
                  g.conn.execute("UPDATE address SET first_name = '{}', last_name = '{}', address1 = '{}', address2 = '{}', city = '{}', state = '{}', zip = '{}', phone = '{}', company = '{}' WHERE address_id = {}"
                      .format(request.form['firstname'], request.form['lastname'], request.form['address1'], request.form['address2'], request.form['city'], request.form['state'], request.form['zips'], request.form['phone'], request.form['company'], request.form['address_id']))
                  flash("Address updated successfully")
              else:
                  if request.form['firstname'] != '' and request.form['lastname'] != '' and request.form['address1'] != '':
                      g.conn.execute("INSERT INTO address (first_name, last_name, address1, address2, city, state, zip, phone, company) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')"
                          .format(request.form['firstname'], request.form['lastname'], request.form['address1'], request.form['address2'], request.form['city'], request.form['state'], request.form['zips'], request.form['phone'], request.form['company']))
                      addr_id = g.conn.execute("SELECT address_id from address WHERE first_name = '{}' AND last_name = '{}' AND address1 = '{}' AND address2 = '{}' AND city = '{}' AND state = '{}' AND zip = '{}' AND phone = '{}' AND company = '{}'"
                          .format(request.form['firstname'], request.form['lastname'], request.form['address1'], request.form['address2'], request.form['city'], request.form['state'], request.form['zips'], request.form['phone'], request.form['company'])).fetchone()
                      user = g.conn.execute("SELECT customer_id FROM customer WHERE email = '{}'".format(get_login())).fetchone()
                      g.conn.execute("INSERT INTO customer_lives (customer_id, address_id, is_active) VALUES ({}, {}, False)".format(user['customer_id'], addr_id['address_id']))
                      flash("Address added successfully")
      user = g.conn.execute("SELECT customer_id FROM customer WHERE email = '{}'".format(get_login())).fetchone()
      addresses = g.conn.execute("SELECT * from address, customer_lives WHERE address.address_id = customer_lives.address_id AND customer_lives.customer_id = {}".format(user['customer_id'])).fetchall()
      addresses_list = []
      for a in addresses:
          row = dict(a)
          form = AddressForm()
          form.addressid.data = row['address_id']
          form.firstname.data = row['first_name']
          form.lastname.data = row['last_name']
          form.address1.data = row['address1']
          form.address2.data = row['address2']
          form.city.data = row['city']
          form.state.data = row['state']
          form.zips.data = row['zip']
          form.phone.data = row['phone']
          form.company.data = row['company']
          form.shipping.data = row['is_active'] if 'ships' not in session else (session['ships'] == int(row['address_id'])) 
          form.billing.data = row['is_active'] if 'bills' not in session else (session['bills'] == int(row['address_id']))
          if form.shipping.data == "True":
            session['ships'] = int(row['address_id'])
          if form.billing.data == "True":
            session['bills'] = int(row['address_id'])
          addresses_list.append(form)
      addresses_list.append(AddressForm())
      ships = None if 'ships' not in session else session['ships']
      bills = None if 'bills' not in session else session['bills']
      return render_template('address.html', addresses_list=addresses_list, ships=ships, bills=bills)


class PaymentForm(Form):
      payment_method = SelectField('Payment Method: ', choices=[(1, 'CARD'), (2, 'BANK')])
      credit_card = StringField('Credit Card Number: ')
      expiration_date = StringField('Expiration Date (YYYY-MM-DD): ')
      cvv2 = StringField('CVV2: ')
      submit = SubmitField('Submit')

@app.route('/payment', methods=['POST', 'GET'])
def payment():
      if 'username' not in session and not session['is_admin']:
            return redirect(url_for('index'))

      form = PaymentForm(request.form)

      if request.method == 'POST':
        payment_method = request.form['payment_method']
        credit_card = request.form['credit_card']
        expiration_date = request.form['expiration_date']
        cvv2 = request.form['cvv2']

        # One transaction
        with g.conn.begin():
            user_id = g.conn.execute("SELECT customer_id FROM customer WHERE email = '{}'".format(get_login())).fetchone()['customer_id']
            g.conn.execute("INSERT INTO orders (customer_id, bills_to, ships_to, order_number, discount, tax, total, is_void) VALUES ({}, {}, {}, '{}', {}, {}, {}, False)"
              .format(user_id, session['bills'], session['ships'], randint(1000000001, 9999999999), session['discount'], session['tax'], session['total_post_tax']))
            order_id = g.conn.execute("SELECT order_id FROM orders WHERE customer_id = {} ORDER BY order_id DESC".format(user_id)).fetchone()['order_id']
            g.conn.execute("INSERT INTO payment (order_id, payment_method, payment_amount, payment_status, credit_card, expiration_date, cvv2) VALUES ({}, '{}', {}, 'SUCCESS', '{}','{}', {})"
              .format(order_id, payment_method, session['total_post_tax'], credit_card, expiration_date, cvv2))
            for k, v in session['cart'].items():
                price = g.conn.execute("select item_price from product where product_id = {}".format(int(k))).fetchone()['item_price']
                discount = round(v/3, 2);
                g.conn.execute("INSERT INTO order_items (order_id, product_id, quantity, price, discount) VALUES ({}, {}, {}, {}, {})"
                  .format(order_id, int(k), v, price, discount))
            addr = g.conn.execute("select address_id from customer_lives where customer_id = {}".format(user_id)).fetchall()
            for a in addr:
                g.conn.execute("UPDATE customer_lives SET is_active = False WHERE address_id = {}".format(a[0]))
            g.conn.execute("UPDATE customer_lives SET is_active = True WHERE address_id = {}".format(session['ships']))
            g.conn.execute("INSERT INTO shipment (order_id) VALUES ({})".format(order_id))

        keys = list(session.keys())
        for k in keys:
            if k not in ('username', 'is_admin'):
                del session[k]

        flash('Payment Successful', 'success')
        return redirect('/orders')
      
      return render_template('payment.html', form=form, amount=session['total_post_tax'])

@app.route('/orders')
def orders():
    initialize_cart()
    if not get_login():
        flash('Login to see order history')
        return redirect(url_for('login'))

    result = g.conn.execute('select * from customer where email = %s', [get_login()])
    customer = result.fetchone()
    customer_id = customer.customer_id

    o = g.conn.execute('select distinct o.order_id, o.order_number, o.customer_id, o.total, o.tax, o.discount, o.is_void, s.carrier, s.tracking_number, s.ship_date, s.delivered_date from orders o left join shipment s on s.order_id = o.order_id WHERE o.customer_id = %s ORDER BY o.order_id DESC', [customer_id])
    orders = o.fetchall()

    return render_template('orders.html', itemcount=session['itemcount'], login=get_login(), customer=customer, orders=orders)
      
@app.route('/order/<int:order_id>')
def order_details(order_id):
    initialize_cart()

    if not get_login():
        flash('Login to see order details')
        return redirect(url_for('login'))

    result = g.conn.execute('select distinct o.order_id, o.order_number, o.customer_id, c.first_name, c.last_name, c.email, o.total, o.tax, o.discount, o.is_void, s.carrier, s.tracking_number, s.ship_date, s.delivered_date, p.payment_method, p.payment_status, p.credit_card, p.expiration_date from orders o inner join customer c on c.customer_id = o.customer_id left join shipment s on s.order_id = o.order_id left join payment p on p.order_id = o.order_id WHERE o.order_id = %s', [order_id])
    order = result.fetchone()

    b = g.conn.execute('select distinct o.order_id, bill.first_name, bill.last_name, bill.address1, bill.address2, bill.city, bill.state, bill.zip, bill.phone, bill.company from orders o inner join address bill on bill.address_id = o.bills_to WHERE o.order_id = %s', [order_id])
    bill = b.fetchone()

    s = g.conn.execute('select distinct o.order_id, ship.first_name, ship.last_name, ship.address1, ship.address2, ship.city, ship.state, ship.zip, ship.phone, ship.company from orders o inner join address ship on ship.address_id = o.ships_to WHERE o.order_id = %s', [order_id])
    ship = s.fetchone()

    od = g.conn.execute('select distinct od.order_id, od.product_id, od.quantity, od.price, od.discount, p.brand_id, p.product_name, b.brand_name, p.product_category, p.upc, p.unit_of_measure, p.region, p.country, p.color from order_items od inner join product p on p.product_id = od.product_id left join brand b on b.brand_id = p.brand_id WHERE od.order_id = %s', [order_id])
    order_details = od.fetchall()

    return render_template('order_details.html', login=get_login(), order=order, order_details=order_details, bill=bill, ship=ship)
      

@app.route('/category/<string:category>', methods=['POST', 'GET'])
def category(category):
    initialize_cart()
    if 'product_id' in request.args:
        product_id = request.args['product_id']
        if product_id in session['cart']:
            session['cart'][product_id] += 1
        else:
            session['cart'][product_id] = 1
        session['itemcount'] += 1
    products = g.conn.execute(
        "select p.product_id, p.product_name, p.unit_of_measure, p.item_price, p.package_quantity, p.region, p.country, p.color, p.description, b.brand_name, b.description as brand_description from product p left join brand b on b.brand_id = p.brand_id where p.product_category = '{}'".format(category)
    ).fetchall()
    products = [dict(row) for row in products]
    for product in products:
        product['count'] = session['cart'][str(product['product_id'])] if str(product['product_id']) in session['cart'] else 0
    return render_template('category.html', products=products, category=category, itemcount=session['itemcount'], login=get_login())


@app.route('/brand/<string:brand>', methods=['POST', 'GET'])
def brand(brand):
    initialize_cart()
    if 'product_id' in request.args:
        product_id = request.args['product_id']
        if product_id in session['cart']:
            session['cart'][product_id] += 1
        else:
            session['cart'][product_id] = 1
        session['itemcount'] += 1
    products = g.conn.execute(
        "select p.product_id, p.product_name, p.product_category, p.unit_of_measure, p.item_price, p.package_quantity, p.region, p.country, p.color, p.description, b.brand_name, b.description as brand_description from product p left join brand b on b.brand_id = p.brand_id where b.brand_name = '{}'".format(brand)
    ).fetchall()
    products = [dict(row) for row in products]
    for product in products:
        product['count'] = session['cart'][str(product['product_id'])] if str(product['product_id']) in session['cart'] else 0
    return render_template('brand.html', products=products, brand=brand, itemcount=session['itemcount'], login=get_login())


@app.route('/admin/product')
def admin_product():
      if 'username' not in session or (not session['is_admin']):
        return redirect(url_for('index'))
      products = g.conn.execute(
          'select p.product_id, p.product_name, p.product_category, p.cur_size, p.upc, p.unit_of_measure, p.buy_price_per_unit, p.item_price, p.package_quantity, p.region, p.country, p.color, p.description, b.brand_id, b.brand_name, b.description as brand_description, b.brand_poc from product p left join brand b on b.brand_id = p.brand_id'
      ).fetchall()
      return render_template('admin/product.html', products=products, itemcount=session['itemcount'])

class ProductForm(Form):
      product_name = StringField('Product Name: ')
      product_category = StringField('Product Category: ')
      cur_size = StringField('Current Inventory: ')
      upc = StringField('UPC: ')
      unit_of_measure = StringField('Unit of Measure: ')
      buy_price_per_unit = DecimalField('Buy Price: ')
      item_price = StringField('Item Price: ')
      package_quantity = StringField('Package Quantity: ')
      region = StringField('Region: ')
      country = StringField('Country: ')
      color = StringField('Color: ')
      description = StringField('Description: ')
      brand_name = StringField('Brand Name: ')
      brand_description = StringField('Brand Description: ')
      brand_poc = StringField('Brand Point of Contact: ')
      submit = SubmitField('Submit')

@app.route('/admin/add_product', methods=['POST', 'GET'])
def admin_add_product():
      if 'username' not in session or not session['is_admin']:
        return redirect(url_for('index'))
      if request.method == 'POST':
        # Insert into brand table if brand does not already exist.
        brand_name = request.form['brand_name']
        brand_description = request.form['brand_description']
        brand_poc = request.form['brand_poc']
        g.conn.execute('INSERT INTO brand(brand_name, description, brand_poc) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', brand_name, brand_description, brand_poc)

        brands = g.conn.execute('SELECT brand_id FROM brand WHERE brand_name = %s', brand_name)
        for row in brands:
              brand_id = row[0]

        # Insert into product table if product does not already exist.
        product_name = request.form['product_name']
        product_category = request.form['product_category']
        cur_size = request.form['cur_size']
        upc = request.form['upc']
        unit_of_measure = request.form['unit_of_measure']
        buy_price_per_unit = request.form['buy_price_per_unit']
        item_price = request.form['item_price']
        package_quantity = request.form['package_quantity']
        region = request.form['region']
        country = request.form['country']
        color = request.form['color']
        description = request.form['description']

        g.conn.execute('INSERT INTO product(brand_id, product_name, product_category, cur_size, upc, unit_of_measure, buy_price_per_unit, item_price, package_quantity, region, country, color, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (product_name) DO NOTHING', brand_id, product_name, product_category, cur_size, upc, unit_of_measure, buy_price_per_unit, item_price, package_quantity, region, country, color, description)
        
        return redirect('/admin/product')

      return render_template('admin/add_product.html')

@app.route('/admin/edit/<int:product_id>', methods=['POST', 'GET'])
def admin_edit_product(product_id):
      if 'username' not in session or not session['is_admin']:
        return redirect(url_for('index'))
      result = g.conn.execute('SELECT * FROM product WHERE product_id = %s', [product_id])
      product = result.fetchone()

      # Get form
      form = ProductForm(request.form)

      # Populate the form with existing data
      form.product_name.data = product['product_name']
      form.product_category.data = product['product_category']
      form.cur_size.data = product['cur_size']
      form.upc.data = product['upc']
      form.unit_of_measure.data = product['unit_of_measure']
      form.buy_price_per_unit.data = product['buy_price_per_unit']
      form.item_price.data = product['item_price']
      form.package_quantity.data = product['package_quantity']
      form.region.data = product['region']
      form.country.data = product['country']
      form.color.data = product['color']
      form.description.data = product['color']

      # Update the product
      if request.method == 'POST':
          product_name = request.form['product_name']
          product_category = request.form['product_category']
          cur_size = request.form['cur_size']
          upc = request.form['upc']
          unit_of_measure = request.form['unit_of_measure']
          buy_price_per_unit = request.form['buy_price_per_unit']
          item_price = request.form['item_price']
          package_quantity = request.form['package_quantity']
          region = request.form['region']
          country = request.form['country']
          color = request.form['color']
          description = request.form['description']

          g.conn.execute('UPDATE product SET product_name=%s, product_category=%s, cur_size=%s, upc=%s, unit_of_measure=%s, buy_price_per_unit=%s, item_price=%s, package_quantity=%s, region=%s, country=%s, color=%s, description=%s WHERE product_id=%s', (product_name, product_category, cur_size, upc, unit_of_measure, buy_price_per_unit, item_price, package_quantity, region, country, color, description, product_id))

          flash('Product Updated', 'success')
          return redirect('/admin/product')

      return render_template('admin/edit_product.html', form=form)

@app.route('/admin/delete/<int:product_id>', methods=['POST',])
def admin_delete_product(product_id):
      if 'username' not in session or not session['is_admin']:
        return redirect(url_for('index'))
      g.conn.execute('DELETE FROM product WHERE product_id = %s', [product_id])
      flash('Product Deleted', 'success')
      return redirect('/admin/product')

# Admin order and shipments overview
class ShipmentForm(Form):
      carrier = StringField('Carrier: ')
      tracking_number = StringField('Tracking Number: ')
      ship_date = DateField('Ship Date: ')
      delivered_date = DateField('Delivered Date: ')
      submit = SubmitField('Submit')

@app.route('/admin/orders')
def admin_orders():
      if 'username' not in session or (not session['is_admin']):
          return redirect(url_for('index'))
      orders = g.conn.execute(
          'select distinct o.order_id, o.order_number, o.customer_id, c.first_name, c.last_name, c.email, o.total, o.tax, o.discount, o.is_void, s.carrier, s.tracking_number, s.ship_date, s.delivered_date from orders o inner join customer c on c.customer_id = o.customer_id left join shipment s on s.order_id = o.order_id ORDER BY o.order_id DESC'
      ).fetchall()
      return render_template('admin/orders.html', orders=orders)

# Admin View for order details
@app.route('/admin/orders/<int:order_id>', methods=['POST','GET'])
def admin_order_details(order_id):
      if 'username' not in session or not session['is_admin']:
        return redirect(url_for('index'))
      
      result = g.conn.execute('select distinct o.order_id, o.order_number, o.customer_id, c.first_name, c.last_name, c.email, o.total, o.tax, o.discount, o.is_void, s.carrier, s.tracking_number, s.ship_date, s.delivered_date, p.payment_method, p.payment_status, p.credit_card, p.expiration_date from orders o inner join customer c on c.customer_id = o.customer_id left join shipment s on s.order_id = o.order_id left join payment p on p.order_id = o.order_id WHERE o.order_id = %s', [order_id])
      order = result.fetchone()

      od = g.conn.execute('select distinct od.order_id, od.product_id, od.quantity, od.price, od.discount, p.brand_id, p.product_name, b.brand_name, p.product_category, p.upc, p.unit_of_measure, p.region, p.country, p.color from order_items od inner join product p on p.product_id = od.product_id left join brand b on b.brand_id = p.brand_id WHERE od.order_id = %s', [order_id])
      order_details = od.fetchall()

      b = g.conn.execute('select distinct o.order_id, bill.first_name, bill.last_name, bill.address1, bill.address2, bill.city, bill.state, bill.zip, bill.phone, bill.company from orders o inner join address bill on bill.address_id = o.bills_to WHERE o.order_id = %s', [order_id])
      bill = b.fetchone()

      s = g.conn.execute('select distinct o.order_id, ship.first_name, ship.last_name, ship.address1, ship.address2, ship.city, ship.state, ship.zip, ship.phone, ship.company from orders o inner join address ship on ship.address_id = o.ships_to WHERE o.order_id = %s', [order_id])
      ship = s.fetchone()

      # Get Form
      form = ShipmentForm(request.form)

      # Populate the form with existing data
      form.carrier.data = order['carrier']
      form.tracking_number.data = order['tracking_number']
      form.ship_date.data = order['ship_date']
      form.delivered_date.data = order['delivered_date']

      if request.method == 'POST':
          carrier = request.form['carrier']
          tracking_number = request.form['tracking_number']
          ship_date = request.form['ship_date']
          delivered_date = request.form['delivered_date']

          g.conn.execute('UPDATE shipment SET carrier=%s, tracking_number=%s, ship_date=%s, delivered_date=%s WHERE order_id=%s', (carrier, tracking_number, ship_date, delivered_date, order_id))

          flash('Shipment Information Updated', 'success')

      return render_template('admin/order_details.html', order=order, form=form, order_details=order_details, bill=bill, ship=ship)


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.secret_key = 'secret_key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
