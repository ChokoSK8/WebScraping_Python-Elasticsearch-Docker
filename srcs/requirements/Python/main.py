import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import sys
import multiprocessing as mp
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import os
import elasticsearch
import re


# URL of the website we want to scrap
base_url = 'https://techcrunch.com'

# How we wants to organize our data on elasticsearch
mappings = {
	"properties": {
		"title": {
			"type": "text",
		},
		"author": {
			"type": "text",
		},
		"published_time": {
			"type": "text",
		},
		"updated_time": {
			"type": "text",
		},
		"description": {
			"type": "text",
		},
		"link": {
			"type": "text",
		}
	}
}

def init_elasticsearch_connection():
	"""
	Initiate a connection to the Elasticsearch service with username=elastic
	Return:
		elasticsearch client object
	"""
	es = elasticsearch.Elasticsearch(
		hosts='http://host.docker.internal:9200',
		basic_auth=('elastic', os.getenv('ELASTIC_PASSWORD')),
		max_retries=30,
		request_timeout=30
	)
	return es

def get_response_text_from_url(url):
	"""
	Retrieve the response's text of a get request
	Arg:
		url: the url receiving the HTTP get request
	Return:
		string
	"""
	try:
		response = requests.get(url)
	except HTTPError as err:
		sys.exit('Http error occurred: ' + err)
	except Exception as err:
		sys.exit('Other error occurred: ' + err)
	return response.text

def get_all_categories():
	"""
	Retrieve all article categories published on Tech Crunch website

	Return:
		dict with following format: {'category_name_1': 'category_link_1', ..., 'category_name_n': 'category_link_n'}
	"""
	res_text = get_response_text_from_url(base_url + '/pages/site-map/')
	soup = BeautifulSoup(res_text, 'html.parser')
	h = soup.find('h1', string = 'Articles by Category')
	tbody = h.find_next('tbody')
	categories = dict()
	for a in tbody.find_all('a'):
		categories[a.contents[0]] = a['href']
	return categories

def make_list_of_tuples_by_category(href):
	"""
	Retrieve all main informations from articles of one category
	Arg:
		href: link to the category page
	Return:
		list of tuples with following format: {(title, author, published_time, updated_time, description, link), ...}
	"""
	res_text = get_response_text_from_url(base_url + href)
	soup = BeautifulSoup(res_text, 'html.parser')
	articles = soup.find_all('a', {'class': 'post-block__title__link'})
	list_of_tuples = list()
	for article in articles:
		res_text = get_response_text_from_url(article['href'])
		soup = BeautifulSoup(res_text, 'html.parser')
		title = article.contents[0].strip()
		description = soup.find('meta', {'name': 'description'})
		if description:
			description = description['content']
		else:
			description = "None"
		author = soup.find('meta', {'name': 'author'})
		if author:
			author = author['content']
		else:
			author = "None"
		published_time = soup.find('meta', {'property': 'article:published_time'})
		if published_time:
			published_time = published_time['content'][:10]
		else:
			published_time = "None"
		updated_time = soup.find('meta', {'property': 'article:modified_time'})
		if updated_time:
			updated_time = updated_time['content'][:10]
		else:
			updated_time = "None"
		link = base_url + article['href']
		list_of_tuples.append(tuple([title, author, published_time, updated_time, description, link]))
	print(href + " has finished")
	return list_of_tuples

def get_df_collection_by_category(categories):
	"""
	With multiprocessing, we extract articles info for each category as lists of tuples,
		then we create a collection of dataframe classified by category
	Args:
		categories: dict with following format: {'category_name_1': 'category_link_1', ..., 'category_name_n': 'category_link_n'}
	Returns:
		dict of dataframe with following format: {'category_name_1': 'dataframe_1', ..., 'category_name_n': 'dataframe_n'}
	"""
	with ProcessPoolExecutor() as executor:
		futures = []
		for category in categories:
			futures.append(executor.submit(make_list_of_tuples_by_category,
					categories[category]))
		df_collection = {}
		for future, category in zip(as_completed(futures), categories):
			category = re.sub('[\'\\\',\'/\',\'*\',\'?\',\'"\',\'<\',\'>\',\'|\',\' \',\',\']', '', category).lower()
			df_collection[category] = pd.DataFrame(future.result(),
					columns=['title', 'author', 'published_time', 'updated_time', 'description', 'link'])
	return df_collection

def add_df_collection_to_elasticsearch(es, df_collection):
	"""
	We insert to elasticsearch's database the collected data
	Args:
		es: elasticsearch client
		df_collection: data with following format: {'category_name_1': 'dataframe_1', ..., 'category_name_n': 'dataframe_n'}
	"""
	for category in df_collection:
		try:
			es.indices.create(index=category, mappings=mappings)
		except elasticsearch.BadRequestError as err:
			if err.status_code != 400:
				raise err
		for i in range(len(df_collection[category])):
			es.index(
				index = category,
				document = df_collection[category].loc[i].to_dict()
			)

if __name__ == "__main__":
	es = init_elasticsearch_connection()
	categories = get_all_categories()
	df_collection = get_df_collection_by_category(categories)
	add_df_collection_to_elasticsearch(es, df_collection)
