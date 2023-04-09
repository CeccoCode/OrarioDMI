# TELEBOT IMPORT
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

# REQUESTS IMPORT
import requests
from bs4 import BeautifulSoup

# OTHER IMPORT
import re
from tabulate import tabulate
# import exceptiongroup
import datetime

API_TOKEN = '5759910468:AAHLWKimYR6w0wwiPerb-mXh4v2tpI-U1aA'
bot = telebot.TeleBot(API_TOKEN)
chat_id = 0
date = ""

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global chat_id
    chat_id = message.chat.id
    bot.send_message(chat_id, "Benvenuto! questo è il bot che ti permette di consulatare l'orario delle lezioni del dipartimento di Matematica e Informatica di Perugia. ", reply_markup=markup_inline())

@bot.message_handler(content_types = ["text"])
def message_listener(message):
    match message.text:
        case "/A0":
            stampa_orario_odierno_aula(0, message)
        case "/A2":
            stampa_orario_odierno_aula(1, message)
        case "/A3":
            stampa_orario_odierno_aula(2, message)
        case "/B1":
            stampa_orario_odierno_aula(3, message)
        case "/B3":
            stampa_orario_odierno_aula(4, message)
        case "/C2":
            stampa_orario_odierno_aula(5, message)
        case "/I1":
            stampa_orario_odierno_aula(6, message)
        case "/I2":
            stampa_orario_odierno_aula(7, message)
        case "/Sala_Riunioni":
            stampa_orario_odierno_aula(8, message)
        case "/Aula_C3":
            stampa_orario_odierno_aula(9, message)
        case "/Aula_Gialla":
            stampa_orario_odierno_aula(10, message)
        case "/Aula_Verde":
            stampa_orario_odierno_aula(11, message)
        case "/NB19":
            stampa_orario_odierno_aula(12, message)
        case "/NB20":
            stampa_orario_odierno_aula(13, message)
        case "/Portatile_4":
            stampa_orario_odierno_aula(14, message)
        case "/Portatile_5":
            stampa_orario_odierno_aula(15, message)
        case "/Proiettore_4":
            stampa_orario_odierno_aula(16, message)
        case "/Tutte_le_aule":
            stampa_orario_odierno_aula(25, message)
        case "/Nuova_data":
            bot.send_message(message.chat.id,
                             "Inserisci una nuova data nel formato gg/mm/aaaa")
            bot.register_next_step_handler(message, responce_handler_dp)
        case "/Indietro":
            bot.send_message(message.chat.id, "Seleziona un comando: ", reply_markup=markup_inline())

def scelta_aula(message, data_type):
    str = '''Scegli l'aula di cui vuoi vedere l'orario: \n
    /A0
    /A2
    /A3
    /B1
    /B3
    /C2      
    /I1
    /I2
    /Sala_Riunioni
    /Aula_C3
    /Aula_Gialla
    /Aula_Verde
    /NB19
    /NB20
    /Portatile_4
    /Portatile_5
    /Proiettore_4
    
    /Tutte_le_aule'''
    if data_type == 0:
        str += '''
    
    /Indietro
        '''
    else:
        str += '''
        
    /Nuova_data             /Indietro
        '''

    bot.send_message(message.chat.id, str)

def stampa_orario_odierno_aula(aula, message):
    global date

    if date == "": # caso data giornaliera
        url = "https://servizi.dmi.unipg.it/mrbs/day.php"
    else: #caso data personalizzata
        ds = date.split("/", 2)
        url = "https://servizi.dmi.unipg.it/mrbs/day.php?day=" + ds[0] + "&month=" + ds[1] + "&year=" + ds[2]

    dip_chiuso = False # memorizza lo stato del dipartimento: True = dip chiuso, False = dip aperto
    try:
        response = requests.post(url)
        if response.status_code == 200:
            # Parse the HTML source code using Beautiful Soup
            soup = BeautifulSoup(response.content, "html.parser")

            giorno = soup.find('div', {'id': 'dwm'})
            bot.send_message(message.chat.id, giorno.text)

            table = soup.find('table', {'class': 'dwm_main'})
            if aula!=25:
                rows = table.find_all('tr')[1:]
                cells = rows[aula].find_all('td')
                dip_chiuso = retrieve_Data_from_table(cells, message)
            else:
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cells = row.find_all('td')
                    if retrieve_Data_from_table(cells, message) == True:
                        dip_chiuso = True
                        break
    finally:
        if dip_chiuso == False: # se il dipartimento è aperto visualizza tutte le aule, altrimenti visualizza solo il pulsante indietro
            if date == "":
                scelta_aula(message, 0)
            else:
                scelta_aula(message, 1)
        else:
            bot.send_message(message.chat.id, "/Indietro")

def retrieve_Data_from_table(cells, message):

    # TODO: togliere aule inutili

    dip_chiuso = False
    flag_aula = True
    str = ""
    for cell in cells:
        if cell.has_attr('class') and 'row_labels' in cell.get('class'):
            aula = cell.text.strip()
            str += "---------- " + aula + " ----------" + "\n"
        elif cell.has_attr('class') and ( ('I' in cell.get('class')) or ('E' in cell.get('class')) ):

            flag_aula = True

            attiv = cell.text.strip()
            if re.search(r'^Chiusura.*', attiv):
                str = attiv
                dip_chiuso = True
                break

            str += "\n"
            lezione = cell.find('div', {'data-id': True})
            data_id = lezione['data-id']
            url = "https://servizi.dmi.unipg.it/mrbs/view_entry.php?id=" + data_id
            response = requests.post(url)
            # TODO: controllo dell'errore se pagina non trovata
            soup = BeautifulSoup(response.content, "html.parser")

            table_title = soup.find_all('div', {'id': 'contents'})
            for title in table_title:
                h3 = title.find_all('h3')
                for hh3 in h3:
                    str += hh3.text.strip() + " | "

            table = soup.find_all('table', {'id': 'entry'})
            flag_skip = False
            flag_ora_in = False
            flag_ora_end = False
            for tr in table:
                ttr = tr.find_all('td')
                for td in ttr:
                    ttd = td.text

                    doc = ttd.startswith("Docente:")
                    ora_in = ttd.startswith("Ora Inizio:")
                    ora_fine = ttd.startswith("Ora Fine:")

                    # nel sistema mrbs la formattazione dei dati è del tipo: Docente: nome_doc, Ora Inizio: ora
                    # questa prima condizione permette di scrivere solo il contenuto (nome_doc, ora) e non il nome dell'attributo (Docente, Ora Inizio)
                    if flag_skip == True or doc or ora_in or ora_fine:
                        if doc == False and ora_in == False and ora_fine == False:
                            if flag_ora_in == True:
                                cut_day = ttd.strip()[0:5]
                                str += "Inizio: " + cut_day + " | "
                                flag_ora_in = False
                            elif flag_ora_end == True:
                                cut_day = ttd.strip()[0:5]
                                str += "Fine: " + cut_day + " | "
                                flag_ora_end = False
                            else:
                                str += ttd.strip()

                    if doc or ora_in or ora_fine:
                        if ora_in:
                            flag_ora_in = True
                        elif ora_fine:
                            flag_ora_end = True
                        flag_skip = True
                    else:
                        flag_skip = False
            str += "\n"
        else:
            if flag_aula == True:
                str += "\n Aula Libera\n"
                flag_aula = False
    bot.send_message(message.chat.id, str)
    return dip_chiuso

def markup_inline():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("HELP", callback_data="help")
    )
    markup.add(
        InlineKeyboardButton("DATA ODIERNA", callback_data="data_odierna"),
        InlineKeyboardButton("DATA PERSONALIZZATA", callback_data="data_personalizzata")
    )
    markup.add(
        InlineKeyboardButton("PAROLE CHIAVE", callback_data="parole_chiave")
    )
    return markup

@bot.callback_query_handler(func=lambda query: query.data == "help")
def help_btn(call):
    # TODO: inserire informazioni utili per l'help. Funzionamento bei bottoni principali
    bot.send_message(call.message.chat.id,
                """Ciao, sono il bot che ti aiuta a consultare l'orario del dipartimento di matematica e informatica di Perugia.
                 """)
    bot.send_message(call.message.chat.id, "Seleziona un comando: ", reply_markup=markup_inline())

@bot.callback_query_handler(func=lambda query: query.data == "data_odierna")
def data_odierna_btn(call):
    scelta_aula(call.message, 0)

@bot.callback_query_handler(func=lambda query: query.data == "data_personalizzata")
def data_personalizzata_btn(call):
    bot.send_message(call.message.chat.id,
                     "Inserisci una data nel formato gg/mm/aaaa. L'anno deve essere di una unità più piccola o uguale all'anno corrente. Non sono ammessi altri valori")
    bot.register_next_step_handler(call.message, responce_handler_dp)

def responce_handler_dp(message):

    global date
    date = message.text
    date_split = date.split("/", 2)
    for i in [0,1,2]:
        date_split[i] = int(date_split[i])

    today = datetime.date.today() # per controllo sull'anno corretto
    try:
        datetime.datetime.strptime(date, "%d/%m/%Y").date()
        cond2 = ( date_split[2] - today.year < -1 ) or ( date_split[2] - today.year > 1 )
        if cond2 == False:
            scelta_aula(message, 1)
        elif cond2:
            bot.send_message(message.chat.id,
                             "La data inserita non è nel formato corretto: L'anno deve essere di una unità più piccola o uguale all'anno corrente. Non sono ammessi altri valori")
            bot.register_next_step_handler(message, responce_handler_dp)
    except ValueError:
        # La stringa inserita dall'utente non è una data valida
        bot.send_message(message.chat.id, "La data inserita non rispetta il formato. Inserire una data nel formato: gg/mm/aaaa")
        bot.register_next_step_handler(message, responce_handler_dp)

@bot.callback_query_handler(func=lambda query: query.data == "parole_chiave")
def parole_chiave_btn(call):
    bot.send_message(call.message.chat.id,
                     "La parola chiave può essere un docente o il nome di un corso. Inserici una parola chiave:")
    bot.register_next_step_handler(call.message, responce_handler_pc)

def responce_handler_pc(message):
    data = message.text
    url = "https://servizi.dmi.unipg.it/mrbs/search.php?year=2023&month=03&day=06&area=1&room=3&search_str=" + data
    # response = requests.post(url, data=data)
    response = requests.post(url)
    if response.status_code == 200:
        # Parse the HTML source code using Beautiful Soup
        soup = BeautifulSoup(response.content, "html.parser")
        # Print the parsed HTML source code
        print(soup.prettify())
    else:
        print("Error submitting data. Status code:", response.status_code)
    bot.send_message(message.chat.id, "Seleziona un comando: ", reply_markup=markup_inline())

bot.polling()


