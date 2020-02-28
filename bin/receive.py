#!/usr/bin/env python


'''
This script ...
'''


import contextlib
# from uuid import uuid4
from functools import partial
import socket
import subprocess
import sys
import time

import pika
import sourmash

import argparse


parser = argparse.ArgumentParser(description='Receive some genomes.')
parser.add_argument(
    '--log', default='-',
    help='IPFS record')
parser.add_argument(
    '--threshold', default=0.95, type=float,
    help='Minimum Jaccard similarity')
parser.add_argument(
    '--db', default=None,
    help='SBT')
parser.add_argument(
    '--outdir', required=True,
    help='Download dir')
parser.add_argument(
    '--url', default='localhost',
    help='AMPQ url or localhost')
parser.add_argument(
    '--exchange', required=True,
    help='RabbitMQ exchange key')
parser.add_argument(
    '--tags', required=True,
    help='Tags to construct routing keys')
parser.add_argument(
    '--filter', required=False,
    help='An SBT index to filter messages')
args = parser.parse_args()


@contextlib.contextmanager
def smart_open(filename=None, mode='w+'):
    '''
    stackoverflow.com/questions/17602878
    TODO: try https://github.com/RaRe-Technologies/smart_open
    '''
    import sys
    if filename and filename != '-':
        fh = open(filename, mode)
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


def callback(ch, method, properties, body, download=False, db=None, threshold=None, outfile='-', outdir=None):
    
    with smart_open(outfile, 'a+') as out:
        # Defaults to stdout
        
        query = sourmash.load_one_signature(body.decode('utf-8'))
        userid, hsh, filename = query.name().split('::')
        # https://stackoverflow.com/questions/21689365/python-3-typeerror-must-be-str-not-bytes-with-sys-stdout-write

        out.write(f'{userid},{hsh},{filename}\n')
        out.flush()

        if db:

            hits = list(sourmash.search_sbt_index(db, query, threshold))

            if hits:
                '''
                import time; time.sleep(2)

                Probably IPFS takes some time to put stuff on the network -- if
                we are too quick w/ the message send/ receive and try to get
                a file from the network that is not properly "put up there" yet,
                we get an error and then this causes an error in the send process.
                '''
                try:
                    result = get_from_ipfs(hsh, filename, outdir)  
                except subprocess.CalledProcessError:
                    exit()

                ch.basic_ack(
                    delivery_tag=method.delivery_tag)

            else:
                ch.basic_reject(
                    delivery_tag=method.delivery_tag, requeue=False)
                # TODO: See tutorial on worker queue
                # requeue parameter set to false
                # https://www.rabbitmq.com/dlx.html

        else:
            try:
                result = get_from_ipfs(hsh, filename, args.outdir)  
            except subprocess.CalledProcessError:
                exit()
            ch.basic_ack(delivery_tag=method.delivery_tag)


def eprint(*args, **kwargs):
    '''
    stackoverflow.com/questions/5574702
    '''
    print(*args, file=sys.stderr, **kwargs)


def get_from_ipfs(hsh, filename, outdir):
    '''
    Put a file on IPFS and return the original file name and the IPFS hash.
    '''
    # subprocess.run waits for the process to end
    # https://stackoverflow.com/questions/49227453
    # https://docs.python.org/3/library/subprocess.html
    # return subprocess.run(['echo', 'foo'])
    
    # import pdb; pdb.set_trace()
    # print(hsh, filename)

    result = subprocess.run(
        ['ipfs', 'get', '-o', f'{outdir}/{filename}', hsh],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    result.check_returncode()
    return result


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


def parse(line):
    return line.strip().split(',')


def load_routing_keys(fp):

    header_lca = 'superkingdom,phylum,class,order,family,genus,species,strain'
    levels = header_lca.split(',')


    with open('tags.csv', 'r') as file:
        header = parse(next(file))
        for line in file:
    
            line_ = ['*' if i == '' else i for i in parse(line)]
            d = {k: v for k, v in zip(header, line_)}
            
            x = ['*' for _ in range(len(levels))]
            
            if (d['level'] == '*') or (d['taxon'] == '*'):
                pass
            else:
                ix = levels.index(d['level'])
                x[ix] = d['taxon']
            
            routing_key = f"{d['name']}.{d['country']}.{d['status']}.{'.'.join(x)}"
            
            yield routing_key


connection = connect(args.url)
channel = connection.channel()
channel.exchange_declare(exchange=args.exchange, exchange_type='topic')

result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

# phiweger.unknown.found.Bacteria.Proteobacteria.Gammaproteobacteria.Pseudomonadales.Moraxellaceae.Acinetobacter.unknown.unknown
# channel.queue_bind(
#         exchange=args.exchange, queue=queue_name, routing_key='*.*.found.Archaea.#')


for k in load_routing_keys(args.tags):
    channel.queue_bind(exchange=args.exchange, queue=queue_name, routing_key=k)


# channel.queue_bind(
#         exchange=args.exchange, queue=queue_name, routing_key='phiweger2.#')
# channel.queue_bind(
#         exchange=args.exchange, queue=queue_name, routing_key='*.*.found.#')
#         # exchange=args.exchange, queue=queue_name, routing_key='hello.#')

# Pass user data to callbacks using partial()
# https://github.com/pika/pika/issues/158
# on_message_callback=callback(download=True)

try:
    db = sourmash.load_sbt_index(args.db)  # 'genomes/context.sbt.json'
except (FileNotFoundError, TypeError):
    db = None

channel.basic_consume(
    queue=queue_name,
    on_message_callback=partial(
        callback,
        download=True,
        db=db,
        threshold=args.threshold,
        outfile=args.log,
        outdir=args.outdir))
# outfile can be e.g. ".log" or "-"

# eprint('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()

