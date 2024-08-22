#!/usr/bin/env python

import requests
import json
from datetime import datetime, date
import locale
import subprocess
import os
import pandas as pd

def initialize_locale():
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

def log_start_time():
    date_fr = date.today().strftime("%d/%m/%Y")
    h_debut = datetime.now().strftime("%H:%M:%S")
    print(f"Exécution du {date_fr} à {h_debut}")

def log_end_time():
    date_fr = date.today().strftime("%d/%m/%Y")
    h_fin = datetime.now().strftime("%H:%M:%S")
    print(f"Fin d'exécution le {date_fr} à {h_fin}")

def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes
    return json.loads(response.content)

def extract_file_info(data):
    taille_fichier = data.get('resources', [{}])[0].get('filesize')
    derniere_modif = data.get('last_modified')
    print(f"Taille du fichier téléchargé : {taille_fichier}")
    print(f"Date raw : {derniere_modif}")
    return taille_fichier, derniere_modif

def format_date(iso_date):
    date_obj = datetime.fromisoformat(iso_date)
    return date_obj.strftime("%d %B %Y à %Hh%M")

def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read().strip()

def handle_changes(taille_changed, date_changed, nvelles_lignes, row, file_path_date, file_path_taille, row_path, taille_fichier, derniere_modif, script_sms, script_infos, date_formatee, data_path, url_csv, ancienne_taille):
    if taille_changed and not date_changed:
        send_sms(script_sms, f"WARN - Taille changée, date inchangée, nouvelles lignes insérées. Ancienne taille : {ancienne_taille}, nouvelle taille : {taille_fichier}.")
        reset_row(row_path)
        update_file(file_path_taille, taille_fichier)
        print("WARN - Taille changée, date inchangée.")

    elif not taille_changed and date_changed:
        reset_row(row_path)
        update_file(file_path_date, derniere_modif)
        print("OK - Fichier inchangé mais à jour.")

    elif taille_changed and date_changed:
        if nvelles_lignes:
            process_new_DIM(data_path, url_csv)
            send_sms(script_sms, f"OK - MAJ totale du {date_formatee}.")
            subprocess.run(["python", script_infos])
            reset_row(row_path)
            update_file(file_path_taille, taille_fichier)
            update_file(file_path_date, derniere_modif)
            print("OK - MAJ totale.")
        else:
            send_sms(script_sms, f"INFO - Date et taille changée. Mais pas de nouvelle ligne.")
            print(taille_fichier)
            print(derniere_modif)
            update_file(file_path_taille, taille_fichier)
            update_file(file_path_date, derniere_modif)

def handle_no_change(row, row_path, script_sms):
    row += 1
    if row >= 9:
        send_sms(script_sms, f"WARN - Rien n'a été modifié pour plus de {row} jours consécutifs.")
        row = 0
    update_file(row_path, row)
    print("WARN - Pas de changement.")

def process_new_DIM(data_path, url_csv):
    save_path = os.path.join(data_path, 'dim.csv')
    old_path = os.path.join(data_path, 'dim_old.csv')
    last_path = os.path.join(data_path, 'dim.csv')
    new_path = os.path.join(data_path, 'dim_added.csv')

    rename_old_file(old_path, last_path)
    download_data(url_csv, save_path)
    load_and_process_csv(old_path, last_path, new_path)

def send_sms(script_sms, message):
    subprocess.run(["python", script_sms, message])

def update_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(str(content))

def reset_row(row_path):
    update_file(row_path, 0)

def download_data(url, save_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(save_path, 'wb') as file:
        file.write(response.content)

def rename_old_file(old_path, last_path):
    if os.path.exists(old_path):
        os.remove(old_path)
        os.rename(last_path, old_path)

def load_and_process_csv(old_path, last_path, new_path):
    df_old = pd.read_csv(old_path, sep=";")
    df_last = pd.read_csv(last_path, sep=";")

    df_old = df_old[['DossierDateCreation', 'DossierNom', 'PieceUrl', 'DossierCommune', 'DossierOperateur', 'DossierQuartier', 'DossierRueNo', 'DossierRueNom', 'PieceType']]
    df_last = df_last[['DossierDateCreation', 'DossierNom', 'PieceUrl', 'DossierCommune', 'DossierOperateur', 'DossierQuartier', 'DossierRueNo', 'DossierRueNom', 'PieceType']]

    df_old['PieceUrl'] = df_old['PieceUrl'].str.replace(' ', '%20')
    df_last['PieceUrl'] = df_last['PieceUrl'].str.replace(' ', '%20')

    df_old = df_old.rename(columns={'DossierNom': 'Nom', 'PieceUrl': 'URL', 'DossierCommune': 'Ville', 'DossierOperateur': 'Operateur', 'DossierQuartier': 'Quartier', 'DossierRueNo': 'RueNo', 'DossierRueNom': 'Rue', 'PieceType': 'Type', 'DossierDateCreation': 'Date_old'})
    df_last = df_last.rename(columns={'DossierNom': 'Nom', 'PieceUrl': 'URL', 'DossierCommune': 'Ville', 'DossierOperateur': 'Operateur', 'DossierQuartier': 'Quartier', 'DossierRueNo': 'RueNo', 'DossierRueNom': 'Rue', 'PieceType': 'Type', 'DossierDateCreation': 'Date_last'})

    df_merged = pd.merge(df_old, df_last, on=['Nom', 'URL', 'Ville', 'Operateur', 'Quartier', 'RueNo', 'Rue', 'Type'], how='outer')
    df_added = df_merged[df_merged['Date_old'].isna()].loc[:, df_merged.columns != 'Date']

    df_added.to_csv(new_path, index=False)
    nb_added = len(df_added)
    print(f"Terminé, il y a {nb_added} nouvelles lignes cette semaine.")
    return nb_added > 0

def handle_error(exception):
    error_message = f"ERROR - DIM_Script_Brest.py : {str(exception)}"
    print(error_message)
    subprocess.run(["python", os.path.join(os.path.dirname(os.path.abspath(__file__)), 'EnvoiSMS_V1.1.py'), error_message])
    
def main():
    try:
        initialize_locale()
        log_start_time()

        # Configuration des chemins de fichiers
        path_app = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(path_app, 'BR_DIMdata')
        file_path_taille = os.path.join(data_path, 'taille.txt')
        file_path_date = os.path.join(data_path, 'date.txt')
        row_path = os.path.join(data_path, 'row.txt')
        script_sms = os.path.join(path_app, 'EnvoiSMS_V1.1.py')
        script_infos = os.path.join(path_app, 'InfosComp.py')

        # Téléchargement et analyse des données
        url_csv = "https://www.data.gouv.fr/fr/datasets/r/1e215dd2-fde6-4a11-8d86-27ebc8d37ae9"
        data = fetch_data("https://www.data.gouv.fr/api/1/datasets/6491a4d239047754679eb080/")
        taille_fichier, derniere_modif = extract_file_info(data)
        date_formatee = format_date(derniere_modif)

        ancienne_date = read_file(file_path_date)
        ancienne_taille = int(read_file(file_path_taille))
        row = int(read_file(row_path))

        date_changed = ancienne_date != derniere_modif
        taille_changed = ancienne_taille != taille_fichier

        print(f"Date changée ? {date_changed}")
        print(f"Taille changée ? {taille_changed}")

        if taille_changed or date_changed:
            handle_changes(taille_changed, date_changed, nvelles_lignes=False, row=row, file_path_date=file_path_date, file_path_taille=file_path_taille, row_path=row_path, taille_fichier=taille_fichier, derniere_modif=derniere_modif, script_sms=script_sms, script_infos=script_infos, date_formatee=date_formatee, data_path=data_path, url_csv=url_csv, ancienne_taille=ancienne_taille)
        else:
            handle_no_change(row=row, row_path=row_path, script_sms=script_sms)

        log_end_time()

    except Exception as e:
        handle_error(e)

if __name__ == "__main__":
    main()