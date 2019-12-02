import mysql.connector
from mysql.connector import Error,errorcode
import tkinter.messagebox

def connection(host,DB_NAME,user,passwd):
    '''Connection a la DB, retourne l'object connection'''
    try:
        connection = mysql.connector.connect(host=host,
                                             database=DB_NAME,
                                             user=user,
                                             password=passwd)

        if connection.is_connected():
            return connection
    except Error as e:
        tkinter.messagebox.showerror("Error","Error while connecting to MySQL"+ str(e))
        return False


def use_db(cursor,DB_NAME):
    '''use database or create it if not exist'''
    try:
        cursor.execute("USE {}".format(DB_NAME))

    except mysql.connector.Error as err:
        print(err)
        exit(1)

def create_table(cursor,TABLE):
    try:
        cursor.execute(TABLE)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            pass
        else:
            tk.messagebox.showerror(str(err.msg))

def insert_into_DB(cursor,matrice):
    ajout = 0
    duplicate=0
    if matrice[0] == 'hmmsearch':
        for result in matrice[1:]:
            add_result = ("INSERT INTO sequences "
                       "(seq_name, seq_len, domain_name, domain_len,ali_from,ali_to) "
                       "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')".format(result[0],result[1],result[2],result[3],result[11],result[12]))
            try:
                cursor.execute(add_result)
                ajout +=1
                print(add_result)
            except mysql.connector.errors.IntegrityError:
                duplicate +=1
    elif matrice[0] == 'hmmscan':
        for result in matrice[1:]:
            add_result = ("INSERT INTO sequences "
                       "(seq_name, seq_len, domain_name, domain_len,ali_from,ali_to) "
                       "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')".format(result[2],result[3],result[0],result[1],result[11],result[12]))
            print(add_result)
            try:
                cursor.execute(add_result)
                ajout +=1
            except mysql.connector.errors.IntegrityError:
                duplicate +=1
    tkinter.messagebox.showinfo('Ajout ','Ajout : {0}\n Duplicat : {1}'.format(ajout,duplicate))


def remember_DB(host,db,user,passwd):
    with open('config.txt','w') as f :
        f.write(host+' '+db+' '+user+' '+passwd)

def add_to_database(matrice,host,DB_NAME,user,passwd):
    TABLE = (
    "CREATE TABLE `sequences` ("
    "  `seq_name` varchar(16) NOT NULL,"
    "  `seq_len` int(10) NOT NULL,"
    "  `domain_name` varchar(20) NOT NULL,"
    "  `domain_len` int(10) NOT NULL,"
    "  `ali_from` int(10) NOT NULL,"
    "  `ali_to` int(10) NOT NULL,"
    " `date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`seq_name`,`seq_len`,`domain_name`,`domain_len`,`ali_from`,`ali_to`)"
    ") ENGINE=InnoDB"
    )
    connect = connection(host,DB_NAME,user,passwd)
    if connect is not False:
        remember_DB(host,DB_NAME,user,passwd)
        cursor = connect.cursor()
        use_db(cursor,DB_NAME)
        create_table(cursor,TABLE)
        insert_into_DB(cursor,matrice)

        connect.commit()
        cursor.close()
        connect.close()
