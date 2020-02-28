# DarkQ

<!-- ![](img/queue.png) -->

<p align="center">
  <img src="./img/queue.png" width="500">
</p>

Genomic surveillance is not only limited by the speed at which genomes can be shared, but by how fast they can reach the right person or algorithm to analyse them. If you are monitoring a regional outbreak of a multiresistant _Klebsiella pneumoniae_ and I send you some viral genomes, this will not be too useful.

DarkQ is a messaging queue for microbial genomes. Publishers (P) send (infectious) messages and consumers (C) subscribe to a filtered subset, depending on their preferences. Say I publish all the stuff we sequence during the month, amongst other things some _Klebsiella_. Now you subscribe to the _Klebsiella_ queue, or even more general to all Enterobacterales from Germany, and you filter the messages for genomes that are similar to the isolates in your current outbreak. You might discover, that some of my isolates are from the same lineage as your outbreak isolates. Now you can contact me and we can take action to limit the spread of this strain.

DarkQ relies on two main components, a message queue and a file sharing protocol. 

<p align="center">
  <img src="./img/flow.png" width="500">
</p>

Messages are _MinHash_ signatures of the underlying genomes -- think lossy compression [1]. They can be wired efficiently across the message queue and you can compare the similarity of a pair of genomes through these signatures, too. If a given message passes the filters (subscription, genome similarity), it is downloaded through the second component of DarkQ, namely the _Interplanetary File System_ (IPFS) [protocol](https://ipfs.io/). Basically, it allows decentralized, peer-to-peer file sharing, which we think is crucial in effective genomic surveillance.

[1]: Ondov, Brian D. et al., 2016. “Mash: Fast Genome and Metagenome Distance Estimation Using MinHash.” Genome Biology 17 (1): 132.


## Install

```bash
# IPFS is a peer-to-peer file sharing protocol
# https://docs.ipfs.io/guides/guides/install/
tar xvfz go-ipfs.tar.gz
cd go-ipfs
./install.sh

# DarkQ has a couple of needs
conda create -n darkq -y python=3.7 && conda activate darkq
conda install -y -c bioconda sourmash nextflow

# RabbitMQ is used to publish and subscribe to messages
# https://www.rabbitmq.com/download.html
conda install -y -c conda-forge rabbitmq-server pika

# And we need a taxonomy database and testdata
conda install -y -c conda-forge osfclient
osf -p gs29b fetch \
    gtdb-release89-k31.lca.json.gz \
    databases/gtdb-release89-k31.lca.json.gz
# Thanks Titus -- http://ivory.idyll.org/blog/2019-sourmash-lca-db-gtdb.html
```


## Run

```bash
git clone https://github.com/phiweger/darkq && cd darkq

# Create a custom database, which will filter the messages for similar genomes
sourmash compute -k31 --scale 1000 data/filter/*
sourmash index databases/filter *.sig && rm *.sig

# Start message queue server (to send via localhost)
rabbitmq-server &

# Start IPFS daemon
ipfs daemon &

# Start sending/ receiving infectious messages
nextflow run main.nf
```

Now pull some genomes from the `data/test` folder into `data/send` and see how they turn up in `data/receive`. In this example, you only shared data with yourself. To start sharing with others, connect to the queue we provide:

```bash
nextflow run main.nf --url amqp://ubugbkyk:GgNs09Y0fnCTTFgEFaBnowTOD-ZFYm3v@swan.rmq.cloudamqp.com/ubugbkyk
```


## How to subscribe to relevant message queues

DarkQ allows you to subscribe to an arbitrary number of queues via so called "routing keys". Each routing key is unique and has five properties:

1. name of sender (e.g. "phiweger")
2. country code (e.g. DE)
3. taxon status ("found" or "mystery")
4. taxon level (either one of superkingdom, phylum, class, order, family, genus, species, strain)
5. taxon name at that level (e.g. "Klebsiella" for genus) -- these are adapted from and must conform to the [GTDB r89](https://gtdb.ecogenomic.org/)

These queues are declared in `tags.csv`, where empty fields mean "all". For example, let's subscibe to three queues:

- all genomes from the Prochlorococcus genus
- all genomes sent by "user1" belonging to Klebsiella pneumoniae
- all genomes sent from Germany with an unknown taxonomy

```csv
name,country,status,level,taxon
,,,genus,Prochlorococcus
user1,,,species,Klebsiella pneumoniae
,DE,mystery,,
```

For published messages, these tags are automatically generated. Only the receiver needs to explicitly state the desired message tags. Routing keys act as filters to the messages received over the queue. DarkQ offers a second filter, that allows similarity-based genome filtering. This filter consists of a _Sequence Bloom Tree_ (SBT) of _MinHash_ signatures as generated using `sourmash index` (see above). It is declared in the `nextflow.config`.





