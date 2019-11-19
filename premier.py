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


def parsehmmsearch(frame_actuelle,file):
    '''Creer une matrice contenant le domtblout parsé,
    verifie les dimensions de la matrice afin de s'assurer que le
    fichier fournis est un domtblout sinon envoie un message d'erreur,
    finalement retourne la matrice si les conditions sont rencontré
    '''
    matrice = []
    with open(file,'r') as f:
        ff =f.readlines()
        for line in ff[3:-10]:
            fin = re.split(r"\s+",line)
            matrice.append(fin)
    try:
        #25 colonne pour hmmscan, 28 pour hmmsearch
        if len(matrice[0]) == 25 or len(matrice[0])==28:
            return matrice
        else:
            tk.messagebox.showerror('fichier non conforme',
            'Merci de fournir un fichier au format domtblout')
            frame_actuelle.grid_forget()
            accueil_fenetre()
    except IndexError:
        tk.messagebox.showerror('fichier non conforme',
        'Merci de fournir un fichier au format domtblout')
        frame_actuelle.grid_forget()
        accueil_fenetre()


def check_maj(frame,button_maj):
    '''Cherche la derniere maj de Pfam-a.hmm sur le serveur FTP et compare
    a celle local si differente execute download_pfam si bouton MAJ appuye
    '''
    try:
        #si une erreur intervient dans ce block un message d'erreur est retourne (erreur de connection)
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
        curlabel = tk.Label(frame,
        text='Version actuelle : {}'.format(current_release)).grid(row=1)
        nbrlabel = tk.Label(frame,
        text='Nombre de profile : {}'.format(nbr_profile)).grid(row=2)
        lastlabel = tk.Label(frame,
        text='derniere version : {}'.format(last_modified)).grid(row=3)

        #Si une nouvelle version a telecharge propose
        if last_modified != current_release:
            majbutton = tk.Button(frame, text='Mettre a jour',
            command=lambda:download_pfam(last_modified,ftp,frame)).grid(row=4)

        else:
            nomaj = tk.Label(frame,
            text='Aucune mise a jour disponible',fg='red').grid(row=4)
            ftp.close()


    except Exception as e:
        errorlabel = tk.messagebox.showerror('Erreur de connection',
        'Verifie votre connection a internet {}'.format(e))


def download_pfam(last_modified,ftp,frame):
    '''telecharge la derniere version de pfam et compte le nbr de profile
    enregistre le nbr de profile et la date de la derniere version
    dans nbr_profile_pfam
    '''
    frame.grid_forget()
    update_pfam = tk.Frame(wBestHMM)

    def download():
        with open('./librairie/Pfam-A.hmm.gz','wb') as handle:
            ftp.retrbinary('RETR Pfam-A.hmm.gz',handle.write)
        ftp.close()


    telechargement = tk.Label(update_pfam,
    text='La nouvelle librairie est en train d\'etre telecharge').grid()

    #Creer un bar de progres contenant la taille du fichier
    taille_fichier = ftp.size('Pfam-A.hmm.gz')
    progress_bar = ttk.Progressbar(update_pfam,
    length=650,maximum=taille_fichier)
    progress_bar.grid()
    update_pfam.grid()

    #Lance le telechargement sur un autre thread
    update_pfam.update()
    t1 = threading.Thread(target=download)
    t1.start()
    #Pendant le telechargement la barre de progres augmente conjointement
    #avec la taille de la librairie telecharge
    while t1.isAlive():
        update_pfam.update()
        progress_bar['value'] = os.path.getsize('./librairie/Pfam-A.hmm.gz')
    t1.join()

    #supprime l'ancienne librairie et decompresse le fichier
    gunzip = tk.Label(update_pfam,
    text='La nouvelle librairie est en train d\'etre decompresse').grid()
    os.remove('./librairie/Pfam-A.hmm')
    subprocess.call('gunzip ./librairie/Pfam-A.hmm.gz', shell=True)
    update_pfam.update()

    #supprime les anciens indexes et hmmpress la nouvelle librairie
    presslabel = tk.Label(update_pfam,
    text='La nouvelle librairie est en train d\' etre optimisé (hmmpress)').grid()
    update_pfam.update()
    pressfile = ['./librairie/Pfam-A.hmm.h3f',
    './librairie/Pfam-A.hmm.h3i',
    './librairie/Pfam-A.hmm.h3m',
    './librairie/Pfam-A.hmm.h3p']
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
    count_profile = tk.Label(update_pfam,
    text='La nouvelle librarie contient {} profiles'.format(count)).grid()

    #enregistre dans un fichier persistant le nombre de profile
    #et la date de la nouvelle_librairie
    with open('./librairie/nbr_profile_pfam','w') as f:
        f.write(str(count)+'\n')
        f.write(last_modified)

    nouvelle_librairie = tk.Label(update_pfam,
    text='La nouvelle librarie est telecharge').grid()
    suivant = tk.Button(update_pfam,
    text='Lancer recherche', command=lambda:retour_recherche(update_pfam)).grid()
    import_resultat = tk.Button(update_pfam,
    text='Importer ses propres resultats').grid()

def troisieme_fenetrefunc(file):
    '''Fenetre affichant les resultats sous la forme d'un tableau '''
    troisieme_fenetre = tk.Frame()

    #stock dans matrice les resultats parsé (une ligne -> une liste)
    matrice = parsehmmsearch(troisieme_fenetre,file)
    labelresultat = tk.Label(troisieme_fenetre,
    text='Resultat trouvé : {}'.format(len(matrice)))

    def update_list(matrice,evalue,recouvrement,tree,labelresultat):
        '''Efface l'ancien tableau et le reconstruit en appliquant
        les conditions : evalue max et recouvrement mini'''
        j=0
        #verifie que la evalue est sous le bon format sinon retourne un message d'erreur
        try:
            evalue = float(evalue)
        except ValueError:
            tk.messagebox.showerror(title='Erreur',
            message='La evalue doit etre un reel \nEcriture scientifique accepté sous la forme 1e-N')
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
        #Pour chaque ligne du domtblout, les inseres si elles respectent les
        #conditions donnees
        passe_selection =0
        for i in matrice:
            j+=1
            if float(i[6])<=evalue:
                if int(recouvrement) <= (int(i[16])-int(i[15]))/int(i[5])*100:
                    passe_selection += 1
                    tree.insert('',j,text='',
                    values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                    i[11],i[15],i[16],i[17],i[18]))
        #Met a jour le label indiquant le nombre de resultat
        labelresultat.grid_forget()
        labelresultat = tk.Label(troisieme_fenetre,
        text='Resultat trouvé : {0}, après filtrage : {1}'.format(len(matrice),passe_selection))
        labelresultat.grid(row=1,columnspan=3,pady=20)
        tree.grid(row=2,columnspan=3)

    #Creer un tableau des resultats
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
    #Insere toutes les lignes du domtblout
    for i in matrice:
        j+=1
        tree.insert('',j,text='',
        values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],i[11],i[15],i[16],i[17],i[18]))

    tree.grid(row=2,columnspan=3)
    filtre_label = tk.Label(troisieme_fenetre,text='').grid(row=3)
    #Choix evalue
    filtre_evalue_label = tk.Label(troisieme_fenetre,
    text='e-value inférieur à :').grid(row=4,column=0)
    filtre_evalue = tk.StringVar()
    filtre_evalue_entry = tk.Entry(troisieme_fenetre,
    textvariable=filtre_evalue,width=10, justify='center')
    filtre_evalue_entry.insert(0,'10')
    filtre_evalue_entry.grid(row=5,column=0)
    #Choix recouvrement
    filtre_recouvrement_label = tk.Label(troisieme_fenetre,
    text='% recouvrement min :').grid(row=4,column=1)
    recouvrement = tk.Scale(troisieme_fenetre,
    from_=0,to=100,orient='horizontal')

    #bouton de mise a jour
    majbutton = tk.Button(troisieme_fenetre,
    text='Mettre à jour',
    command=lambda:update_list(matrice,filtre_evalue.get(),recouvrement.get(),tree,labelresultat)).grid(row=5,column=2)
    tk.Label(troisieme_fenetre).grid()

    def add_to_DB(tree):
        '''Ajouter les lignes selectionne a la database mysql'''
        tk.messagebox.showinfo(title='coucou',message='{0}'.format(tree.get()))

    #Bouton d'ajout a la DB
    send_check = tk.Button(troisieme_fenetre,
    text='Ajouter a la base de donnee',
    command=lambda:add_to_DB(recouvrement))
    #Bouton retour recherche
    NouvelleRecherche = tk.Button(troisieme_fenetre,
    text='Nouvelle recherche',
    command=lambda:retour_recherche(troisieme_fenetre))
    #bouton retour accueil
    Accueil = tk.Button(troisieme_fenetre,
    text='Retour accueil',
    command=lambda:retour_accueil(troisieme_fenetre))
    #Configuration du layout
    labelresultat.grid(row=1,columnspan=3,pady=20)
    recouvrement.grid(row=5,column=1)
    send_check.grid(row=6,column=1)
    NouvelleRecherche.grid(row=6,column=2)
    Accueil.grid(row=6,column=0)
    tk.Label(troisieme_fenetre).grid()
    troisieme_fenetre.grid(row=0, column=1,sticky='news')
    troisieme_fenetre.grid_rowconfigure(0, pad=50)
    troisieme_fenetre.grid_rowconfigure(6, pad=50)

def deuxieme_fenetrefunc(macmd,file):
    '''deuxieme_fenetre affichant les modeles en train d'etre query pour
    hmmsearch ou les sequences query pour hmmscan avec une barre de progres
    '''
    deuxieme_fenetre = tk.Frame(wBestHMM)


    #Affiche la commande execute
    nom_cmd = tk.Label(deuxieme_fenetre, text='Commande execute :').grid()
    cmd_label=tk.Label(deuxieme_fenetre, text=macmd)
    start_time = time.time()


    #Selon hmmcmd determine le nombre d'etape total et stock dans maxval
    #hmmsearch ->nbre de profil hmmscan_>nombre de seq
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
        '''Execute la recherche hmmsearch ou scan (macmd), ecrit
        l'output dans output_text et augmente conjointement la barre de progres
        '''
        avancement = 0
        #ecris dans output_text l'output
        with subprocess.Popen("exec " + macmd, shell=True,
        stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
            cancel_button = tk.Button(deuxieme_fenetre,
            text='Retour', command=lambda:cancel_popen(p)).grid(row=4,
            column=0,sticky='w',pady=25,padx=25)
            for line in p.stdout:
                if line.startswith('Query:'):
                    avancement += 1
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)
                    progress_bar['value'] = avancement

        #Si la commande rencontre un probleme affiche un message d'Erreur
        #sinon execute la troisieme fenetre en appuyant sur le bouton suivant
        if p.returncode !=0:
            tk.messagebox.showerror('Erreur',
            'Une erreur s\'est produite lors de l\'execution')
        else:
            #A partir d'ici le fichier reference a l'output afin de rejoindre
            #l'importation d'un fichier personnel
            file='tmp'
            tk.messagebox.showinfo('Succee',
            'processe termine en {} secondes'.format(time.time() - start_time))
            suivant = tk.Button(deuxieme_fenetre,text='suivant',
            command=lambda:aller_troisieme_fenetre(deuxieme_fenetre,file)).grid(row=4,
            column=1,sticky='e',pady=25,padx=25)

    def cancel_popen(p):
        '''tue le thread si bouton retour est appuye et retourne sur
        la fenetre de recherche'''
        p.kill()
        fenetre()


    #Cadre text recevant l'output de la commande
    output_text = tk.Text(deuxieme_fenetre, borderwidth=3, relief="sunken")

    #lance un thread separé pour popene afin de ne pas freeze le gui
    t1= threading.Thread(target=popene, args=(output_text,macmd,progress_bar))
    t1.start()

    #configuration du deuxieme frame
    cmd_label.grid(row=1,columnspan=2)
    output_text.grid(row=2,columnspan=2)
    progress_bar.grid(row=3,columnspan=2)

    deuxieme_fenetre.grid(row=0, column=1,sticky='news')
    deuxieme_fenetre.grid_rowconfigure(0, pad=50)


def fenetre():
    '''Fenetre de choix de la recherche, propose de choisir un fichier
    fasta, hmmsearch ou hmmscan, et une evalue seuil
    '''

    def Openfile():
        '''Demande a l'utilisateur de choisir un fichier'''
        global filename
        filename = tk.filedialog.askopenfilename()
        nom_file = tk.Label(premiere_fenetre,text=filename).grid(row=2,column=1)

    premiere_fenetre = tk.Frame(wBestHMM)
    #Rentrer un fichier fasta
    Labelinput=tk.Label(premiere_fenetre, text="Rentrer un fichier fasta")
    browsebutton = tk.Button(premiere_fenetre, text="Parcourir", command=Openfile)

    #Choisir entre hmmsearch et hmmscan
    choicecmd = tk.StringVar()
    radiosearch =tk.Radiobutton(premiere_fenetre, text="hmmsearch", value="hmmsearch", var=choicecmd)
    radioscan =tk.Radiobutton(premiere_fenetre, text="hmmscan", value="hmmscan", var=choicecmd)

    #Choisir les options de la recherche
    LabelinputOptions=tk.Label(premiere_fenetre, text="Options:")
    LabelinputEvalue=tk.Label(premiere_fenetre, text="E-value :")
    LabelinputCvalue=tk.Label(premiere_fenetre, text="C-value :")
    evalue = tk.StringVar()
    eforEValue =tk.Entry(premiere_fenetre, width=10, justify='center',textvariable=evalue)
    eforCValue =tk.Entry(premiere_fenetre, width=10, justify='center')

    #Boutton pour envoyer les informations
    Bsubmit= tk.Button(premiere_fenetre, text ="Envoyé",
    command=lambda:check_input(filename,choicecmd.get(),evalue.get(),premiere_fenetre))

    #Bouton pour retourner a l'accueil
    Accueil= tk.Button(premiere_fenetre, text ="Retour accueil",
    command=lambda:retour_accueil(premiere_fenetre))
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
    Accueil.grid(row=8,column=1,sticky='w')
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
    '''Check si le fasta est valide en utilisant biopython'''
    try:
        with open(file, "r") as f:
            fasta = Bio.SeqIO.parse(f, "fasta")
            return any(fasta)  # False when `fasta` is empty, i.e. wasn't a FASTA file
    except FileNotFoundError:
        return False

def check_input(file,choicecmd,evalue,frame):
    '''Verifie que l'input est un fasta, que la cmd est selectionne
    et que la evalue est valable. Si les conditions sont rencontré,
    deuxieme_fenetrefunc() est execute avec la commande adequate
    '''
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
        frame.grid_forget()
        deuxieme_fenetrefunc(command,file)

def accueil_fenetre():
    '''Fenetre d'accueil, propose de mettre a jour, lancer une
    recherche ou importer ces propres resultats
    '''
    accueil = tk.Frame(wBestHMM)
    maj = tk.Button(accueil,
    text='Chercher une mise a jour',command=lambda:check_maj(accueil,maj))
    suivant = tk.Button(accueil,
    text='Lancer recherche', command=lambda:retour_recherche(accueil))
    import_resultat = tk.Button(accueil,
    text='Importer ses propres domtblout',command=lambda:OpenPersonalFile(accueil))
    maj.grid(row=5)
    suivant.grid(row=6)
    import_resultat.grid(row=7,padx=30)
    for i in range(5,8):
        accueil.grid_rowconfigure(i, pad=50)
    accueil.grid()

def retour_recherche(frame):
    '''Permet de retourner a la fenetre de recherche depuis
    n'importe quelle autre fenetre
    '''
    frame.grid_forget()
    fenetre()

def retour_accueil(frame):
    '''Permet de retourner a la fenetre d'accueil depuis
    n'importe quelle autre fenetre
    '''
    frame.grid_forget()
    accueil_fenetre()

def aller_troisieme_fenetre(frame,file):
    frame.grid_forget()
    troisieme_fenetrefunc(file)

def OpenPersonalFile(frame):
    '''Commande execute si l'utilisateur decide d'importer ces propres
    resultats, lance la fenetre d'affichage des resultats avec
    le fichier selectionné
    '''
    persoFile = tk.filedialog.askopenfilename()
    #Test si un fichier a ete choisi, tkinter.filedialog return () ou ''
    #si cancel selectionne
    if str(persoFile) != '()' and str(persoFile) != '':
        frame.grid_forget()
        troisieme_fenetrefunc(persoFile)


#debut du script
filename = ''
##Parametre de la fenetre
wBestHMM=tk.Tk()
wBestHMM.title("BestHMM")
# wBestHMM.geometry("1080x720")
# wBestHMM.minsize(480,360)
# wBestHMM.config(background="#ffcc99")
accueil_fenetre()
wBestHMM.mainloop()
