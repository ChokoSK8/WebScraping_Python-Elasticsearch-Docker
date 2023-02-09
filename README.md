# What does it do ?
  We scrap data from "www.techcrunch.com". We seek for informations about articles from any category. We collect them in dataframes. Then we insert them to the Elasticsearch database.
# Installation
### Clone the repo
```
git clone https://github.com/ChokoSK8/WebScraping_Python-Elasticsearch-Docker.git
```
### Configure your .env file in srcs directory
copy this file in srcs/, then add an elastic_password and a cluster_name
```
# Password for the 'elastic' user (at least 6 characters)
ELASTIC_PASSWORD=

# Version of Elastic products
STACK_VERSION=8.6.1

# Set the cluster name
CLUSTER_NAME=

# Port to expose Elasticsearch HTTP API to the host
ES_PORT=9200

# Increase or decrease based on the available host memory (in bytes)
MEM_LIMIT=1073741824
```
## Running the project
```
make
```
