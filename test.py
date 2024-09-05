#!/usr/bin/env python
import sys
import requests
import json
from datetime import datetime, date
import locale
import subprocess
import os
import pandas as pd

# Initialisation du format de date en français
def initialize_locale():
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Journalisation de l'heure de début et de fin de l'exécution
def log_time(event):
    date_fr = date.today().strftime("%d/%m/%Y")
    heure = datetime.now().strftime("%H:%M:%S")
    print(f"{event} le {date_fr} à {heure}")

# Téléchargement des données depuis une URL et conversion en JSON
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Extraction de la taille du fichier et de la date de modification
def extract_file_info(data):
    taille_fichier = data.get('resources', [{}])[0].get('filesize', 0)
    derniere_modif = data.get('last_modified', "")
    print(f"Taille du fichier : {taille_fichier}, Date : {derniere_modif}")
    return taille_fichier, derniere_modif

# Formatage de la date ISO en un format français lisible
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %B %Y à %Hh%M")

# Lecture simple d'un fichier
def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read().strip()

# Mise à jour du contenu d'un fichier
def update_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(str(content))

# Fonction pour traiter les nouvelles lignes et mettre à jour le fichier si nécessaire
def process_new_DIM(data_path, url_csv):
    old_path = os.path.join(data_path, 'dim_old.csv')
    last_path = os.path.join(data_path, 'dim.csv')
    new_path = os.path.join(data_path, 'dim_added.csv')

    rename_file(last_path, old_path)  # Renommer l'ancien fichier
    download_data(url_csv, last_path)  # Télécharger les nouvelles données
    return load_and_process_csv(old_path, last_path, new_path)  # Traitement des nouvelles lignes

# Fonction pour comparer et fusionner les anciens et nouveaux fichiers CSV
def load_and_process_csv(old_path, last_path, new_path):
    df_old = pd.read_csv(old_path, sep=";")
    df_last = pd.read_csv(last_path, sep=";")

    df_old, df_last = format_dataframe(df_old), format_dataframe(df_last)
    df_merged = pd.merge(df_old, df_last, on=['Nom', 'URL', 'Ville', 'Operateur', 'Quartier', 'RueNo', 'Rue', 'Type'], how='outer')
    
    df_added = df_merged[df_merged['Date_old'].isna()].loc[:, df_merged.columns != 'Date']
    df_added.to_csv(new_path, index=False)
    
    nb_added = len(df_added)
    print(f"{nb_added} nouvelles lignes cette semaine.")
    return nb_added > 0

# Mise en forme commune des DataFrames
def format_dataframe(df):
    df = df[['DossierDateCreation', 'DossierNom', 'PieceUrl', 'DossierCommune', 'DossierOperateur', 'DossierQuartier', 'DossierRueNo', 'DossierRueNom', 'PieceType']]
    df['PieceUrl'] = df['PieceUrl'].str.replace(' ', '%20')
    return df.rename(columns={'DossierNom': 'Nom', 'PieceUrl': 'URL', 'DossierCommune': 'Ville', 'DossierOperateur': 'Operateur', 'DossierQuartier': 'Quartier', 'DossierRueNo': 'RueNo', 'DossierRueNom': 'Rue', 'PieceType': 'Type', 'DossierDateCreation': 'Date_old'})

# Téléchargement et enregistrement des nouvelles données CSV
def download_data(url, save_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(save_path, 'wb') as file:
        file.write(response.content)

# Renommer un fichier si nécessaire
def rename_file(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    if os.path.exists(src):
        os.rename(src, dst)

# Envoi de SMS via un script externe
def send_sms(script_sms, message):
    subprocess.run([sys.executable, script_sms, message])

# Gestion des changements de taille et/ou de date, ainsi que des nouvelles lignes
def handle_changes(taille_changed, date_changed, nvelles_lignes, taille_fichier, derniere_modif, ancienne_taille, script_sms, file_path_date, file_path_taille, date_formatee):
    if taille_changed and not date_changed:
        send_sms(script_sms, f"DIM_BREST: WARN - Taille changée, date inchangée. Ancienne taille : {ancienne_taille}, nouvelle taille : {taille_fichier}.")
        update_file(file_path_taille, taille_fichier)
        print("WARN - Taille changée, date inchangée.")
    elif not taille_changed and date_changed:
        update_file(file_path_date, derniere_modif)
        print("OK - Fichier à jour.")
    elif taille_changed and date_changed:
        if nvelles_lignes:
            send_sms(script_sms, f"DIM_BREST: OK - MAJ totale du {date_formatee}.")
            update_file(file_path_taille, taille_fichier)
            update_file(file_path_date, derniere_modif)
            print("OK - MAJ totale avec nouvelles lignes.")
        else:
            send_sms(script_sms, f"DIM_BREST: INFO - Date et taille changée, mais pas de nouvelle ligne.")
            update_file(file_path_taille, taille_fichier)
            update_file(file_path_date, derniere_modif)

# Gestion en cas d'absence de changement
def handle_no_change(script_sms, row, row_path):
    row += 1
    if row >= 9:
        send_sms(script_sms, f"DIM_BREST: WARN - Aucun changement depuis {row} jours.")
        row = 0
    update_file(row_path, row)
    print(f"WARN - Pas de changement depuis {row} jours.")

# Fonction principale
def main():
    try:
        initialize_locale()
        log_time("Début d'exécution")

        # Chemins des fichiers
        path_app = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(path_app, 'BR_DIMdata')
        file_path_taille = os.path.join(data_path, 'taille.txt')
        file_path_date = os.path.join(data_path, 'date.txt')
        row_path = os.path.join(data_path, 'row.txt')
        script_sms = os.path.join(path_app, 'EnvoiSMS.py')

        # URL des données
        url_csv = "https://www.data.gouv.fr/fr/datasets/r/1e215dd2-fde6-4a11-8d86-27ebc8d37ae9"
        data = fetch_data("https://www.data.gouv.fr/api/1/datasets/6491a4d239047754679eb080/")
        taille_fichier, derniere_modif = extract_file_info(data)
        date_formatee = format_date(derniere_modif)

        # Lecture des anciens fichiers
        ancienne_date = read_file(file_path_date)
        ancienne_taille = int(read_file(file_path_taille))
        row = int(read_file(row_path))

        # Comparaison des changements
        date_changed = ancienne_date != derniere_modif
        taille_changed = ancienne_taille != taille_fichier

        # Gestion des changements
        if taille_changed or date_changed:
            nvelles_lignes = process_new_DIM(data_path, url_csv)
            handle_changes(taille_changed, date_changed, nvelles_lignes, taille_fichier, derniere_modif, ancienne_taille, script_sms, file_path_date, file_path_taille, date_formatee)
        else:
            handle_no_change(script_sms, row, row_path)

        log_time("Fin d'exécution")

    except Exception as e:
        error_message = f"ERROR - {str(e)}"
        send_sms(os.path.join(os.path.dirname(__file__), 'EnvoiSMS.py'), error_message)
        print(error_message)

if __name__ == "__main__":
    main()