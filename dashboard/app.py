import csv
import xlrd
import io
import json
import re
import pandas as pd
import numpy as np
import pymongo
from bson import ObjectId  # For ObjectId to work
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
title = "CodeBlack: KB CVS Production line automation"
heading = "CodeBlack: KB CVS Production line automation"

# region  MongoDB Configurations
url = "mongodb://codeblack:codeblack@codeblackcluster-shard-00-00-jhkho.mongodb.net:27017,codeblackcluster-shard-00-01-jhkho.mongodb.net:27017,codeblackcluster-shard-00-02-jhkho.mongodb.net:27017/test?ssl=true&replicaSet=codeblackCluster-shard-0&authSource=admin&retryWrites=true&w=majority"
# client = MongoClient("mongodb://127.0.0.1:27017")  # host uri
try:
    client = MongoClient(url)
except:
    print("Could not connect to MongoDB")
db = client.codeblack  # Select the database
emptybins = db.emptybins  # Select the collection name
products = db.products  # Select the collection name
products.create_index([('to_number', pymongo.ASCENDING), ('material', pymongo.ASCENDING)], unique=True)
emptybins.create_index([('station_id', pymongo.ASCENDING), ('bin_id', pymongo.ASCENDING)], unique=True)
# endregion

# region REST full API calls
@app.route('/products', methods=["GET"])
def get_products():
    return CodeBlack.get_products()


@app.route("/", methods=["GET"])
@app.route("/emptybins", methods=["GET"])
def get_emptybins():
    return CodeBlack.get_emptybins()


@app.route("/search_products", methods=['GET'])
def search_products():
    return CodeBlack.search_products()


@app.route("/search_emptybins", methods=['GET'])
def search_emptybins():
    return CodeBlack.search_emptybins()


@app.route("/check_transfer_order", methods=["POST"])
def check_transfer_order():
    return CodeBlack.check_transfer_order()


@app.route("/update_product_details", methods=["POST"])
def update_product_details():
    return CodeBlack.update_product_details()


@app.route('/update_bin_status', methods=["POST"])
def update_bin_status():
    return CodeBlack.update_bin_status()


@app.route('/insert_TO', methods=["POST"])
def insert_TO():
    return CodeBlack.insert_TO()


# endregion

class CodeBlack(object):
    @staticmethod
    def redirect_url():
        return request.args.get('next') or \
               request.referrer or \
               url_for('index')

    @staticmethod
    def get_products():
        # Display the all Tasks
        product_list = products.find()
        a2 = "active"
        return render_template('products.html', a2=a2, products=product_list, t=title, h=heading)

    @staticmethod
    def get_emptybins():
        emptybin_list = emptybins.find()
        a1 = "active"
        return render_template('index.html', a1=a1, bins=emptybin_list, t=title, h=heading)

    @staticmethod
    def search_products():
        # Searching a Task with various references
        a2 = "active"
        key = request.values.get("key")
        refer = request.values.get("refer")
        if (key == "_id"):
            product_list = products.find({refer: ObjectId(key)})
        else:
            product_list = products.find({refer: key})
        return render_template('searchproducts.html', a2=a2, products=product_list, t=title, h=heading)

    @staticmethod
    def search_emptybins():
        # Searching a Task with various references
        a1 = "active"
        key = request.values.get("key")
        refer = request.values.get("refer")
        if key == "_id":
            bins = emptybins.find({refer: ObjectId(key)})
        else:
            bins = emptybins.find({refer: key})
        return render_template('searchbins.html', a1=a1, bins=bins, t=title, h=heading)

    @staticmethod
    def check_transfer_order():
        json_data = request.get_json()

        try:
            product_match = products.find({'to_number': json_data['to_number']}, {'_id': 1})
        except Exception as e:
            print("Error occurred: %s" % str(e))

        if len(list(product_match)) > 0:
            resp = "success"
        else:
            resp = "failure"
        return json.dumps(resp)

    @staticmethod
    def update_product_details():
        json_data = request.get_json()
        # Find if {"to_number":transfer_order,"dest__bin":bin,"material":product}
        # Matches to the database
        try:
            product_match = products.find({'to_number': json_data['to_number'],
                                           'dest__bin': json_data['dest__bin'],
                                           'material': json_data['material']}, {'_id': 1})
        except Exception as e:
            print("Error occurred: %s" % str(e))
            return json.dumps("failure")
        if len(list(product_match)) > 0:
            try:
                status = products.update({'to_number': json_data['to_number'],
                                          'dest__bin': json_data['dest__bin'],
                                          'material': json_data['material']}
                                         , {
                                             '$set': {"status": "Scanned"}
                                         })
                resp = "success"
            except Exception as e:
                print("Error occurred: %s" % str(e))
                resp = "failure"
        else:
            resp = 'failure'
        return json.dumps(resp)

    @staticmethod
    def update_bin_status():
        json_data = request.get_json()

        try:
            if json_data['status'] == 'E':
                emptybins.insert_one({'station_id': json_data['station_id'],
                                      'bin_id': json_data['bin_id'], 'status': json_data['status']})
            elif json_data['status'] == 'F':
                emptybins.remove({'station_id': json_data['station_id'],
                                  'bin_id': json_data['bin_id']})
            else:
                return "failure"
            resp = "success"
        except Exception as e:
            print("Error occurred: %s" % str(e))
            resp = "ignore"

        return json.dumps(resp)

    @staticmethod
    def insert_TO():
        file = request.files['data_file']
        if not file:
            return "No file"
        elif '.xlsx' in str(file):
            book = xlrd.open_workbook(file_contents=file.read())
            df = pd.read_excel(book, sheet_name=0, header=0, engine='xlrd', convert_float='False')
            # Excel read int as numerical data, while csv reads it as string
            # To make both uniform as string, below section identifies the same & replace with string
            categorical = list(df.columns[(df.dtypes.values == np.dtype('float64'))])
            df[categorical] = df[categorical].fillna(-1)
            df[categorical] = df[categorical].astype(int)
            df[categorical] = df[categorical].astype(str)
            df[categorical] = df[categorical].replace('-1', np.nan)
        elif '.csv' in str(file):
            # latin-1
            stream = io.StringIO(file.stream.read().decode("latin-1"), newline=None)
            # stream = io.StringIO(file.stream.read(), newline=None)
            csv_input = csv.reader(stream)
            df_data = []

            for row in csv_input:
                df_data.append(row)
            headers = df_data.pop(0)
            df = pd.DataFrame(df_data, columns=headers)
        else:
            return "Upload csv/excel file."

        # remove special chars between the name of column
        df.columns = ["_".join(re.sub("[^a-zA-Z]", " ", col.lower()).strip().split(" ")) for col in df.columns]
        # Remove duplicate rows if there any (Based on Transfer Order number)
        df.drop_duplicates(subset=["material"], keep='first', inplace=True)
        # Remove duplicate columns if there any (Based on Transfer Order number)
        df = df.loc[:, ~df.columns.duplicated()]
        df['status'] = "Not Scanned"

        json_str = df.to_json(orient='records')
        json_data = json.loads(json_str)
        try:
            products.insert_many(json_data)
            print('Records inserted successfully.')
            resp = "Success"
        except Exception as e:
            resp = "Failure"
            print('Error occurred: %s ' % (str(e)))
        return redirect("/products")


if __name__ == "__main__":
    app.run(debug=True)
