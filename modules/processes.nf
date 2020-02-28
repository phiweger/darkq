'''
Nextflow uses symlinks to represent all input files. However, when symlinks
are added to IPFS, they are different "things" than the original file they
point to. Therefore, we copy the symlinked file into the processes' workdir
first, and then add this original file to IPFS.

> By default, add should store the symlinks NOT the files. you can add a flag
to make the resolution happen if you want it to, and maybe a printed warning
for the user (to stderr) to use the flag if they meant to add the file.
-- https://github.com/ipfs/go-ipfs/issues/2839

https://stackoverflow.com/questions/21238570
'''
process p2p {
    // echo true

    input:
    tuple val(id), file(genome)

    output:
    tuple val(id), file('filehash.txt')

    """
    cp --remove-destination "\$(readlink ${genome})" ${genome}
    # cp ${genome} ${id}
    ipfs add ${genome} > filehash.txt 2> /dev/null
    """
}


process send {
    // echo true

    input:
    tuple val(id), file(genome), file(filehash), file(signature), file(taxonomy)
    file(db)
    
    script:
    """
    send.py --genome ${genome} --filehash ${filehash} --db ${db} --url ${params.url} --exchange ${params.exchange} --id ${params.id} --signature ${signature} --taxonomy ${taxonomy} --geo
    """
}


process sketch {
    // echo true

    input:
    tuple val(id), file(genome)

    output:
    tuple val(id), file("signature.json")

    """
    sourmash compute \
        -k ${params.k} --scaled ${params.scale} -o signature.json ${genome}
    """
}


'''
This process will load gigabytes of sourmash LCA database for each sample,
which is suboptimal. However, the in return for this, we get the error handling
and scaling of the workflow manager. We picked the latter.
'''
process taxonomy {
    // echo true

    input:
    tuple val(id), file(signature)
    file(db)

    output:
    tuple val(id), file('taxonomy.csv')

    """
    sourmash lca classify --db ${db} --query ${signature} > taxonomy.csv
    """
}


process receive_filter {
    // echo true
    // publishDir 'downloads', mode: 'copy', overwrite: true
    // Does not work bc/ seems the process has to exit first to publish

    input:
    file(db)
    file(dbhidden)
    file(tags)
    // This is the output, but because this is an infinite process, we have
    // to pass the output directory as input. Yeah, I know.

    script:
    """
    receive.py \
        --outdir ${params.receive} \
        --db ${db} \
        --threshold ${params.threshold} \
        --url ${params.url} \
        --exchange ${params.exchange} \
        --tags ${tags} \
        > ${params.report}
    """
}


process receive_nofilter {
    // echo true
    // publishDir 'downloads', mode: 'copy', overwrite: true
    // Does not work bc/ seems the process has to exit first to publish

    input:
    file(tags)

    script:
    """
    receive.py \
        --outdir ${params.receive} \
        --threshold ${params.threshold} \
        --url ${params.url} \
        --exchange ${params.exchange} \
        --tags ${tags} \
        > ${params.report}
    """
}
