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

try:

    import csv
    import smtplib
    import os
    import subprocess
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    path_app = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(path_app, 'BR_DIMdata')
    new_path = os.path.join(data_path, 'dim_added.csv')
    script_sms = os.path.join(path_app, 'EnvoiSMS_V1.1.py')

    def creation_mail(nb_dim):
        msg = MIMEMultipart()
        msg['Subject'] = f"{nb_dim} nouveaux DIM cette semaine !" if nb_dim > 1 else "Un nouveau DIM cette semaine !"
        msg['From'] = 'MAILEXPEMAILEXPE'
        msg['To'] = 'MAILDESTIMAILDESTI'
        return msg

    def contenu_mail(msg, new_path):
        with open(new_path, newline = '') as csvfile :
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            content = ""
            for i, row in enumerate(csvreader):
                if i == 0:
                    continue
                line = ' - '.join([row[4], row[3], row[5], f'{row[6]} {row[7]} - ({row[8]}) :']) # Opé, ville, quartier, rue, type
                line += '\n'
                line += row[2]  # le lien est contenu dans la troisième colonne
                line += '\n'
                if i != 1:
                    content += '\n'
                content += line
        msg.attach(MIMEText(content, 'plain'))

    def envoi_mail(msg):
        with smtplib.SMTP('smtp.free.fr', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login('MAILEXPEMAILEXPE', 'MDPMAILEXPEMDPMAILEXPE')
            smtp.sendmail('MAILEXPEMAILEXPE', 'MAILDESTIMAILDESTI', msg.as_string())
        print('E-mail envoyé !')

    def envoi_sms(new_path):
        with open(new_path, newline = '') as csvfile :
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            content = "Nb de DIM par opé :"
            content += '\n'
            nb_dim_ByTel = 0
            nb_dim_Free = 0
            nb_dim_ORF = 0
            nb_dim_SFR = 0
            nb_dim_autre = 0
            nb_total = 0
            for i, row in enumerate(csvreader):
                if i == 0:
                    continue
                if str(row[4]) == 'BOUYGUES TELECOM':
                    nb_dim_ByTel += 1
                    continue
                if str(row[4]) == 'FREE MOBILE':
                    nb_dim_Free += 1
                    continue
                if str(row[4]) == 'ORANGE':
                    nb_dim_ORF += 1
                    continue
                if str(row[4]) == 'SFR':
                    nb_dim_SFR += 1
                    continue
                else:
                    nb_dim_autre += 1
            nb_total = nb_dim_ByTel + nb_dim_Free + nb_dim_ORF + nb_dim_SFR + nb_dim_autre
            if nb_dim_ByTel != 0:
                content += f"ByTel : {nb_dim_ByTel}"
                content += '\n'
            if nb_dim_Free != 0:
                content += f"Free : {nb_dim_Free}"
                content += '\n'
            if nb_dim_ORF != 0:
                content += f"Orange : {nb_dim_ORF}"
                content += '\n'
            if nb_dim_SFR != 0:
                content += f"SFR : {nb_dim_SFR}"
                content += '\n'
            if nb_dim_autre != 0:
                content += f"Autre : {nb_dim_autre}"
                content += '\n'
            subprocess.run(["python", script_sms, content.rstrip()])
            return nb_total


    # SMS
    nb_dims = envoi_sms(new_path)

    # MAIL
    msg = creation_mail(nb_dims)
    contenu_mail(msg, new_path)
    envoi_mail(msg)

except Exception as e:
	#Si une erreur Python a lieu, elle est également remontée.
	subprocess.run(["python", script_sms, f"ERROR - InfoComp.py (DIM BREST) : Shit happened (py-error) : {str(e)}."])
	print(e)