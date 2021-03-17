
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
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from wtforms import Form, StringField

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

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)

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

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(category=category, brand=brand)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

@app.route('/admin/product')
def admin_product():
      products = g.conn.execute(
          'select p.product_name, p.product_category, p.cur_size, p.upc, p.unit_of_measure, p.buy_price_per_unit, p.item_price, p.package_quantity, p.region, p.country, p.color, p.description, b.brand_name, b.description as brand_description, b.brand_poc from product p left join brand b on b.brand_id = p.brand_id'
      ).fetchall()
      return render_template('admin/product.html', products=products)

class ProductForm(Form):
      product_name = StringField('Product Name')

@app.route('/admin/add_product', methods=['POST', 'GET'])
def admin_add_product():
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
      product = g.conn.execute('SELECT * FROM product WHERE product_id = %s', product_id)
      product = product.fetchone()

      # Populate the form with existing data
      form.product_name.data = product['title']

      # if request.method == 'POST':
      #     product_name = request.form['product_name']
      #     product_category = request.form['product_category']
      #     cur_size = request.form['cur_size']
      #     upc = request.form['upc']
      #     unit_of_measure = request.form['unit_of_measure']
      #     buy_price_per_unit = request.form['buy_price_per_unit']
      #     item_price = request.form['item_price']
      #     package_quantity = request.form['package_quantity']
      #     region = request.form['region']
      #     country = request.form['country']
      #     color = request.form['color']
      #     description = request.form['description']

      #     g.conn.execute('INSERT INTO product(brand_id, product_name, product_category, cur_size, upc, unit_of_measure, buy_price_per_unit, item_price, package_quantity, region, country, color, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (product_name) DO NOTHING', brand_id, product_name, product_category, cur_size, upc, unit_of_measure, buy_price_per_unit, item_price, package_quantity, region, country, color, description)

      #     return redirect('/admin/product')

      return render_template('admin/edit_product.html')
  
@app.route('/admin/shipment')
def admin_shipment():
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
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
