#!/usr/bin/env python3


'''
TODO: watch directory

nextflow has a channel.watchPath ...

(for send process)
(for download process?)
'''



import pika


# import argparse
# import glob
# from pathlib import Path
# import pprint

# import networkx as nx
import screed
# import sourmash
# from tqdm import tqdm


# parser = argparse.ArgumentParser(description='Cluster and search context')
# parser.add_argument(
#     '-i', required=True, help='Query genomes')
# parser.add_argument(
#     '-o', required=True, help='Where to save clusters')
# parser.add_argument(
#     '--db', default=None, help='SBT')
# parser.add_argument(
#     '--minsize', default=3, type=int, help='Minimum cluster size')
# parser.add_argument(
#     '--threshold', default=0.95, type=float, help='nt distance threshold')
# args = parser.parse_args()

import argparse
from pathlib import Path
import socket
import uuid

import geocoder
import sourmash



import argparse

parser = argparse.ArgumentParser(description='Process some genomes.')
parser.add_argument(
    '--genome', required=True,
    help='an integer for the accumulator')
parser.add_argument(
    '--filehash', required=True,
    help='Filename and IPFS hash')
parser.add_argument(
    '--db',
    help='Sourmash LCA database')
parser.add_argument(
    '--url', default='localhost',
    help='AMPQ url or localhost')
parser.add_argument(
    '--exchange', required=True,
    help='RabbitMQ exchange key')
parser.add_argument(
    '--id', default=uuid.uuid4(),
    help='User id')
parser.add_argument(
    '--signature', default=uuid.uuid4(),
    help='Sourmash signature/ sketch of the genome')
parser.add_argument(
    '--taxonomy', default=uuid.uuid4(),
    help='Sourmash lca classify output')
parser.add_argument(
    '--geo', action='store_true',
    help='Add geolocation')
args = parser.parse_args()


# mh_params = {
#     'n': 0, 
#     'ksize': 31, 
#     'scaled': 1000}

genome = Path(args.genome)  # list so tqdm knows how many
# paths = list(Path(args.i).glob('*.fasta'))  # list so tqdm knows how many
# sigs = {}



def parse(line: str) -> list:
    return line.strip().split(',')



def load_taxonomy(fp: str) -> dict:
    '''
    ID,status,superkingdom,phylum,class,order,family,genus,species,strain
MIT9313.fasta,found,Bacteria,Cyanobacteria,unassigned,Synechococcales,Prochloraceae,Prochlorococcus,Prochlorococcus marinus,

    ID,status,superkingdom,phylum,class,order,family,genus,species,strain
mock.fasta,nomatch,,,,,,,,
    '''
    with open(fp, 'r') as file:
        header = parse(next(file))
        names = parse(next(file))

        # Modify the status into a binary feature so it can be part of the
        # routing key, to allow e.g. search of unknown "mystery" bacteria.
        # names[1]: 'found', 'disagree', 'nomatch'
        status = names[1]
        if status == 'nomatch':
            status = 'mystery'
        elif status in ['found', 'disagree']:
            status = 'found'
        taxa = [i.split('__')[-1] if i else 'unknown' for i in names[2:]]
        return status, taxa
        # GTDB syntax w/ taxonomy prefix, e.g. "g__Acinetobacter"


def eprint(*args, **kwargs):
    '''
    stackoverflow.com/questions/5574702
    '''
    print(*args, file=sys.stderr, **kwargs)


from sourmash.lca import lca_utils
from sourmash.lca.command_classify import classify_signature


'''
topic to generate

species.country.x.y.z

> Fully 95.1% match at the genus level! And for all of these, the sourmash classifications agree with the GTDB taxonomy - a full 99.96% of the time. -- http://ivory.idyll.org/blog/2019-sourmash-lca-vs-gtdb-classify.html

database from there, alternative from docs:

https://sourmash.readthedocs.io/en/latest/tutorials-lca.html

curl -L -o genbank-k31.lca.json.gz https://osf.io/4f8n3/download

- https://github.com/dib-lab/2019-sourmash-gtdb/blob/master/bulk-classify-sbt-with-lca.py
- http://ivory.idyll.org/blog/2019-sourmash-lca-db-gtdb.html

this works:

sourmash lca classify --db gtdb-release89-k31.lca.json.gz --query reference.fasta.sig


db2 = args.db  # 'gtdb-release89-k31.lca.json.gz'
print('Loading taxonomy database ...')
dblist, ksize, scaled = lca_utils.load_databases([db2])

classified_as, why = classify_signature(query, dblist, 5)
# Insist on at least 'threshold' counts of a given lineage before taking
# it seriously.
print(get_species(classified_as))
print(classified_as)
'''

# def get_species(lca_query):
#     last = lca_query[-1]
#     if last.rank == 'species':
#         return last.name
#     else:
#         return None


def connect(url):
    '''
    https://www.cloudamqp.com/blog/2015-05-21-part2-3-rabbitmq-for-beginners_example-and-sample-code-python.html
    '''
    if args.url == 'localhost':
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=args.url))
        except pika.exceptions.AMQPConnectionError as e:
            eprint(e)
            eprint('Did you start a local RabbitMQ server? (rabbitmq-server)')
            sys.exit(-1)
    else:        
        try:
            params = pika.URLParameters(args.url)
            params.socket_timeout = 5
            connection = pika.BlockingConnection(params)
        except socket.gaierror as e:  # No internet connection?
            eprint(e)
            eprint('There seems to be a problem w/ your internet connection?')
            sys.exit(-1)

    return connection


# TODO: Write this as if else localhost url -- for testing (paper) use former
# CloudAMPQ docs
# https://www.cloudamqp.com/blog/2015-05-21-part2-3-rabbitmq-for-beginners_example-and-sample-code-python.html
# https://pika.readthedocs.io/en/latest/modules/parameters.html
# url = 'amqp://ubugbkyk:GgNs09Y0fnCTTFgEFaBnowTOD-ZFYm3v@swan.rmq.cloudamqp.com/# ubugbkyk'
# params = pika.URLParameters(url)
# params.socket_timeout = 5
# connection = pika.BlockingConnection(params)
# # connection = pika.BlockingConnection(
# #         pika.ConnectionParameters(host='localhost'))
# channel = connection.channel()







connection = connect(args.url)
channel = connection.channel()


# channel.queue_declare(queue='hello')
channel.exchange_declare(exchange=args.exchange, exchange_type='topic')


# TODO: How to control access/ security?
# https://www.rabbitmq.com/passwords.html


'''
Messages sent to a topic exchange can't have an arbitrary routing_key - it must be a list of words, delimited by dots. The words can be anything, but usually they specify some features connected to the message. A few valid routing key examples: "stock.usd.nyse", "nyse.vmw", "quick.orange.rabbit". There can be as many words in the routing key as you like, up to the limit of 255 bytes.
'''

# import subprocess


# def put_on_ipfs(file):
#     '''
#     Put a file on IPFS and return the original file name and the IPFS hash.
#     '''
#     hsh = subprocess.run(
#         ['ipfs', 'add', file],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.DEVNULL)
#     # ('added QmS5cz... foo.fasta\n',)
#     try:
#         hsh.check_returncode()
#     except subprocess.CalledProcessError:
#         print('damn')
#         import sys; sys.exit(-1)

#     return hsh.stdout.decode('utf-8').strip().split(' ')[1:]


# Geolocation as part of the topic routing key
# TODO: catch connection error
if args.geo:
    geo = geocoder.ip('me')
    if not geo.error:
        country = geo.country
    else:
        country = 'unknown'

# TODO: debug
# country = 'DE'
# print('Sending out message(s) ...')
status, tax = load_taxonomy(args.taxonomy)  # tax['status'] 'found'

# print(tax)
# 69/1faadc
# bb/ae65c2


# found
# nomatch

# print(country)
# print('tax', load_taxonomy(args.taxonomy))

routing_key = '.'.join([str(args.id), country, status, *tax])
print(routing_key)
# phiweger.unknown.found.Bacteria.Proteobacteria.Gammaproteobacteria.Pseudomonadales.Moraxellaceae.Acinetobacter.unknown.unknown
# print(f'Routing key: {routing_key}')




# mh = sourmash.MinHash(**mh_params)

# for record in screed.open(genome.resolve().__str__()):
#     mh.add_sequence(record.sequence, True)


with open(args.filehash, 'r') as file:
    hsh, filename = next(file).strip().split(' ')[1:]
    # added QmP3viJv... file.fasta

signame = f'{args.id}::{hsh}::{filename}'
print(filename)

# query = sourmash.SourmashSignature(mh, name=signame)

sketch = sourmash.load_one_signature(args.signature)
query = sourmash.SourmashSignature(sketch.minhash, name=signame)
msg = sourmash.save_signatures([query])
# import time; time.sleep(1)


# channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
channel.basic_publish(
    exchange=args.exchange, routing_key=routing_key, body=msg)
    # exchange=args.exchange, routing_key='hello.cello', body=msg)

connection.close()

