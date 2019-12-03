install: BestHMM.py
	mkdir librairie
	cd librairie; \
	wget ftp://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz; \
	gunzip Pfam-A.hmm.gz; \
	hmmpress Pfam-A.hmm
	python nombre_profil.py
