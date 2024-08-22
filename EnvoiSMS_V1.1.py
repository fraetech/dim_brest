#!/usr/bin/env python

'''
Script Envoi SMS
Description : Le programme, prend en paramètre un argument qui est le message à envoyer par SMS directement.

Amélioration prévue :
N/A

-- (V. Actuelle) --
Version 1.1 : Le script ne se base plus sur des messages prédéfinis pour envoyer ses SMS. Il envoie ce qui lui est mis en paramètre directement.
Il n'est ainsi plus nécessaire de prédéfinir les messages dans ce script directement.
Version 1.0 : Version initiale
'''
import requests
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("USER")
key = os.getenv("KEY")

message = sys.argv[1]
url = f'https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={message}'

reponse = requests.get(url)

if reponse.status_code == 200:
	print('SMS envoyé avec succès !')
else:
	print(f"Erreur lors de l'envoi du SMS. Code d'erreur : {reponse.status_code}.")