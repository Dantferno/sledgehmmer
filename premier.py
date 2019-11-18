import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import subprocess
import threading
import time
import Bio.SeqIO
import Bio.SearchIO
import tkinter.ttk as ttk
import ttkwidgets #a installer
import ftplib
import os
import re


def parsehmmsearch(file):
    #Parse le fichier domtblout
    matrice = []
    if file=='':
        with open('tmp','r') as f:
            ff =f.readlines()
            for line in ff[3:-10]:
                fin = re.split(r"\s+",line)
                matrice.append(fin)
        return matrice
    else:
        with open(file,'r') as f:
            ff =f.readlines()
            for line in ff[3:-10]:
                fin = re.split(r"\s+",line)
                matrice.append(fin)
        return matrice


def check_maj(frame,button_maj):
    #cherche la derniere maj de Pfam-a.hmm et compare a celle local
    #si differente execute download_pfam si bouton appuye
    try:
        ftp = ftplib.FTP('ftp.ebi.ac.uk')
        ftp.login()
        ftp.cwd('/pub/databases/Pfam/current_release')
        reponse = []
        ftp.retrlines('LIST Pfam-A.hmm.gz', reponse.append)


        reponse = reponse[0].split()
        last_modified = '{0} {1} {2}'.format(reponse[-3],reponse[-4], reponse[-2])
        with open('./librairie/nbr_profile_pfam','r') as f:
            readf = f.readlines()
            nbr_profile = readf[0]
            current_release = readf[1].strip('\n')

        #affiche sur le GUI les informations
        button_maj.grid_forget()
        curlabel = tk.Label(frame, text='Version actuelle : {}'.format(current_release)).grid(row=1)
        nbrlabel = tk.Label(frame, text='Nombre de profile : {}'.format(nbr_profile)).grid(row=2)
        lastlabel = tk.Label(frame, text='derniere version : {}'.format(last_modified)).grid(row=3)

        #Si une nouvelle version a telecharge propose
        if last_modified != current_release:
            majbutton = tk.Button(frame, text='Mettre a jour', command=lambda:download_pfam(last_modified,ftp,frame)).grid(row=4)
        else:
            nomaj = tk.Label(frame,text='Aucune mise a jour disponible').grid(row=4)
            ftp.close()


    except Exception as e:
        errorlabel = tk.messagebox.showerror('Erreur de connection','Verifie votre connection a internet {}'.format(e))


def download_pfam(last_modified,ftp,frame):
    #telecharge la derniere version de pfam et compte le nbr de profile
    #enregistre le nbr de profile et la date de la derniere version dans nbr_profile_pfam
    frame.grid_forget()
    update_pfam = tk.Frame(wBestHMM)

    def download():
        with open('./librairie/Pfam-A.hmm.gz','wb') as handle:
            ftp.retrbinary('RETR Pfam-A.hmm.gz',handle.write)
        ftp.close()


    telechargement = tk.Label(update_pfam, text='La nouvelle librairie est en train d\'etre telecharge').grid()

    #Creer un bar de progres contenant la taille du fichier
    taille_fichier = ftp.size('Pfam-A.hmm.gz')
    progress_bar = ttk.Progressbar(update_pfam, length=650,maximum=taille_fichier)
    progress_bar.grid()
    update_pfam.grid()

    #Lance le telechargement sur un autre thread
    update_pfam.update()
    t1 = threading.Thread(target=download)
    t1.start()
    while t1.isAlive():
        update_pfam.update()
        progress_bar['value'] = os.path.getsize('./librairie/Pfam-A.hmm.gz')
    t1.join()

    #decompresse le fichier et supprime l'ancienne librairie
    gunzip = tk.Label(update_pfam, text='La nouvelle librairie est en train d\'etre decompresse').grid()
    os.remove('./librairie/Pfam-A.hmm')
    subprocess.call('gunzip ./librairie/Pfam-A.hmm.gz', shell=True)
    update_pfam.update()

    #supprime les anciens indexes et hmmpress la nouvelle librairie
    presslabel = tk.Label(update_pfam, text='La nouvelle librairie est en train d\' etre optimisé (hmmpress)').grid()
    update_pfam.update()
    pressfile = ['./librairie/Pfam-A.hmm.h3f','./librairie/Pfam-A.hmm.h3i','./librairie/Pfam-A.hmm.h3m','./librairie/Pfam-A.hmm.h3p']
    for i in pressfile:
        if os.path.exists(i):
            os.remove(i)
    subprocess.call('hmmpress ./librairie/Pfam-A.hmm',shell=True)

    #compte le nombre de modele
    with open('./librairie/Pfam-A.hmm','r') as f:
        count = 0
        for line in f:
            if line.startswith('//'):
                count +=1
    count_profile = tk.Label(update_pfam, text='La nouvelle librarie contient {} profiles'.format(count)).grid()

    #enregistre dans un fichier persistant le nombre de profile et la date de la nouvelle_librairie
    with open('./librairie/nbr_profile_pfam','w') as f:
        f.write(str(count)+'\n')
        f.write(last_modified)

    nouvelle_librairie = tk.Label(update_pfam, text='La nouvelle librarie est telecharge').grid()
    suivant = tk.Button(update_pfam, text='Lancer recherche', command=lambda:fenetre_suivante(update_pfam)).grid()
    import_resultat = tk.Button(update_pfam, text='Importer ses propres resultats').grid()

def troisieme_fenetrefunc(file):
    troisieme_fenetre = tk.Frame()

    #stock dans matrice les resultats parsé (une ligne -> une liste)
    matrice = parsehmmsearch(file)
    labelresultat = tk.Label(troisieme_fenetre, text='Resultat trouvé : {}'.format(len(matrice))).grid(row=1)

    def update_list(matrice,evalue,recouvrement,tree):
        j=0
        #verifie que la evalue est sous le bon format
        try:
            evalue = float(evalue)
        except ValueError:
            tk.messagebox.showerror(title='Erreur',message='La evalue doit etre un reel \nEcriture scientifique accepté sous la forme 1e-N')
            return False
        recouvrement = int(recouvrement)
        #Oublie l'ancien tableau et recreer le avec les conditions
        tree.grid_remove()
        tree = ttkwidgets.CheckboxTreeview(troisieme_fenetre, height=20)
        tree['columns']=('one','two','three','four','five','six','7','8','9','10','11','12','13')
        #tailles colonnes
        tree.column("#0",width=50)
        tree.column("one",width=100)
        tree.column("two",width=100)
        tree.column("three",width=100)
        tree.column('four',width=100)
        tree.column('five',width=100)
        tree.column('six',width=100)
        tree.column('7',width=100)
        tree.column('8',width=100)
        tree.column('9',width=100)
        tree.column('10',width=100)
        tree.column('11',width=100)
        tree.column('12',width=100)
        tree.column('13',width=100)
        #nom colonnes
        tree.heading('#0',text='select')
        tree.heading('one',text='target')
        tree.heading('two',text='tlen')
        tree.heading('three',text='query')
        tree.heading('four',text='qlen')
        tree.heading('five',text='evalue')
        tree.heading('six',text='score')
        tree.heading('7',text='#')
        tree.heading('8',text='of')
        tree.heading('9',text='c-evalue')
        tree.heading('10',text='hmm from')
        tree.heading('11',text='hmm to')
        tree.heading('12',text='ali to')
        tree.heading('13',text='ali from')
        for i in matrice:
            j+=1
            if float(i[6])<=evalue:
                tree.insert('',j,text='',values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],i[11],i[15],i[16],i[17],i[18]))
        tree.grid(row=2)


    #

    #creer une liste des resultats
    tree = ttkwidgets.CheckboxTreeview(troisieme_fenetre, height=20)
    tree['columns']=('one','two','three','four','five','six','7','8','9','10','11','12','13')
    #tailles colonnes
    tree.column("#0",width=50)
    tree.column("one",width=100)
    tree.column("two",width=100)
    tree.column("three",width=100)
    tree.column('four',width=100)
    tree.column('five',width=100)
    tree.column('six',width=100)
    tree.column('7',width=100)
    tree.column('8',width=100)
    tree.column('9',width=100)
    tree.column('10',width=100)
    tree.column('11',width=100)
    tree.column('12',width=100)
    tree.column('13',width=100)
    #nom colonnes
    tree.heading('#0',text='select')
    tree.heading('one',text='target')
    tree.heading('two',text='tlen')
    tree.heading('three',text='query')
    tree.heading('four',text='qlen')
    tree.heading('five',text='evalue')
    tree.heading('six',text='score')
    tree.heading('7',text='#')
    tree.heading('8',text='of')
    tree.heading('9',text='c-evalue')
    tree.heading('10',text='hmm from')
    tree.heading('11',text='hmm to')
    tree.heading('12',text='ali to')
    tree.heading('13',text='ali from')
    j=0


    for i in matrice:
        j+=1
        tree.insert('',j,text='',values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],i[11],i[15],i[16],i[17],i[18]))

    tree.grid()
    filtre_label = tk.Label(troisieme_fenetre,text='Filtre :').grid()
    #Choix evalue
    filtre_evalue_label = tk.Label(troisieme_fenetre,text='e-value inférieur à :').grid()
    filtre_evalue = tk.StringVar()
    filtre_evalue_entry = tk.Entry(troisieme_fenetre,textvariable=filtre_evalue).grid()

    #Choix recouvrement
    filtre_recouvrement_label = tk.Label(troisieme_fenetre,text='% recouvrement min :').grid()
    recouvrement = tk.Scale(troisieme_fenetre,from_=0,to=100,orient='horizontal')

    #bouton de mise a jour
    majbutton = tk.Button(troisieme_fenetre,text='Mettre à jour',command=lambda:update_list(matrice,filtre_evalue.get(),recouvrement.get(),tree)).grid(row=7)
    tk.Label(troisieme_fenetre).grid()
    #configuration
    def popup(tree):
        tk.messagebox.showinfo(title='coucou',message='{0}'.format(tree.get()))


    send_check = tk.Button(troisieme_fenetre,text='Ajouter a la base de donnee',command=lambda:popup(recouvrement))
    recouvrement.grid(row=6)
    send_check.grid(row=8)
    tk.Label(troisieme_fenetre).grid()

    troisieme_fenetre.grid(row=0, column=1,sticky='news')
    troisieme_fenetre.grid_rowconfigure(0, pad=50)

def deuxieme_fenetrefunc(macmd,file):
    #Deuxieme fenetre
    deuxieme_fenetre = tk.Frame(wBestHMM)


    #Affiche la commande execute
    nom_cmd = tk.Label(deuxieme_fenetre, text='Commande execute :').grid()
    cmd_label=tk.Label(deuxieme_fenetre, text=macmd)
    start_time = time.time()


    #Selon hmmcmd determine le nombre d'etape hmmsearch ->nbre de profil hmmscan_>nombre de seq
    if macmd.startswith('hmmsearch'):
        with open('./librairie/nbr_profile_pfam','r') as f:
            maxval = int(f.readlines()[0])
    else:
        with open(file, "r") as f:
            fasta = Bio.SeqIO.parse(f, "fasta")
            maxval = 0
            for i in fasta:
                maxval += 1

    #output dynamique dans output_text et progressbar
    progress_bar = ttk.Progressbar(deuxieme_fenetre, length=650,maximum=maxval)
    def popene(output_text,macmd,progress_bar):
        avancement = 0
        #ecris dans output_text l'output
        with subprocess.Popen("exec " + macmd, shell=True, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
            cancel_button = tk.Button(deuxieme_fenetre, text='Retour', command=lambda:cancel_popen(p)).grid()
            for line in p.stdout:
                if line.startswith('Query:'):
                    avancement += 1
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)
                    progress_bar['value'] = avancement
                    # progress_bar.update_idletasks()
                    # output_text.update_idletasks()
        if p.returncode !=0:
            tk.messagebox.showerror('Erreur', 'Une erreur s\'est produite lors de l\'execution')
        else:
            file=''
            tk.messagebox.showinfo('Succee', 'processe termine en {} secondes'.format(time.time() - start_time))
            suivant = tk.Button(deuxieme_fenetre,text='suivant',command=lambda:troisieme_fenetrefunc(file)).grid()

    def cancel_popen(p):
        #tue l
        p.kill()
        fenetre()



    output_text = tk.Text(deuxieme_fenetre, borderwidth=3, relief="sunken")

    #lance un thread separé pour popene afin de ne pas freeze le gui
    t1= threading.Thread(target=popene, args=(output_text,macmd,progress_bar))
    t1.start()

    #configuration du deuxieme frame
    cmd_label.grid(row=1)
    output_text.grid()
    progress_bar.grid()

    deuxieme_fenetre.grid(row=0, column=1,sticky='news')
    deuxieme_fenetre.grid_rowconfigure(0, pad=50)
    # deuxieme_fenetre.update_idletasks()

def fenetre():
    #frame de la premiere fenetre
    premiere_fenetre = tk.Frame(wBestHMM)
    #Rentrer un fichier fasta
    Labelinput=tk.Label(premiere_fenetre, text="Rentrer un fichier fasta")

    def Openfile():
        global filename
        filename = tk.filedialog.askopenfilename()
        nom_file = tk.Label(premiere_fenetre,text=filename).grid(row=2,column=1)


    browsebutton = tk.Button(premiere_fenetre, text="Parcourir", command=Openfile)

    #Choisir entre hmmsearch et hmmscan
    choicecmd = tk.StringVar()
    radiosearch =tk.Radiobutton(premiere_fenetre, text="hmmsearch", value="hmmsearch", var=choicecmd)
    radioscan =tk.Radiobutton(premiere_fenetre, text="hmmscan", value="hmmscan", var=choicecmd)

    #Choisir les options de la recherche
    LabelinputOptions=tk.Label(premiere_fenetre, text="Options:")

    LabelinputEvalue=tk.Label(premiere_fenetre, text="E-value")

    LabelinputCvalue=tk.Label(premiere_fenetre, text="C-value")
    evalue = tk.StringVar()
    eforEValue =tk.Entry(premiere_fenetre, width=10, justify='center',textvariable=evalue)

    eforCValue =tk.Entry(premiere_fenetre, width=10, justify='center')

    #envoye les informations
    Bsubmit= tk.Button(premiere_fenetre, text ="Envoyé", command=lambda:check_input(filename,choicecmd.get(),evalue.get()))

    #arrangement du layout
    premiere_fenetre.grid_columnconfigure(0, weight=1, minsize=20) #weight 1 permet de creer column vide
    premiere_fenetre.grid_columnconfigure(4, weight=1, minsize=20)
    premiere_fenetre.grid_rowconfigure(8, weight=1)
    Labelinput.grid(row=0, column=1,sticky='w')
    browsebutton.grid(row=1,column=1,sticky='w')
    radiosearch.grid(row=3, column=1,sticky='w')
    radioscan.grid(row=4, column=1,sticky='w')
    LabelinputOptions.grid(row=5, column=1,sticky='w')
    LabelinputEvalue.grid(row=6, column=1,sticky='w')
    LabelinputCvalue.grid(row=7, column=1,sticky='w')
    eforEValue.grid(row=6, column=2)
    eforCValue.grid(row=7, column=2)
    Bsubmit.grid(row=8, column=3,sticky='e')
    eforEValue.insert(0,"10")
    eforCValue.insert(0,"10")
    Labelinput.config(font=("song ti", 14))
    LabelinputOptions.config(font=("song ti", 14))
    #Ajoute pour chaque ligne un padding
    for i in range(12):
        if i !=2:
            premiere_fenetre.grid_rowconfigure(i, pad=50)
    premiere_fenetre.grid_columnconfigure(3, pad=100)
    premiere_fenetre.grid(row=0, column=1,sticky='news')

def check_fasta(file):
    #Check si le fasta est valide
    try:
        with open(file, "r") as f:
            fasta = Bio.SeqIO.parse(f, "fasta")
            return any(fasta)  # False when `fasta` is empty, i.e. wasn't a FASTA file
    except FileNotFoundError:
        return False

def check_input(file,choicecmd,evalue):
    #check que l'input est un fasta, que la cmd est selectionne et que la evalue est valable
    try:
        evalue = float(evalue)
        evalue_ok = True
    except ValueError:
        evalue_ok = False

    if check_fasta(file) is False:
        tk.messagebox.showerror('Erreur', 'Merci de specifier un fichier au format fasta')
    elif choicecmd == '':
        tk.messagebox.showerror('Erreur', 'Merci de specifier hmmsearch ou hmmscan')
    elif evalue_ok is False:
        tk.messagebox.showerror('Erreur', 'Merci de specifier une evalue valable')
    else:
        if choicecmd=='hmmsearch':
            command = '{0} --domtblout tmp --noali -E {2} ./librairie/Pfam-A.hmm {1} '.format(choicecmd,filename,evalue)
        elif choicecmd=='hmmscan':
            command = '{0} --domtblout tmp --noali -E {2} ./librairie/Pfam-A.hmm {1} '.format(choicecmd,filename,evalue)
        deuxieme_fenetrefunc(command,file)

def accueil_fenetre():
    accueil = tk.Frame(wBestHMM)



    maj = tk.Button(accueil, text='Chercher une mise a jour',command=lambda:check_maj(accueil,maj))
    suivant = tk.Button(accueil, text='Lancer recherche', command=lambda:fenetre_suivante(accueil))
    import_resultat = tk.Button(accueil, text='Importer ses propres domtblout',command=lambda:OpenPersonalFile(accueil))
    maj.grid(row=5)
    suivant.grid(row=6)
    import_resultat.grid(row=7)
    accueil.grid()

def fenetre_suivante(frame):
    frame.grid_forget()
    fenetre()

def OpenPersonalFile(frame):
    persoFile = tk.filedialog.askopenfilename()
    frame.grid_forget()
    troisieme_fenetrefunc(persoFile)


#debut du script
filename = ''

##Parametre de la fenetre
wBestHMM=tk.Tk()
wBestHMM.title("BestHMM")
# wBestHMM.geometry("1080x720")
wBestHMM.minsize(480,360)
# wBestHMM.config(background="#ffcc99")
accueil_fenetre()
wBestHMM.mainloop()
