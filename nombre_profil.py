import ftplib

#si une erreur intervient dans ce block un message d'erreur est retourne (erreur de connection)
ftp = ftplib.FTP('ftp.ebi.ac.uk')
ftp.login()
ftp.cwd('/pub/databases/Pfam/current_release')
reponse = []
ftp.retrlines('LIST Pfam-A.hmm.gz', reponse.append)


reponse = reponse[0].split()
#Stock la date de derniere modification dans le fichier nbr_profile
last_modified = '{0} {1} {2}'.format(reponse[-3],reponse[-4], reponse[-2])

with open('./librairie/Pfam-A.hmm','r') as f:
    count = 0
    for line in f:
        if line.startswith('//'):
            count +=1


with open('./librairie/nbr_profile_pfam','w') as w:
    w.write(str(count)+'\n')
    w.write(last_modified)
