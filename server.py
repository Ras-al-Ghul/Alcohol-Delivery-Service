
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
from sqlalchemy.sql.selectable import Select
from wtforms import Form, StringField, SubmitField, DecimalField, IntegerField

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

  context = dict(category=category, brand=brand)

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)


@app.route('/loginpost', methods=['POST'])
def loginpost():
  username = request.form['username']
  password = hashlib.md5(request.form['password'].encode()).hexdigest()
  # password = "md512cc15408468bd3663f4717e87acf491" # customer
  password = "md55565b8e7bf495890ee95b3a0345d2c43" # employee
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


@app.route('/signuppost', methods=['POST'])
def signuppost():
  username = request.form['username']
  password1 = request.form['password1']
  password2 = request.form['password2']
  firstname = request.form['firstname']
  lastname = request.form['lastname']
  dob = request.form['dob']
  if ((password1 != password2) or ('@' not in username or '.' not in username) or
      (len(dob) != 10 or dob[4] != '-' or dob[7] != '-') or (dob[:4] > '2000')):
    flash('One of your details is incorrect. Try again.')
    return redirect(url_for('signup'))
  passhash = hashlib.md5(password1.encode()).hexdigest()
  g.conn.execute("INSERT INTO customer (first_name, last_name, email, dob, password) VALUES '{}', '{}', '{}', {}, '{}'"
    .format(firstname, lastname, username, dob, passhash))
  flash('Welcome to Booze.io')
  session['username'] = username
  session['is_admin'] = False
  return redirect(url_for('index'))


@app.route('/login')
def login():
    return render_template('login.html')
    

@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/admin/product')
def admin_product():
      if 'username' not in session or (not session['is_admin']):
        return redirect(url_for('index'))
      products = g.conn.execute(
          'select p.product_id, p.product_name, p.product_category, p.cur_size, p.upc, p.unit_of_measure, p.buy_price_per_unit, p.item_price, p.package_quantity, p.region, p.country, p.color, p.description, b.brand_id, b.brand_name, b.description as brand_description, b.brand_poc from product p left join brand b on b.brand_id = p.brand_id'
      ).fetchall()
      return render_template('admin/product.html', products=products)

class ProductForm(Form):
      product_name = StringField('Product Name: ')
      product_category = StringField('Product Category: ')
      cur_size = IntegerField('Current Inventory: ')
      upc = StringField('UPC: ')
      unit_of_measure = StringField('Unit of Measure: ')
      buy_price_per_unit = DecimalField('Buy Price: ')
      item_price = DecimalField('Item Price: ')
      package_quantity = IntegerField('Package Quantity: ')
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


@app.route('/admin/shipment')
def admin_shipment():
      if 'username' not in session or not session['is_admin']:
        return redirect(url_for('index'))
      return render_template('admin/shipment.html')


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
