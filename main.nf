nextflow.enable.dsl = 2

include {p2p; send; sketch; taxonomy; receive_filter; receive_nofilter} from './modules/processes.nf'

def helpMessage() {
    log.info"""
    Usage:

    # Start the IPFS daemon
    ipfs daemon &
    
    # Start the local RabbitMQ server if no url
    rabbitmq-server &
    
    # The typical command for running the pipeline is as follows:
    nextflow main.nf --help
    nextflow main.nf --url localhost --exchange foobar
    nextflow main.nf --filter false
    
    Mandatory arguments:
      --url                         {localhost, <url>}
      --exchange <name>             Name of the remote RabbitMQ exchange
      
    Options:
      --lca                         LCA database
    """.stripIndent()
}


// Show help message
if (params.help){
    helpMessage()
    exit 0
}

if( !nextflow.version.matches('20.+') ) {
    println "This workflow requires Nextflow version 20.X or greater -- You are running version $nextflow.version"
    exit 1
}

// Check if IPFS daemon is running:
file(params.p2p_daemon, hidden: true, checkIfExists: true)
lca = file(params.lca, checkIfExists: true)
tags = file(params.tags, checkIfExists: true)


workflow {

    // https://www.nextflow.io/docs/latest/channel.html#watchpath
    // batch:  .fromPath(params.send)
    // stream: .watchPath(params.send, 'create,modify')
    genomes_ch = Channel
        .watchPath(params.send, 'create,modify')
        .map { file -> tuple(file.baseName, file) }
        .unique()
        // file.name, file.simpleName, file.baseName
        // https://github.com/nextflow-io/nextflow/issues/278

    p2p(genomes_ch)
    
    sketch(genomes_ch)
    taxonomy(sketch.out, lca)
    
    send_ch = genomes_ch.join(p2p.out).join(sketch.out).join(taxonomy.out)
    send(send_ch, lca)

    if (params.filter){
        receive_filter(
            file(params.filter.sbt), 
            file(params.filter.sbt_hidden),
            tags)
    } else {
        receive_nofilter(tags)
    }

}
