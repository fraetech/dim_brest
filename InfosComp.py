#!/usr/bin/env python

'''
Script Python DIM Brest
Description : Le programme s'exécute automatiquement à 12h tous les jours ouvrés 

Amélioration prévue :
Version 2.2 : Nettoyage du code, implémentation de fonctions (optionnel : aller directement dans le CSV choper les infos du nouveau DIM)

-- (V. Actuelle) --
Version 1.1 : Amélioration de la version initiale (ajout de fonctions)
Version 1.0 : Version initiale
'''

import csv
import smtplib
import os
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

# Variables globales pour les informations de login et de mail
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 587
MAIL_SENDER = os.getenv("MAIL_SENDER")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_RECIPIENT = os.getenv("MAIL_RECIPIENT")

# Paths globaux
path_app = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(path_app, 'BR_DIMdata')
new_path = os.path.join(data_path, 'dim_added.csv')
script_sms = os.path.join(path_app, 'EnvoiSMSpy')

def creation_mail(nb_dim):
    subject = f"{nb_dim} nouveaux DIM aujourd'hui !" if nb_dim > 1 else "Un nouveau DIM aujourd'hui !"
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = MAIL_SENDER
    msg['To'] = MAIL_RECIPIENT
    return msg

def contenu_mail(msg, new_path):
    with open(new_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        content = ""
        for i, row in enumerate(csvreader):
            if i == 0:
                continue
            line = ' - '.join([row[4], row[3], row[5], f'{row[6]} {row[7]} - ({row[8]}) :'])
            line += '\n' + row[2] + '\n'
            if i != 1:
                content += '\n'
            content += line
        msg.attach(MIMEText(content, 'plain'))

def envoi_mail(msg):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(MAIL_SENDER, MAIL_PASSWORD)
            smtp.sendmail(MAIL_SENDER, MAIL_RECIPIENT, msg.as_string())
        print('E-mail envoyé avec succès !')
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")

def envoi_sms(new_path):
    with open(new_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        nb_dim_ByTel = nb_dim_Free = nb_dim_ORF = nb_dim_SFR = nb_dim_autre = 0
        for i, row in enumerate(csvreader):
            if i == 0:
                continue
            if row[4] == 'BOUYGUES TELECOM':
                nb_dim_ByTel += 1
            elif row[4] == 'FREE MOBILE':
                nb_dim_Free += 1
            elif row[4] == 'ORANGE':
                nb_dim_ORF += 1
            elif row[4] == 'SFR':
                nb_dim_SFR += 1
            else:
                nb_dim_autre += 1

        content = f"DIM_BREST: INFO - Nb de DIM par opé :\n"
        if nb_dim_ByTel: content += f"ByTel : {nb_dim_ByTel}\n"
        if nb_dim_Free: content += f"Free : {nb_dim_Free}\n"
        if nb_dim_ORF: content += f"Orange : {nb_dim_ORF}\n"
        if nb_dim_SFR: content += f"SFR : {nb_dim_SFR}\n"
        if nb_dim_autre: content += f"Autre : {nb_dim_autre}\n"

        nb_total = nb_dim_ByTel + nb_dim_Free + nb_dim_ORF + nb_dim_SFR + nb_dim_autre
        subprocess.run(["python", script_sms, content.rstrip()])
        return nb_total

def main():
    try:
        # SMS
        nb_dims = envoi_sms(new_path)

        # MAIL
        msg = creation_mail(nb_dims)
        contenu_mail(msg, new_path)
        envoi_mail(msg)

    except Exception as e:
        subprocess.run(["python", script_sms, f"DIM_BREST: ERROR - InfoComp.py : Shit happened (py-error) : {str(e)}."])
        print(e)

if __name__ == "__main__":
    main()