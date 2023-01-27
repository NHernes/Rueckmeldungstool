import eel
import datetime
import json,requests
import re
from icalevents.icalevents import events
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, ssl
import tkinter as tk
from bs4 import BeautifulSoup
import base64
from tkinter import simpledialog
import pytz

####Notizen####
#Ggf. zum Crawlen der Wiki-Seiten Threads benutzen wenn es zu lange dauert.


kalenderstatus=["05. Warten auf Rückmeldung","05.Warten auf Rückmeldung"]

application_window = tk.Tk()
application_window.withdraw()

def credentials():
    global access_token
    
    try:
        with open("token.txt","r") as f:
            access_token=f.read()

    except:
        access_token=""
        while access_token=="":
            access_token = simpledialog.askstring("Input", "Gib deinen Wiki Personal Token ein:",
                                                parent=application_window)
            
            with open("token.txt","w+") as f:
                f.write(access_token)
    finally:
        if access_token=="":
            while access_token=="":
                access_token = simpledialog.askstring("Input", "Gib deinen Wiki Personal Token ein:",
                                                    parent=application_window)
                
                with open("token.txt","w+") as f:
                    f.write(access_token)
        else:
            pass


def wiki_url_shortener(wiki_url):
    if "/x/" in wiki_url:
        wiki_url=wiki_url.removeprefix("https://wikis.fu-berlin.de/x/")
        wiki_url_short=int.from_bytes(base64.b64decode(wiki_url.ljust(8,'A').replace('_','+').replace('-','/').encode()),byteorder='little')
    
    if "pageId" in wiki_url:
        wiki_url_short=wiki_url.removeprefix("https://wikis.fu-berlin.de/pages/viewpage.action?pageId=")
    
    if "pageId" not in wiki_url and "/x/" not in wiki_url and "wikis" in wiki_url:
        wiki_url_short=wiki_url.removeprefix("https://wikis.fu-berlin.de/display/eexam/")
    
    if "viewinfo" in wiki_url:
        wiki_url_short=wiki_url.removeprefix("https://wikis.fu-berlin.de/pages/viewinfo.action?pageId=")

    if wiki_url=="":
        wiki_url_short=wiki_url
    return wiki_url_short


credentials()

eel.init("web")

def wiki_inhalt_abrufen(wiki_url_short):
    
    url = f'https://wikis.fu-berlin.de/rest/api/content/{wiki_url_short}?expand=body.storage'
    headers = {
    "Accept": "application/json;charset=UTF-8",
    "Content-Type": "application/json;charset=UTF-8",
    "Authorization": f"Bearer {access_token}"
    }

    r = requests.get(url=url, headers=headers)

    ###Oberer Inhalt
    inhalt=json.loads(r.text)
    inhalt=inhalt["body"]["storage"]["value"]

    url = f'https://wikis.fu-berlin.de/rest/api/content/{wiki_url_short}?expand=body.view'
    headers = {
    "Accept": "application/json;charset=UTF-8",
    "Content-Type": "application/json;charset=UTF-8",
    "Authorization": f"Bearer {access_token}"
    }

    r = requests.get(url=url, headers=headers)

    ###Oberer Inhalt
    inhalt_html=json.loads(r.text)
    inhalt_html=inhalt_html["body"]["view"]["value"]
    
    return inhalt,inhalt_html

def wiki_inhalt_manipulieren(inhalt,wiki_url_short):
    #Daten für das Seiten-Update ziehen
    url = f'https://wikis.fu-berlin.de/rest/api/content/{wiki_url_short}?expand=version'

    headers = {

    'Content-Type': 'application/json;charset=iso-8859-1',
    "Authorization": f"Bearer {access_token}"
    }

    r = requests.get(url=url, headers=headers)
    seitenversion=r.json()["version"]

    seitenversion=seitenversion["_links"]
    seitenversion=seitenversion["self"]
    while "/" in seitenversion:
        seitenversion=seitenversion[1:]

    
    seitentitel=r.json()["title"]

    url = f"https://wikis.fu-berlin.de/rest/api/content/{wiki_url_short}"

    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
    }

    payload = json.dumps( {
    "version": {
        "number":int(seitenversion)+1
    },
    "title": seitentitel,
    "type": "page",
    "status": "current",
    "ancestors": [],
    "body": {
        "storage": {
        "value": inhalt,
        "representation": "storage"
        }}
    } )

    response = requests.request(
    "PUT",
    url,
    data=payload,
    headers=headers
    )

    if response.status_code==200:
        print("Wiki-Seite erfolgreich aktualisiert")
    
    return response.status_code

def wiki_kommentar(wiki_url_short):
    #Bisherige Kommentare auslesen
    url = f'https://wikis.fu-berlin.de/rest/api/content/{wiki_url_short}/child/comment?expand=body.view&depth=all'
        
    headers = {
    'Content-Type': 'application/json;charset=iso-8859-1',
    "Authorization": f"Bearer {access_token}"
    }
    r = requests.get(url=url, headers=headers)
    #print(r.text)
    ergebnisse=r.json()["results"]
    zähler_rm=0
    for i in ergebnisse:
        kommentar=i["body"]["view"]["value"]
        if "Rückmeldungstool: Erinnerung versendet" in kommentar:
            zähler_rm+=1
    zähler_rm+=1 #Die aktuelle RM-Iteration wird auf Basis der vorherigen Kommentare hochgezählt
    heutiges_datum=datetime.datetime.now().date().strftime("%d.%m.%Y")
    neues_kommentar=f"<h3>Rückmeldungstool: Erinnerung versendet (Datum: {heutiges_datum}, Nummer: {zähler_rm})</h3>"

    #Kommentar abfeuern
    url = f'https://wikis.fu-berlin.de/rest/api/content/{wiki_url_short}?expand=version'

    headers = {
        'Content-Type': 'application/json;charset=iso-8859-1',
        "Authorization": f"Bearer {access_token}"
        }

    r = requests.get(url=url, headers=headers)
    seitentitel=r.json()["title"]

    url = f'https://wikis.fu-berlin.de/rest/api/content/'
    headers = {
        "Accept": "application/json;charset=UTF-8",
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {access_token}"
        }

    payload=json.dumps({
        "type": "comment",
        "space": {
            "key": "eexam"
        },
        "body": {
            "storage": {
            "representation": "storage",
            "value": neues_kommentar
            }
        },
        "title": seitentitel,
        "container": {
                "id": wiki_url_short,
                "type" : "global"
        }
        })

    r = requests.post(url=url, headers=headers,data=payload)


def rm_mail_senden(mail,name_prüfung,datum_rm_neu,benutzername,passwort):
    global server

    print(mail)
    if mail[0]!="":
        
            #prüfungstermin_string=datum_rm.strftime("%d.%m.%Y")
            subject = f"Reminder: Rückmeldung zu Ihrer erstellten Prüfung: {name_prüfung}"
            
            body = f"""\
            <html>
            Liebe Lehrende,
            <br>
            <br>
            Sie haben uns noch keine Rückmeldung zu den letzten Änderungen an Ihrer digitalen Prüfung übermittelt: 
            <br>
            <br>
            <b> {name_prüfung} </b>
            <br>
            <br>
            Bitte senden Sie uns Ihr Feedback spätestens bis zum {datum_rm_neu} zu.
            <br>
            <br>
            Vielen Dank.
            <br>
            <br>
            <b> Sollten Sie uns bereits Feedback zur letzten Iteration zugesendet haben, erachten Sie diese Mail als gegenstandslos. </b>
            <br>
            <br>
            Mit besten Grüßen
            <br>
            Ihr E-Examinations Team
            <br>
            _________________________________________________
            <br>
            Dies ist eine automatisiert versendete E-Mail
            </html>
            """
            mail.append("e-examinations@cedis.fu-berlin.de")
            print(mail)
            sender_email = "e-examinations@cedis.fu-berlin.de"

            receiver_email = ",".join(mail)
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"]  = subject
            message["Cc"] = sender_email

            message.attach(MIMEText(body, "html"))

            text = message.as_string()
            #li = list(receiver_email.split(","))
            #li.append("e-examinations@cedis.fu-berlin.de")
            #context = ssl.create_default_context()
            # Log in to server using secure context and send email

            """
            ctx = ssl.create_default_context()
            ctx.set_ciphers('DEFAULT')
            
            mailadresse=""
            port=""
            imapSrc = imaplib.IMAP4_SSL(mailadresse, ssl_context = ctx)
            with smtplib.SMTP_SSL(mailadresse, port, context=ctx) as server:
                server.login(benutzername, passwort)

                server.sendmail(sender_email, mail, text)

            """
            server.sendmail(sender_email, mail, text)
            return "Erfolgreich"
    else:
        return "Fehlgeschlagen"

@eel.expose
def wiki_seiten_abrufen(datum):
    utc=pytz.UTC
    berlin = pytz.timezone('Europe/Berlin')
    start = datetime.datetime(2022,10,1, 1, 0, 0).astimezone(berlin)
    end = datetime.datetime(2023,6,1, 23, 59, 59).astimezone(berlin)

    ical_id_1=""
    ical_id_2=""
    übergang=events(ical_id_1,start=start,end=end)
    abschließender_kalender=events(ical_id_2, start=start,end=end)
    
    übergang
    
    zähler=0
    kalender_daten=[]
    """
    if  isinstance(übergang, list):
        for i in übergang:
            if i.categories[0] in kalenderstatus: #Hier wird geprüft, ob das Kalender-Event einen Prüfungsstatus hat, damit Events wie LPLUS Updates gefiltert werden
                prüfungsname=i.summary
                beschreibung=i.description
                prüfungsname=prüfungsname.replace(f": {beschreibung}","")

                status_event=i.categories
                status_event=status_event[0]
                datum_kalender=i.start
                datum_kalender=datum_kalender.strftime("%d.%m.%Y")
                url=i.url
                mail=i.location
                

                if ("nobot" not in i.description) and url!=None: #Hier prüft das Script, ob Boty für den Termin ausgeschaltet wurde
                    wiki_url_short=wiki_url_shortener(url)
                    kalender_daten=kalender_daten+[[wiki_url_short,prüfungsname,datum_kalender,status_event,mail]]
                    zähler+=1
    """
    if  isinstance(abschließender_kalender, list):
        for i in abschließender_kalender:
            if i.categories[0] in kalenderstatus and "Durchgang 2" not in i.summary and "Durchgang 3" not in i.summary and "Durchgang 4" not in i.summary: #Hier wird geprüft, ob das Kalender-Event einen Prüfungsstatus hat, damit Events wie LPLUS Updates gefiltert werden
                url=i.url
                beschreibung=i.description
                
                if url!=None and "nobot" not in beschreibung:
                    prüfungsname=i.summary
                    prüfungsname=prüfungsname.replace(f": {beschreibung}","")
                    prüfungsname=prüfungsname.replace("(EEC1)","")
                    prüfungsname=prüfungsname.replace("(EEC2)","")
                    prüfungsname=prüfungsname.replace("(Home)","")
                    prüfungsname=prüfungsname.replace("(A-Pool)","")

                    status_event=i.categories
                    status_event=status_event[0]
                    datum_kalender=i.start
                    datum_kalender=datum_kalender.strftime("%d.%m.%Y")
                    
                    mail=i.location

                    [(support:="ja" if "[S]" in prüfungsname else "nein") for i in prüfungsname ]

                    #Aussortieren von Prüfungen mit zwei gleichzeitigen Durchläufen:
                    existiert_prüfung=False
                    for prüfung in kalender_daten:
                        vorhandene_prüfung=prüfung[1]
                        vorhandene_prüfung=vorhandene_prüfung.replace("EEC1","EECX")
                        vorhandene_prüfung=vorhandene_prüfung.replace("EEC2","EECX")
                        
                        neue_prüfung=prüfungsname
                        neue_prüfung=neue_prüfung.replace("EEC1","EECX")
                        neue_prüfung=neue_prüfung.replace("EEC2","EECX")

                        if neue_prüfung==vorhandene_prüfung:
                            existiert_prüfung=True
                            break
                    
                    if not existiert_prüfung:
                        prüfungsname=prüfungsname.replace("Durchgang 1","")
                        wiki_url_short=wiki_url_shortener(url)
                        kalender_daten=kalender_daten+[[wiki_url_short,prüfungsname,datum_kalender,status_event,mail]]

                        zähler+=1

    today=datetime.datetime.strptime(datum,"%Y-%m-%d").date()
    liste_fällig=[]
    for eintrag in kalender_daten:
        wiki_url_short=eintrag[0]
        inhalt_rm=wiki_inhalt_abrufen(wiki_url_short)
        inhalt_html=inhalt_rm[1]

        soup = BeautifulSoup(inhalt_html, 'html.parser')
        inhalt_html=soup.find_all('li')
        inhalt_html=list(inhalt_html)

        zähler=-1
        for i in inhalt_html:
            i=str(i)

            if "RM bis zum" in i and 'class="checked"' not in i:
                soup=BeautifulSoup(i,'html.parser')
                mydivs = soup.find("time", {"class": "date-past"})

                if mydivs!=None:
                    datum_rm=mydivs.string
                else:
                    mydivs = soup.find("time", {"class": "date-upcoming"})
                    if mydivs!=None:
                        datum_rm=mydivs.string
                    else:
                        mydivs = soup.find("time", {"class": "date-future"})
                        datum_rm=mydivs.string
        
                datum_rm=datetime.datetime.strptime(datum_rm,"%d.%m.%Y").date()

                if datum_rm<today:

                    datum_rm=datum_rm.strftime("%d.%m.%Y")
                    liste_fällig=liste_fällig+[[f"{eintrag[1]} ({eintrag[2]})",f" RM-Datum: {datum_rm}",eintrag[4], eintrag[0]]]
            


 
    return liste_fällig

eel.abruf_wiki_daten()(wiki_seiten_abrufen)


@eel.expose
def check_mail_credentials(benutzername, passwort):
    global server
    ctx = ssl.create_default_context()
    ctx.set_ciphers('DEFAULT')
    log=False


    server = smtplib.SMTP_SSL(mailadresse, port, context=ctx)

    try:
        server.login(benutzername, passwort) #attempt to log into smtp server
        log="korrekt" #sets to true if log in is successful
    except:
            log="falsch"

    return log

eel.abfrage(check_mail_credentials)

@eel.expose
def check_lehrenden_mail(query):
    print(query)
    for eintrag in query:
        if "@" in eintrag:
            return "korrekt"
    return "falsch"

@eel.expose
def rm_mails_senden(values,tage,benutzername, passwort):
    werte=[values]
    tage=int(tage)
    for eintrag in werte:

        liste_eintrag=eintrag.split(",")
        wiki_url_short=liste_eintrag[-1]
        liste_eintrag.pop(-1)

        inhalt_rm=wiki_inhalt_abrufen(wiki_url_short)
        inhalt_rm=inhalt_rm[0]
        
        """
        datum_rm=liste_eintrag[1]
        while " " in datum_rm:
            datum_rm=datum_rm[1:]
        datum_rm=datetime.datetime.strptime(datum_rm,"%d.%m.%Y").date()
        """

        datum_rm_neu=datetime.datetime.now().date()+datetime.timedelta(days=tage)
        datum_rm_neu_wiki=datum_rm_neu.strftime("%Y-%m-%d")
        datum_rm_neu=datum_rm_neu.strftime("%d.%m.%Y")

        name_prüfung=liste_eintrag[0]
        liste_eintrag.pop(0)

        print(name_prüfung)
        if "[S]" in name_prüfung:
            userkey="20ad2a7e82f723140182f82586ca000b"
        else:
            userkey="20ad2a7e7dd62460017de19e99010007"

        name_prüfung=re.sub("[\(\[].*?[\)\]]", "", name_prüfung)

        liste_eintrag.pop(0)
        mail=liste_eintrag
        for count, item in enumerate(mail):
            
            mail[count]=item.strip()
            print(mail[count])

        print(mail)

        try:
            rm_mail=rm_mail_senden(mail,name_prüfung,datum_rm_neu,benutzername,passwort)

        except:
            rm_mail="Fehlgeschlagen"
        
        neuer_string=f'RM bis zum <time datetime="{datum_rm_neu_wiki}"'

        def wiki_inhalt_anpassen(inhalt_rm,wiki_url_short,neuer_string,userkey):
            inhalt_bs4 = BeautifulSoup(inhalt_rm, 'html.parser')
            inhalt_tasks=inhalt_bs4.find_all('ac:task-body')

            for i in inhalt_tasks:
                if "RM bis" in i.text:           
                    old_tag=i
                    new_tag = inhalt_bs4.new_tag("ac:task-body")
                    new_tag.string = f'<ac:link><ri:user ri:userkey="{userkey}"></ri:user></ac:link> {neuer_string}></time>'
                    old_tag.replace_with(new_tag)

            inhalt_compiled=str(inhalt_bs4)
            inhalt_compiled = inhalt_compiled.replace("&lt;", "<")
            inhalt_compiled = inhalt_compiled.replace("&gt;", ">")

            print(inhalt_compiled)
            return inhalt_compiled
        
        inhalt=wiki_inhalt_anpassen(inhalt_rm,wiki_url_short,neuer_string,userkey)

        try:
            status=wiki_inhalt_manipulieren(inhalt, wiki_url_short)
            wiki_kommentar(wiki_url_short)
            if status==200:
                wiki_inhalt_ergebnis=f" <a href='https://wikis.fu-berlin.de/pages/viewpage.action?pageId={wiki_url_short}' target='_blank'>Erfolgreich</a>"
            else:
                wiki_inhalt_ergebnis=f"<a href='https://wikis.fu-berlin.de/pages/viewpage.action?pageId={wiki_url_short}' target='_blank'>Fehlgeschlagen</a>"
        except:
            wiki_inhalt_ergebnis=f"<a href='https://wikis.fu-berlin.de/pages/viewpage.action?pageId={wiki_url_short}' target='_blank'>Fehlgeschlagen</a>"



    return [name_prüfung,datum_rm_neu,wiki_inhalt_ergebnis,rm_mail]


eel.start("index.html",size=(1200, 900))

