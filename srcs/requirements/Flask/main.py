from flask import Flask, render_template
import requests
import json

app = Flask(__name__)

get_indexes_url = 'http://host.docker.internal:9200/_aliases'

@app.route('/')
def home():
	response = requests.get(get_indexes_url)
	if response.status_code != 200:
		return '<h1>Error when accessing elasticsearch database</h1>'
	json_to_py = json.loads(response.content)
	categories = list(json_to_py.keys())
	return render_template('index.html', categories=categories)

@app.route('/<category>')
def get_categorie_docs(category):
	url = "http://host.docker.internal:9200/" + category + "/_search?pretty"
	response = requests.get(url)
	if response.status_code != 200:
		return f'<h1>Error when accessing {category} data</h1>'
	json_to_py = json.loads(response.content)
	docs = json_to_py['hits']['hits']
	return render_template('category.html', category=category, docs=docs)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
