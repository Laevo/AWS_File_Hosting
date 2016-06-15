import boto3
import boto
from boto.s3.connection import S3Connection
from datetime import datetime, timedelta
import webbrowser
import os
import json
from flask import Flask, Response, request, make_response
from flask_table import Table, Col
app = Flask(__name__)
s3r = boto3.resource('s3')
s3c = boto3.client('s3')

connection = S3Connection(
    aws_access_key_id='AKIAJZHN3P6PIO3FWKCQ',
    aws_secret_access_key='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')


@app.route('/')
def Welcome():
    return app.send_static_file('login.html')

bucketname = None
username = None
@app.route('/login', methods=['GET', 'POST'])
def Login():
    global username
    global bucketname
    if request.method == 'POST':
        username = str(request.form['username'])
        bucket = s3r.Bucket('userscred')
        obj = bucket.Object('UserAccessList.txt')
        users = obj.get()['Body'].read()
        users = users.split()
        print users
        for user in users:
            if user == username:
                if username == 'mike':
                    bucketname = 'pratha222'
                if username == 'harsha':
                    bucketname = 'rohit562'
                if username == 'dummy':
                    bucketname = 'vinay111'
                return app.send_static_file('index.html')
        return 'Authentication Failed'



@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_name = file.filename
            content = file.read()
            s3c.put_object(Bucket=bucketname, Key=file_name, Body=content)
            # s3r.Bucket(bucket.bucketname).put_object(Key=file_name, Body=content)
            return 'File Uploaded'


@app.route('/list', methods=['GET', 'POST'])
def list_files():
    if request.method == 'POST':
        # Declare your table
        class ItemTable(Table):
            name = Col('Filename')
            size = Col('Size')
            uploaded = Col('Uploaded')
        class Item(object):
            def __init__(self, name, size, uploaded):
                self.name = name
                self.size = size
                self.uploaded = uploaded
        items = []
        bucket = s3r.Bucket(bucketname)
        for key in bucket.objects.all():
            doc = dict(name=str(key.key)+'  ', size=str(key.size/1000)+' kb', uploaded='  '+str(key.last_modified))
            items.append(doc)
        table = ItemTable(items)
        passtable = (table.__html__())
        return passtable


@app.route('/delete', methods=['GET', 'POST'])
def delete_file():
    if request.method == 'POST':
        filename = request.form['filename']
        bucket = s3r.Bucket(bucketname)
        for key in bucket.objects.all():
            if key.key == filename:
                key.delete()
                return 'File Deleted'
        return 'File Not Found'


@app.route('/download', methods=['GET', 'POST'])
def download_file():
    if request.method == 'POST':
        filename = request.form['filename']
        bucket = s3r.Bucket(bucketname)
        for key in bucket.objects.all():
            if key.key == filename:
                url = connection.generate_url(
                60,
                'GET',
                bucket.name,
                str(key.key),
                response_headers={
                    'response-content-type': 'application/octet-stream'
                })
                url = url[:url.find('?')]
                webbrowser.open(str(url))
                return 'File Downloaded'
                break
        return 'File Not Found'


@app.route('/purge', methods=['GET', 'POST'])
def purge_files():
    if request.method == 'POST':
        purgetime = float(request.form['purgetime'])
        bucket = connection.get_bucket(bucketname)
        key_list = bucket.get_all_keys()
        for key in key_list:
            expires = datetime.utcnow() + timedelta(hours=(purgetime))
            expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            metadata = {'Expires': expires}
            key.copy(bucketname, key, metadata=metadata, preserve_acl=True)
            return 'All file will be purged on ' + expires


port = os.getenv('VCAP_APP_PORT', '5005')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port), debug=True)