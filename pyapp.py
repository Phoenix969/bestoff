from flask import Flask,render_template,request,redirect,flash,url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath

app = Flask(__name__)
app.secret_key=b'_5#y2L"F4Q8z\n\xec]/'
UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

details_dict={}
products_dict={}
pairs={}
orders_path = ""
products_path = ""
num = 0
print_pairs = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/results',  methods=['GET','POST'])
def results():
    return render_template('results.html',data=print_pairs)



@app.route('/index', methods=['GET','POST'])
def index():
    global pairs, print_pairs, details_dict, products_dict, num
    if request.method == "POST":
        os.makedirs(os.path.join(app.instance_path, 'htmlfi'), exist_ok=True)
        global orders_path, products_path
        details_dict['description'] = request.form.get("description")
        orders = request.files['orders']
        if orders.filename != '':

            orders_path = os.path.join(app.instance_path, 'htmlfi', secure_filename(orders.filename))
            # set the file path
            orders.save(orders_path)
        details_dict['o_oid'] = request.form.get('O_Oid').strip()
        details_dict['o_pid'] = request.form.get('O_Pid').strip()
        products = request.files['products']
        if products.filename != '':
            #products_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(products.filename))
            products_path = os.path.join(app.instance_path, 'htmlfi', secure_filename(products.filename))
            # set the file path
            products.save(products_path)
        details_dict['p_pid'] = request.form.get('P_Pid').strip()
        details_dict['p_pname'] = request.form.get('P_Pname').strip()
        validate()
        count_dict = process()

        return render_template('index.html')
    else:

        pairs = {}
        print_pairs = {}
        details_dict = {}
        products_dict = {}
        num = 0
        return render_template('index.html')

@app.route('/red_ind', methods=['GET', 'POST'])
def red_ind():
    global  pairs
    pairs = {}
    return render_template('index.html')

def validate():

    df = pd.read_csv(orders_path)
    products = pd.read_csv(products_path)
    if (details_dict['o_oid'] not in df.columns):
        flash("No "+details_dict['o_oid'] + " column in Orders data","error")
        return
    if (details_dict['o_pid'] not in df.columns):
        flash("No "+details_dict['p_pid']+ " column in Orders data","success")
        return
    if (details_dict['p_pid'] not in products.columns):
        flash("No "+details_dict['p_pid']+ " column in Products data")
        return
    if (details_dict['p_pname'] not in products.columns):
        flash("No "+details_dict['p_pname']+ " column in Products data")
        return

def process():
    global pairs,print_pairs
    prod = pd.read_csv(products_path)
    prod_map = dict(zip(prod.product_id, prod.product_name))
    orders = pd.read_csv(orders_path)


    orders_dict = {}                               # Contains transactions

    for i in range(len(orders)):
        if orders.order_id[i] not in orders_dict:
            orders_dict[orders.order_id[i]] = [orders.product_id[i]]
        else:
            orders_dict[orders.order_id[i]].append(orders.product_id[i])

    for i in orders_dict:                           # Removes duplicate products in transactions
        orders_dict[i] = list(set(orders_dict[i]))

    num_trans = len(orders_dict)                    # Total number of transactions
    count_dict = {}
    for i in orders_dict:
        count_pair(count_dict, orders_dict[i])      # Counts the occurence of each pair of products in every transaction
    count_dict = dict(sorted(count_dict.items(), key=lambda item: item[1], reverse=True))   # Sort by count
    evaluate(count_dict,num_trans,prod_map)
    pair_sort = list(pairs.values())
    newlist = sorted(pair_sort, key=lambda d: d['support'], reverse=True)
    key = list(pairs.keys())
    pairs = dict(zip(key, newlist))


    for i in pairs:
        if i <= 1000:
            print_pairs[i] = pairs[i]
    flash("Succesfully Processed")
    return count_dict

def evaluate(count_dict,num_trans,prod):            # Evaluates support and lift of the pairs
    k = 1
    for i in count_dict:
        if (len(i) == 2):
            x = count_dict[i]
            count_dict[i] = {}
            count_dict[i]['count'] = x
            support = round(count_dict[i]['count'] / num_trans, 9)
            count_dict[i]['support'] = support
            count = []
            prod1 = []

            for j in i:
                count.append(count_dict[frozenset({j, j})])
                prod1.append(prod[j])

            lift = round(support / (count[0] * count[1]), 9)
            count_dict[i]['lift'] = lift
            pairs[k] = {'product1': prod1[0],
                        'product2': prod1[1],
                        'count': count_dict[i]['count'],
                        'support': count_dict[i]['support'],
                        'lift': count_dict[i]['lift']}
            k = k + 1
    return

def count_pair(count_dict, prod):
    for i in range(len(prod)):
        for j in range(i, len(prod)):
            if frozenset({prod[i], prod[j]}) not in count_dict:
                count_dict[frozenset({prod[i], prod[j]})] = 1
            else:
                count_dict[frozenset({prod[i], prod[j]})] = count_dict[frozenset({prod[i], prod[j]})] +1
    return


if __name__ == '__main__':
    app.run(debug=True)

