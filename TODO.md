## TODO

[ ] exclude downloading self genomes (by passing a UID to the minhash sig that identifies genomes as self, then check for this in receive)

---

[ ] automatic routing key generation

---

[ ] allow download=False in receive
 
---

test cases:

- don't send, only receive
- receive later (offline at moment of send)
- send x, routing key rk false, no receive
- send x, rk true, filter, receive
- send x, rk true, filter, no receive
- send x, rk true, no filter, receive
- send x, rk true, no filter, no receive

---

[ ] what does routing key look like?

username.tag.location

e.g.

`*.*.germany.klebsiella_pneumoniae.#`

`*.outbreak.*.*.klebsiella.#`

(LineagePair(rank='superkingdom', name='Bacteria'), LineagePair(rank='phylum', name='Proteobacteria'), LineagePair(rank='class', name='Gammaproteobacteria'), LineagePair(rank='order', name='Pseudomonadales'), LineagePair(rank='family', name='Moraxellaceae'), LineagePair(rank='genus', name='Acinetobacter'), LineagePair(rank='species', name='Acinetobacter baumannii'))

> You can create multiple bindings: [...] -- https://www.rabbitmq.com/tutorials/tutorial-five-python.html

https://stackoverflow.com/questions/50679145/how-to-match-the-routing-key-with-binding-pattern-for-rabbitmq-topic-exchange-us

Don't expose the routing key but parse, e.g. "country": "Germany", "genus": "Acinetobacter" ...

superkingdom,phylum,class,order,family,genus,species,strain

---

[ ] optional filter w/ SBT -- can be turned off to "just" receive genomes

---

[ ] use our and becker data to illustrate the case -- rki seq A, we seq B, get to reconstruct

---

[ ] in receive, check routing key for match to GTDB syntax

---

[ ] have one key in routing key that is "found" or "notfound" so one can get weird samples not seen yet

---

[ ] verify what's detection limit of minhash (k=51, ...) -- study design?

get outbreaks from lit -- what is the minimum similarity in all-vs-all comparison? boxplot (each pair a point, y sim, x dataset) -- set params so we get 95% of cases correct

dimensions:

- k = 31, 51
- scaled = 1000, 10000 (less space for message needed)
- reads, assemblies
- containment, similarity

---

[ ] https://www.rabbitmq.com/production-checklist.html

---

[ ] log and check to not download messages multiple times -- also note if the genome is not available and retry later if need be

---

[ ] one folder in receive for each routing key? optional?

---

[ ] TODO: add to manuscript: deduplication included