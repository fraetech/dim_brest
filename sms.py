#!/usr/bin/env python
import requests
import functions_dim
import os
from dotenv import load_dotenv
import sys

def load_environment_variables():
    load_dotenv()
    user = os.getenv("USER")
    key = os.getenv("KEY")
    if not user or not key:
        raise ValueError("Les variables d'environnement USER et KEY doivent être définies.")
    return user, key

def send_sms(user, key, message):
    url = f'https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={message}'
    response = requests.get(url)
    return response.status_code

def main():
    try:
        if len(sys.argv) != 2:
            functions_dim.log_message("Usage: python EnvoiSMS.py 'Votre message ici'")
            sys.exit(1)
        
        user, key = load_environment_variables()
        message = sys.argv[1]
        status_code = send_sms(user, key, message)
        
        if status_code == 200:
            functions_dim.log_message('SMS envoyé avec succès !')
        else:
            functions_dim.log_message(f"Erreur lors de l'envoi du SMS. Code d'erreur : {status_code}.")
    
    except Exception as e:
        functions_dim.log_message(f"Erreur : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
