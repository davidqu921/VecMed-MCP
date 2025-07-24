esearch -db pubmed -query "rare disease AND 2015:2025[dp]" | \
efetch -format uid > pmid.txt
# split -l 1000 pmid.txt pmid_batch_