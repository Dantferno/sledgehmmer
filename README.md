# BestHMM
BestHMM is a GUI for hmmscan and hmmsearch analysis against the latest Pfam library.
It allows visualisation of the results in a table view using Tkinter.
Domains can be filtered after the analysis using an E-value, the minimum coverage of the profile hmm and a redondant option.
Selected items from the table can be added to a custom MySQL database.

A web interface is also available to visualize the results at : http://hugo.croizer.etu.perso.luminy.univ-amu.fr/besthmm/interfaceweb.php


## Installation
You must have hmmer for BestHMM to work.
Installation depends on your package manager.
For Ubuntu :
```bash
sudo apt install hmmer
```

Once hmmer is installed just run this in the BestHMM directory
```make
make install
```
## Required :
Linux

hmmer

python>=3

The following library will be installed from the make file :

ttkwidgets

ttkthemes

mysql-connector-python

Biopython

gerer redondance
transformer update window in class
ask databse information OK
curseur maj

site:
plot historique des seq ajout
login page
couleur domaines
recouvrement moyen max min
cle triple
improve table
