import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog
import ttkthemes #a installer
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
from mysqlconnect import *

class Accueil(ttk.Frame):
    '''Fenetre d'accueil, propose de mettre a jour, lancer une
    recherche ou importer ces propres resultats
    '''
    def __init__(self,master):
        ttk.Frame.__init__(self, master)
        self.master = master

        self.photo = tk.PhotoImage(master=self,file='./prot.png')
        self.labelphoto= tk.Label(self,image=self.photo)
        self.labelphoto.image = self.photo
        self.labelphoto.grid(row=1,columnspan=3)

        self.maj = ttk.Button(self,text='Chercher une mise à jour',command=self.check_maj)
        self.maj.grid(row=5,column=0)
        self.recherche = ttk.Button(self,text='Lancer une recherche',command=self.fenetre_recherche)
        self.recherche.grid(row=5,column=1)
        self.import_resultat = ttk.Button(self,text='Importer résultats',command=self.OpenPersonalFile)
        self.import_resultat.grid(row=5,column=2)
        self.grid()

    def fenetre_recherche(self):
        '''Permet d'aller a la fenetre de recherche'''
        self.grid_forget()
        Recherche(self.master)

    def check_maj(self):
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
            #Stock la date de derniere modification dans le fichier nbr_profile
            self.last_modified = '{0} {1} {2}'.format(reponse[-3],reponse[-4], reponse[-2])

            try :
                with open('./librairie/nbr_profile_pfam','r') as f:
                    readf = f.readlines()
                    nbr_profile = readf[0]
                    current_release = readf[1].strip('\n')
            except FileNotFoundError:
                tk.messagebox.showerror('Pfam','Merci d\'éxécuter le makefile afin de compléter l\'installation')
                return

            #affiche sur le GUI les informations
            self.maj.grid_forget()
            tk.messagebox.showinfo('Mise à jour',
            'Version actuelle : {0}\n\nNombre de profiles : {1}\nDerniere version : {2}'.format(
            current_release,nbr_profile,self.last_modified))

            #Si une nouvelle version a telecharge propose
            if self.last_modified != current_release:
                self.majbutton = ttk.Button(self, text='Actualiser',
                command=lambda:download_pfam(self,ftp)).grid(row=5,column=0)

            else:
                nomaj = ttk.Label(self,
                text='Aucune mise a jour disponible').grid(row=5,column=0)
                ftp.close()

        except Exception as e:

            errorlabel = tk.messagebox.showerror('Erreur de connection',
            'Verifie votre connection a internet {}'.format(e))


    def download_pfam(self,ftp):
        '''telecharge la derniere version de pfam et compte le nbr de profile,
        enregistre le nbr de profile et la date de la derniere version
        dans nbr_profile_pfam, Affiche une nouvelle fenetre indiquant
        la progression du telechargement et le nbr de profile du nouveau fichier
        '''
        self.grid_forget()
        update_pfam = ttk.Frame(wBestHMM)

        def download():
            '''Telecharge Pfam-a depuis le serveur ftp'''
            with open('./librairie/Pfam-A.hmm.gz','wb') as handle:
                ftp.retrbinary('RETR Pfam-A.hmm.gz',handle.write)
            ftp.close()


        telechargement = ttk.Label(update_pfam,
        text='La nouvelle librairie est en train d\'etre telecharge').grid(pady=50,padx=20)

        #Creer un bar de progres contenant la taille du fichier
        taille_fichier = ftp.size('Pfam-A.hmm.gz')
        progress_bar = ttk.Progressbar(update_pfam,
        length=650,maximum=taille_fichier)
        progress_bar.grid(pady=50,padx=20)
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
        gunzip = ttk.Label(update_pfam,
        text='La nouvelle librairie est en train d\'etre decompresse').grid()
        os.remove('./librairie/Pfam-A.hmm')
        subprocess.call('gunzip ./librairie/Pfam-A.hmm.gz', shell=True)
        update_pfam.update()

        #supprime les anciens indexes et hmmpress la nouvelle librairie
        presslabel = ttk.Label(update_pfam,
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
        count_profile = ttk.Label(update_pfam,
        text='La nouvelle librarie contient {} profiles'.format(count)).grid()

        #enregistre dans un fichier persistant le nombre de profile
        #et la date de la nouvelle_librairie
        with open('./librairie/nbr_profile_pfam','w') as f:
            f.write(str(count)+'\n')
            f.write(self.last_modified)

        nouvelle_librairie = ttk.Label(update_pfam,
        text='La nouvelle librarie est telecharge').grid()
        suivant = ttk.Button(update_pfam,
        text='Lancer recherche', command=lambda:fenetre_recherche(self)).grid()
        import_resultat = ttk.Button(update_pfam,
        text='Importer ses propres resultats').grid()

    def OpenPersonalFile(self):
        '''Commande execute si l'utilisateur decide d'importer ces propres
        resultats, lance la fenetre d'affichage des resultats avec
        le fichier selectionné
        '''
        persoFile = tk.filedialog.askopenfilename()
        #Test si un fichier a ete choisi, tkinter.filedialog return () ou ''
        #si cancel selectionne
        try:
            with open(persoFile) as f :
                f = f.readlines()
                if 'domtblout' in f[-4]:
                    self.grid_forget()
                    Results(self.master,persoFile)
                else:
                    tk.messagebox.showerror('Erreur',
                    'Merci d\'indiquer un fichier au format domtblout')
        except :
            tk.messagebox.showerror('Erreur',
            'Merci d\'indiquer un fichier au format domtblout')

class Recherche(ttk.Frame):
    '''Fenetre de choix de la recherche, propose de choisir un fichier
    fasta, hmmsearch ou hmmscan, et une evalue seuil
    '''
    def __init__(self,master):
        ttk.Frame.__init__(self, master)
        self.master = master
        self.filename = ''
        self.command = ''

        #image hmmer
        self.photo = tk.PhotoImage(master = self,file='hmmer_logo.png')
        self.labelphoto = tk.Label(self,image=self.photo)
        self.labelphoto.image = self.photo
        self.labelphoto.grid(row=0,column=1,columnspan=3)
        #Rentrer un fichier fasta
        self.Labelinput=ttk.Label(self, text="Rentrer un fichier fasta")
        self.Labelinput.grid(row=1, column=1,sticky='w',columnspan=2)
        self.browsebutton = ttk.Button(self, text="Parcourir", command=self.Openfile)
        self.browsebutton.grid(row=2,column=1,sticky='w')
        self.label_filename = ttk.Label(self, text="")
        self.label_filename.grid(row=3,column=1,sticky='w',columnspan=3)
        #Choisir entre hmmsearch et hmmscan
        self.choicecmd = tk.StringVar()
        self.radiosearch =ttk.Radiobutton(self, text="hmmsearch", value="hmmsearch", var=self.choicecmd)
        self.radiosearch.grid(row=4, column=1,sticky='w')
        self.radioscan =ttk.Radiobutton(self, text="hmmscan", value="hmmscan", var=self.choicecmd)
        self.radioscan.grid(row=5, column=1,sticky='w')

        #Choisir les options de la recherche
        self.LabelinputOptions=ttk.Label(self, text="Options:")
        self.LabelinputOptions.grid(row=6, column=1,sticky='w')
        self.LabelinputEvalue=ttk.Label(self, text="E-value :")
        self.LabelinputEvalue.grid(row=7, column=1,sticky='w')
        self.LabelinputCvalue=ttk.Label(self, text="Domaine E-value :")
        self.LabelinputCvalue.grid(row=8, column=1,sticky='w')
        self.evalue = tk.StringVar()
        self.domevalue = tk.StringVar()
        self.eforEValue =ttk.Entry(self, width=10, justify='center',textvariable=self.evalue)
        self.eforEValue.grid(row=7, column=2)
        self.eforCValue =ttk.Entry(self, width=10, justify='center',textvariable=self.domevalue)
        self.eforCValue.grid(row=8, column=2)
        #Boutton pour envoyer les informations
        self.Bsubmit= ttk.Button(self, text ="Envoyé",
        command=self.check_input)
        self.Bsubmit.grid(row=9, column=3,sticky='e')

        #Bouton pour retourner a l'accueil
        self.Accueil= ttk.Button(self, text ="Retour accueil",
        command=self.fenetre_accueil)
        self.Accueil.grid(row=9,column=1,sticky='w')


        self.eforEValue.insert(0,"10")
        self.eforCValue.insert(0,"10")

        #Ajoute pour chaque ligne un padding
        for i in range(12):
            if i != 3:
                self.grid_rowconfigure(i, pad=20)
        self.grid_columnconfigure(0, weight=1, minsize=20) #weight 1 permet de creer column vide
        self.grid_columnconfigure(4, weight=1, minsize=20)
        self.grid_rowconfigure(8, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(3, pad=100)
        self.grid()

    def Openfile(self):
        '''Demande a l'utilisateur de choisir un fichier'''

        filename = tk.filedialog.askopenfilename()
        self.label_filename['text'] = filename
        self.filename = filename

    def check_fasta(self):
        '''Check si le fasta est valide en utilisant biopython'''
        try:
            with open(self.filename, "r") as f:
                fasta = Bio.SeqIO.parse(f, "fasta")
                return any(fasta)  # False when `fasta` is empty, i.e. wasn't a FASTA file
        except (FileNotFoundError,TypeError,UnicodeDecodeError):
            return False

    def check_input(self):
        '''Verifie que l'input est un fasta, que la cmd est selectionne
        et que la evalue est valable. Si les conditions sont rencontré,
        deuxieme_fenetrefunc() est execute avec la commande adequate
        '''
        try:
            evalue = float(self.evalue.get())
            domevalue = float(self.domevalue.get())
            evalue_ok = True
        except ValueError:
            evalue_ok = False
        try:
            with open('./librairie/Pfam-A.hmm','r') as f:
                pass
            with open('./librairie/nbr_profile_pfam','r') as f:
                Pfam_exist=True
        except FileNotFoundError:
            Pfam_exist = False
        if self.check_fasta() is False:
            tk.messagebox.showerror('Erreur', 'Merci de specifier un fichier au format fasta')
        elif Pfam_exist is False:
            tk.messagebox.showerror('Pas de librarie PFAM',"Merci d'éxécuter le makefile afin de télécharger la librairie Pfam")
            self.grid_forget()
            Accueil(self.master)

        elif self.choicecmd.get() == '':
            tk.messagebox.showerror('Erreur', 'Merci de specifier hmmsearch ou hmmscan')
        elif evalue_ok is False:
            tk.messagebox.showerror('Erreur', 'Merci de specifier une evalue valable')
        else:
            if self.choicecmd.get()=='hmmsearch':
                self.command = '{0} --domtblout tmp --noali -E {2} --domE {3} ./librairie/Pfam-A.hmm {1} '.format(self.choicecmd.get(),self.filename,self.evalue.get(),self.domevalue.get())
            elif self.choicecmd.get()=='hmmscan':
                self.command = '{0} --domtblout tmp --noali -E {2} --domE {3} ./librairie/Pfam-A.hmm {1} '.format(self.choicecmd.get(),self.filename,self.evalue.get(),self.domevalue.get())
            self.grid_forget()
            SearchInProgress(self.master,self.command,self.filename)

    def fenetre_accueil(self):
        self.grid_forget()
        Accueil(self.master)


class SearchInProgress(ttk.Frame):
    '''deuxieme_fenetre affichant les modeles en train d'etre query pour
    hmmsearch ou les sequences query pour hmmscan avec une barre de progres
    '''
    def __init__(self,master,cmd,filename):
        ttk.Frame.__init__(self,master)
        self.master = master
        self.cmd = cmd
        self.filename = filename
        #Affiche la commande execute
        self.label_cmd = ttk.Label(self, text='Commande execute :')
        self.label_cmd.grid(row=0,columnspan=2)
        self.cmd_label  =ttk.Label(self, text=self.cmd)
        self.start_time = time.time()
        #Selon hmmcmd determine le nombre d'etape total et stock dans maxval
        #hmmsearch ->nbre de profil hmmscan_>nombre de seq
        if self.cmd.startswith('hmmsearch'):
            with open('./librairie/nbr_profile_pfam','r') as f:
                self.maxval = int(f.readlines()[0])
        else:
            with open(self.filename, "r") as f:
                fasta = Bio.SeqIO.parse(f, "fasta")
                self.maxval = 0
                for i in fasta:
                    self.maxval += 1
        #output dynamique dans output_text et progressbar
        self.progress_bar = ttk.Progressbar(self, length=650,maximum=self.maxval)
        #Cadre text recevant l'output de la commande
        self.output_text = tk.Text(self, borderwidth=3, relief="sunken")
        self.output_text.grid(row=2,columnspan=2)

        #lance un thread separé pour popene afin de ne pas freeze le gui

        def popene(self):
            '''Execute la recherche hmmsearch ou scan (macmd), ecrit
            l'output dans output_text et augmente conjointement la barre de progres
            '''
            avancement = 0
            #ecris dans output_text l'output
            with subprocess.Popen("exec " + self.cmd, shell=True,
            stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
                self.cancel_button = ttk.Button(self,
                text='Retour', command=lambda:self.cancel_popen(p)).grid(row=4,
                column=0,sticky='w',pady=25,padx=25)
                for line in p.stdout:
                    if line.startswith('Query:'):
                        avancement += 1
                        self.output_text.insert(tk.END, line)
                        self.output_text.see(tk.END)
                        self.progress_bar['value'] = avancement

            #Si la commande rencontre un probleme affiche un message d'Erreur
            #sinon execute la troisieme fenetre en appuyant sur le bouton suivant
            if p.returncode !=0:
                tk.messagebox.showerror('Erreur',
                'Une erreur s\'est produite lors de l\'execution')
            else:
                #A partir d'ici le fichier reference a l'output afin de rejoindre
                #l'importation d'un fichier personnel
                self.result_file='tmp'
                tk.messagebox.showinfo('Succee',
                'processe termine en {} secondes'.format(int(time.time() - self.start_time)))
                suivant = ttk.Button(self,text='suivant',
                command=self.aller_troisieme_fenetre).grid(row=4,
                column=1,sticky='e',pady=25,padx=25)


        t1= threading.Thread(target=lambda:popene(self))
        t1.start()

        #configuration du deuxieme frame
        self.cmd_label.grid(row=1,columnspan=2,pady=20,padx=10)
        self.progress_bar.grid(row=3,columnspan=2)

        self.grid(row=0, column=1,sticky='news')
        self.grid_rowconfigure(0, pad=10)

    def aller_troisieme_fenetre(self):
        self.grid_forget()
        Results(self.master,self.result_file)


    def cancel_popen(self,p):
        '''tue le thread si bouton retour est appuye et retourne sur
        la fenetre de recherche'''
        p.kill()
        self.grid_forget()
        Recherche(self.master)


class Results(ttk.Frame):
    '''Fenetre affichant les resultats sous la forme d'un tableau '''
    def __init__(self,master,result_file):
        ttk.Frame.__init__(self,master)
        self.master = master
        self.result_file = result_file


        #stock dans matrice les resultats parsé (une ligne -> une liste)
        self.matrice = self.parsehmmer()
        self.labelresultat = ttk.Label(self,
        text='Résultats trouvés : {}'.format(len(self.matrice)-1))

        #Creer un tableau des resultats
        self.tree = ttkwidgets.CheckboxTreeview(self, height=20)
        self.tree['columns']=('target','tlen','query','qlen','evalue','score','#','of','c-evalue','hmm from','hmm to','ali from','ali to')
        #tailles colonnes
        self.tree.column("#0",width=50)
        self.tree.column("target",width=130,anchor=tk.CENTER)
        self.tree.column("tlen",width=50,anchor=tk.CENTER)
        self.tree.column("query",width=150,anchor=tk.CENTER)
        self.tree.column('qlen',width=50,anchor=tk.CENTER)
        self.tree.column('evalue',width=100,anchor=tk.CENTER)
        self.tree.column('score',width=100,anchor=tk.CENTER)
        self.tree.column('#',width=25,anchor=tk.CENTER)
        self.tree.column('of',width=25,anchor=tk.CENTER)
        self.tree.column('c-evalue',width=100,anchor=tk.CENTER)
        self.tree.column('hmm from',width=100,anchor=tk.CENTER)
        self.tree.column('hmm to',width=100,anchor=tk.CENTER)
        self.tree.column('ali from',width=100,anchor=tk.CENTER)
        self.tree.column('ali to',width=100,anchor=tk.CENTER)
        #nom colonnes
        for col in self.tree['columns']:
            self.tree.heading(col,text=col,command=lambda _col=col:self.tree_sort_column(_col,False))

        j=0
        #dictionnaire pour associer les elements de la matrice avec les checkbox
        self.index_indices = {}
        #Insere toutes les lignes du domtblout
        for i in self.matrice[1:]:
            if j%2 ==0:
                indice = self.tree.insert('',j,text='',
                values=(i[0],int(i[2]),i[3],int(i[5]),float(i[6]),float(i[7]),int(i[9]),int(i[10]),float(i[11]),int(i[15]),int(i[16]),int(i[17]),int(i[18])),tags = ('pair',))
                self.index_indices[indice] = (i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],i[11],i[15],i[16],i[17],i[18])
            else:
                indice = self.tree.insert('',j,text='',
                values=(i[0],int(i[2]),i[3],int(i[5]),float(i[6]),float(i[7]),int(i[9]),int(i[10]),float(i[11]),int(i[15]),int(i[16]),int(i[17]),int(i[18])),tags = ('impair',))
                self.index_indices[indice] = (i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],i[11],i[15],i[16],i[17],i[18])
            j+=1
        self.tree.tag_configure('pair', background='#E8E8E8')
        self.tree.tag_configure('impair', background='#DFDFDF')
        self.tree.grid(row=2,columnspan=4)
        self.filtre_label = ttk.Label(self,text='').grid(row=3)
        #Choix evalue
        self.filtre_evalue_label = ttk.Label(self,
        text='e-value inférieur à :').grid(row=4,column=0)
        self.filtre_evalue = tk.StringVar()
        self.filtre_evalue_entry = ttk.Entry(self,
        textvariable=self.filtre_evalue,width=10, justify='center')
        self.filtre_evalue_entry.insert(0,'10')
        self.filtre_evalue_entry.grid(row=5,column=0)
        #Choix recouvrement
        self.filtre_recouvrement_label = ttk.Label(self,
        text='% recouvrement min :').grid(row=4,column=1)
        self.recouvrement = ttkwidgets.TickScale(self,
        from_=0,to=100,orient='horizontal',resolution=1,length=200)
        #Choix redondance
        self.redondance_label = ttk.Label(self,
        text='Supprimer redondance :').grid(row=4,column=2)
        self.redondance = tk.IntVar()
        self.redondance_box = ttk.Checkbutton(self,onvalue=1,offvalue=0, variable = self.redondance)
        #bouton de mise a jour
        self.majbutton = ttk.Button(self,
        text='Mettre à jour',
        command=self.update_tree).grid(row=5,column=3)

        #Bouton d'ajout a la DB
        self.send_check = ttk.Button(self,
        text='Ajouter a la base de donnee',
        command=self.add_to_DB)
        #Bouton retour recherche
        self.NouvelleRecherche = ttk.Button(self,
        text='Nouvelle recherche',
        command=self.fenetre_recherche)
        #bouton retour accueil
        self.Accueil = ttk.Button(self,
        text='Retour accueil',
        command=self.fenetre_accueil)
        #Configuration du layout
        self.labelresultat.grid(row=1,columnspan=4,pady=20)
        self.recouvrement.grid(row=5,column=1)
        self.redondance_box.grid(row=5,column=2)
        self.send_check.grid(row=6,column=1,columnspan=2)
        self.NouvelleRecherche.grid(row=6,column=3)
        self.Accueil.grid(row=6,column=0)
        self.grid(row=0, column=1,sticky='news')
        self.grid_rowconfigure(0, pad=50)
        self.grid_rowconfigure(6, pad=50)
        self.grid()


    def parsehmmer(self):
        '''Creer une matrice contenant le domtblout parsé,
        verifie les dimensions de la matrice afin de s'assurer que le
        fichier fournis est un domtblout sinon envoie un message d'erreur,
        finalement retourne la matrice si les conditions sont rencontré
        Chaque ligne de la matrice correspond a une ligne du domtblout
        le programme (scan ou search) est enregistre dans matrice[0]
        '''
        self.matrice = []
        try:
            with open(self.result_file,'r') as f:
                ff =f.readlines()
                program = ff[-9] #hmmer indique le programme utilise ici
                if 'hmmsearch' in program:
                    self.matrice.append('hmmsearch')
                elif 'hmmscan' in program:
                    self.matrice.append('hmmscan')
                else:
                    tk.messagebox.showerror('fichier non conforme',
                    'Merci de fournir un fichier au format domtblout')
                    self.fenetre_accueil
                for line in ff[3:-10]:
                    fin = re.split(r"\s+",line)
                    self.matrice.append(fin)
            return self.matrice
        except IndexError:
            tk.messagebox.showerror('fichier non conforme',
            'Merci de fournir un fichier au format domtblout')
            self.fenetre_accueil


    def tree_sort_column(self,col,reverse):
        '''Sort columns upon clicking on heading'''
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)

        except ValueError:
            l.sort(key=lambda v: v[0].upper(),reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        # reverse sort next time
        self.tree.heading(col, command=lambda:self.tree_sort_column(col,not reverse))

    def update_tree(self):
        '''Efface l'ancien tableau et le reconstruit en appliquant
        les conditions : evalue max et recouvrement mini'''
        #verifie que la evalue est sous le bon format sinon retourne un message d'erreur
        try:
            evalue = float(self.filtre_evalue.get())
        except ValueError:
            tk.messagebox.showerror(title='Erreur',
            message='La evalue doit etre un reel \nEcriture scientifique accepté sous la forme 1e-N')
            return False
        recouvrement = int(self.recouvrement.get())

        #Oublie l'ancien tableau et recreer le avec les conditions
        self.tree.grid_forget()
        self.tree = ttkwidgets.CheckboxTreeview(self, height=20)
        self.tree['columns']=('target','tlen','query','qlen','evalue','score','#','of','c-evalue','hmm from','hmm to','ali from','ali to')
        #tailles colonnes
        self.tree.column("#0",width=50)
        self.tree.column("target",width=130,anchor=tk.CENTER)
        self.tree.column("tlen",width=50,anchor=tk.CENTER)
        self.tree.column("query",width=150,anchor=tk.CENTER)
        self.tree.column('qlen',width=50,anchor=tk.CENTER)
        self.tree.column('evalue',width=100,anchor=tk.CENTER)
        self.tree.column('score',width=100,anchor=tk.CENTER)
        self.tree.column('#',width=25,anchor=tk.CENTER)
        self.tree.column('of',width=25,anchor=tk.CENTER)
        self.tree.column('c-evalue',width=100,anchor=tk.CENTER)
        self.tree.column('hmm from',width=100,anchor=tk.CENTER)
        self.tree.column('hmm to',width=100,anchor=tk.CENTER)
        self.tree.column('ali from',width=100,anchor=tk.CENTER)
        self.tree.column('ali to',width=100,anchor=tk.CENTER)
        #nom colonnes
        for col in self.tree['columns']:
            self.tree.heading(col,text=col,command=lambda _col=col:self.tree_sort_column(_col,False))

        #Pour chaque ligne du domtblout, les inseres si elles respectent les
        #conditions donnees
        j=0
        passe_selection =0
        self.index_indices = {}
        if self.redondance.get() == 1:
            sorted_matrice = self.adjust_matrix()
        else:
            sorted_matrice = self.matrice
        if self.matrice[0] == 'hmmsearch':
            for i in sorted_matrice[1:]:
                j+=1
                if float(i[6])<=evalue:
                    if int(recouvrement) <= (int(i[16])-int(i[15])+1)/int(i[5])*100:
                        passe_selection += 1
                        if passe_selection%2==0:
                            indice = self.tree.insert('',j,text='',
                            values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18]),tags = ('pair',))
                            self.index_indices[indice] = (i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18])
                        else :
                            indice = self.tree.insert('',j,text='',
                            values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18]),tags = ('impair',))
                            self.index_indices[indice] = (i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18])
        else:
            for i in sorted_matrice[1:]:
                j+=1
                if float(i[6])<=evalue:
                    if int(recouvrement) <= (int(i[16])-int(i[15])+1)/int(i[2])*100:
                        passe_selection += 1
                        if passe_selection%2==0:
                            indice = self.tree.insert('',j,text='',
                            values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18]),tags = ('pair',))
                            self.index_indices[indice] = (i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18])
                        else:
                            indice = self.tree.insert('',j,text='',
                            values=(i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18]),tags = ('impair',))
                            self.index_indices[indice] = (i[0],i[2],i[3],i[5],i[6],i[7],i[9],i[10],
                            i[11],i[15],i[16],i[17],i[18])

        self.tree.tag_configure('pair', background='#E8E8E8')
        self.tree.tag_configure('impair', background='#DFDFDF')
        #Met a jour le label indiquant le nombre de resultat
        self.labelresultat.grid_forget()
        self.labelresultat = ttk.Label(self,
        text='Résultats trouvés : {0}, après filtrage : {1}'.format(len(self.matrice)-1,passe_selection))
        self.labelresultat.grid(row=1,columnspan=4,pady=20)
        #Bouton d'ajout a la DB
        self.send_check = ttk.Button(self,
        text='Ajouter a la base de donnee',
        command=self.add_to_DB)
        self.send_check.grid(row=6,column=1,columnspan=2)
        self.tree.grid(row=2,columnspan=4)

    def adjust_matrix(self):
        """Si l'option supprimer la redondance est cochée, supprime les hits
        qui se recouvre en gardant celui avec la meilleur evalue et place ceux-ci
        dans une nouvelle matrice -> adjusted_matrix """
        j=0
        if self.matrice[0] == 'hmmscan':
            adjusted_matrix=[self.matrice[1]]
            for result in self.matrice[2:]: #pour chaque resultat
            #pars du principe que le resultat et non redondant
                ok = True
                for adjust in adjusted_matrix: #pour chaque resultqt non redondant
                    if result[3]==adjust[3] :
                        if int(adjust[17])<=int(result[17]) <=int(adjust[18]) or int(adjust[17])<=int(result[18]) <=int(adjust[18]):
                            ok=False
                if ok is True:
                    adjusted_matrix.append(result)
        elif self.matrice[0] == 'hmmsearch':
            adjusted_matrix=[self.matrice[1]]
            for result in self.matrice[2:]: #pour chaque resultat
            #pars du principe que le resultat et non redondant
                ok = True
                for adjust in adjusted_matrix: #pour chaque resultat non redondant
                    if result[0]==adjust[0] : #Si le resultat correspond a une sequence deja ajuste
                        #Considere comme redondant si les coordonnes du nouveaux domaines chevauche un domaine ajuste
                        if int(adjust[17])<=int(result[17]) <=int(adjust[18]) or int(adjust[17])<=int(result[18]) <=int(adjust[18]):
                            ok=False
                if ok is True:
                    adjusted_matrix.append(result)
        return adjusted_matrix




    def add_to_DB(self):
        '''Ajouter les lignes selectionne a la database mysql,
        si aucune DB configure demande les renseignements'''
        self.grab = []
        self.grab.append(self.matrice[0])
        for i in self.tree.get_checked():
            self.grab.append(self.index_indices[i])
        try:
            with open('config.txt','r') as f :
                list_info = f.read().split()
                host = list_info[0]
                db = list_info[1]
                user = list_info[2]
                passwd = list_info[3]
                add_to_database(self.grab,host,db,user,passwd)
        except (FileNotFoundError,IndexError):
            PromptDB(self,'Connection Base de donnee')



    def fenetre_recherche(self):
        '''Permet d'aller a la fenetre de recherche'''
        self.save_file()
        self.grid_forget()
        Recherche(self.master)

    def fenetre_accueil(self):
        self.save_file()
        self.grid_forget()
        Accueil(self.master)

    def save_file(self):
        ''' Save the domtblout file if user want to '''
        if tk.messagebox.askyesno('Enregistrement','Voulez-vous sauvegarger vos résultats avant de quitter ?') :
            f = tk.filedialog.asksaveasfile(mode='w', defaultextension=".txt")
            if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
                return
            with open('tmp','r') as t:
                text2save = t.read()
            f.write(text2save)
            f.close()

class PromptDB(tk.simpledialog.Dialog):
    '''Prompt for database information'''
    def body(self, master):

        ttk.Label(master, text="Host:").grid(row=0)
        ttk.Label(master, text="Database:").grid(row=1)
        ttk.Label(master, text="User:").grid(row=2)
        ttk.Label(master, text="Password:").grid(row=3)

        self.e1 = ttk.Entry(master)
        self.e2 = ttk.Entry(master)
        self.e3 = ttk.Entry(master)
        self.e4 = ttk.Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        self.e4.grid(row=3, column=1)
        return self.e1 # initial focus

    def apply(self):
        host = self.e1.get()
        database = self.e2.get()
        user = self.e3.get()
        passwd = self.e4.get()
        add_to_database(self.master.grab,host,database,user,passwd)



wBestHMM=ttkthemes.themed_tk.ThemedTk(theme='ubuntu')

wBestHMM.title("BestHMM")
wBestHMM.resizable(False,False)
# wBestHMM.geometry("1000x820")
# wBestHMM.minsize(480,360)
# wBestHMM.config(background="#ffcc99")

Accueil(wBestHMM)
wBestHMM.mainloop()
