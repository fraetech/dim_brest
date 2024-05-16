#!/usr/bin/env python

'''
Script Python DIM Brest
Description : Le programme s'exécute automatiquement à 12h tous les jours ouvrés 

Amélioration prévue :
Version 2.2 : Nettoyage du code, implémentation de fonctions (optionnel : aller directement dans le CSV choper les infos du nouveau DIM)

-- (V. Actuelle) --
Version 2.1 : Ajout gestion des erreurs Python et leur envoi par SMS
Version 2.0 : Adaptation du script à data.gouv.fr (et non plus la plateforme OpenData de BREST)
Version 1.1 : Correctifs divers de la 1.0
Version 1.0 : Version initiale
'''

try:

	import requests
	import json
	from datetime import datetime, date
	import locale
	import subprocess
	import os
	import pandas as pd
	from datetime import datetime

	h_debut = datetime.now().strftime("%H:%M:%S")
	date_fr = date.today().strftime("%d/%m/%Y")
	print(f"Exécution du {date_fr} à {h_debut}")

	curl = "https://www.data.gouv.fr/api/1/datasets/6491a4d239047754679eb080/"
	reponse = requests.get(curl)

	url_csv = "https://www.data.gouv.fr/fr/datasets/r/1e215dd2-fde6-4a11-8d86-27ebc8d37ae9"

	data = json.loads(reponse.content)

	taille_fichier = data.get('resources', [{}])[0].get('filesize')
	derniere_modif = data.get('last_modified')

	print(f"Taille du fichier téléchargé : {taille_fichier}")
	print(f"Date raw : {derniere_modif}")

	date_obj = datetime.fromisoformat(str(derniere_modif))

	locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

	date_formatee = date_obj.strftime("%d %B %Y à %Hh%M")

	print(f"Date de la dernière modification du fichier : {date_formatee}")

	path_app = os.path.dirname(os.path.abspath(__file__))
	data_path = os.path.join(path_app, 'BR_DIMdata')
	file_path_taille = os.path.join(data_path, 'taille.txt')
	file_path_date = os.path.join(data_path, 'date.txt')
	row_path = os.path.join(data_path, 'row.txt')
	script_sms = os.path.join(path_app, 'EnvoiSMS_V1.1.py')
	script_infos = os.path.join(path_app, 'InfosComp.py')

	date_changed = False
	taille_changed = False

	with open(file_path_date, "r") as file:
		ancienne_date = file.read()

	with open(file_path_taille, "r") as file:
		ancienne_taille = int(file.read())

	with open(row_path, "r") as file:
		row = int(file.read())

	if ancienne_date != derniere_modif:

		date_changed = True

	if ancienne_taille != taille_fichier:
		taille_changed = True

	print(f"Date changée ? {date_changed}")
	print(f"Taille changée ? {taille_changed}")

	def download_data(url, save_path):
		"""Télécharge les données depuis l'URL spécifiée et les sauvegarde dans le fichier indiqué."""
		response = requests.get(url)
		with open(save_path, 'wb') as file:
			file.write(response.content)

	def rename_old_file(old_path, last_path):
		"""Traitement des anciens fichiers"""
		if os.path.exists(old_path):
			os.remove(old_path)
			os.rename(last_path, old_path)

	def load_and_process_csv(old_path, last_path, new_path):
		# Chargement des fichiers CSV
		df_old = pd.read_csv(old_path, sep=";")
		df_last = pd.read_csv(last_path, sep=";")

		# On ne garde que les colonnes qui nous intéressent
		df_old = df_old[['DossierDateCreation', 'DossierNom', 'PieceUrl', 'DossierCommune', 'DossierOperateur', 'DossierQuartier', 'DossierRueNo', 'DossierRueNom', 'PieceType']]
		df_last = df_last[['DossierDateCreation', 'DossierNom', 'PieceUrl', 'DossierCommune', 'DossierOperateur', 'DossierQuartier', 'DossierRueNo', 'DossierRueNom', 'PieceType']]

		# On remplace les espaces dans les URL par "%20"
		df_old['PieceUrl'] = df_old['PieceUrl'].str.replace(' ', '%20')
		df_last['PieceUrl'] = df_last['PieceUrl'].str.replace(' ', '%20')

		df_old = df_old.rename(columns={'DossierNom': 'Nom', 'PieceUrl': 'URL', 'DossierCommune': 'Ville', 'DossierOperateur': 'Operateur', 'DossierQuartier': 'Quartier', 'DossierRueNo': 'RueNo', 'DossierRueNom': 'Rue', 'PieceType': 'Type', 'DossierDateCreation': 'Date_old'})
		df_last = df_last.rename(columns={'DossierNom': 'Nom', 'PieceUrl': 'URL', 'DossierCommune': 'Ville', 'DossierOperateur': 'Operateur', 'DossierQuartier': 'Quartier', 'DossierRueNo': 'RueNo', 'DossierRueNom': 'Rue', 'PieceType': 'Type', 'DossierDateCreation': 'Date_last'})

		# On fait la jointure sur les colonnes communes
		df_merged = pd.merge(df_old, df_last, on=['Nom', 'URL', 'Ville', 'Operateur', 'Quartier', 'RueNo', 'Rue', 'Type'], how='outer')
		# On repère les lignes ajoutées
		df_added = df_merged[df_merged['Date_old'].isna()]
		df_added = df_added.loc[:, df_added.columns != 'Date']

		# Écriture des données ajoutées dans un fichier CSV
		df_added.to_csv(new_path, index=False)
		nb_added = len(df_added)
		print(f"Terminé, il y a {nb_added} nouvelles lignes cette semaine.")

	if taille_changed == True and date_changed == False:
		#Cas que je n'ai pour l'instant jamais vu, mais sait-on jamais..
		subprocess.run(["python", script_sms, f"WARN - DIM_Script_Brest.py : Taille changée, date inchangée. Ancienne taille : {ancienne_taille}, nouvelle taille : {taille_fichier}."])
		row = 0
		with open(row_path, "w") as file:
			file.write(str(row))
		with open(file_path_taille, "w") as file:
			file.write(str(taille_fichier))
		print("WARN - Taille changée, date inchangée.")

	elif taille_changed == False and date_changed == True:
		#Pas de SMS, scénario arrivant tous les jours : fichier à jour, mais pas de nouveau DIM.
		row = 0
		with open(row_path, "w") as file:
			file.write(str(row))
		with open(file_path_date, "w") as file:
			file.write(derniere_modif)
		print("OK - Fichier inchangé mais à jour.")

	elif taille_changed == True and date_changed == True:
		#Un nouveau DIM a été publié.
		save_path = os.path.join(data_path, 'dim.csv')
		old_path = os.path.join(data_path, 'dim_old.csv')
		last_path = os.path.join(data_path, 'dim.csv')
		new_path = os.path.join(data_path, 'dim_added.csv')

		rename_old_file(old_path, last_path)
		download_data(url_csv, save_path)
		load_and_process_csv(old_path, last_path, new_path)

		subprocess.run(["python", script_sms, f"OK - DIM_Script_Brest.py : MAJ totale du {date_formatee}."])
		subprocess.run(["python", script_infos])
		row = 0
		with open(row_path, "w") as file:
			file.write(str(row))
		with open(file_path_taille, "w") as file:
			file.write(str(taille_fichier))
		with open(file_path_date, "w") as file:
			file.write(derniere_modif)
		print("OK - MAJ totale.")

	elif taille_changed == False and date_changed == False:
		#Action à réaliser lorsqu'il ne se passe rien (WE, jours fériés, ou à cause d'une erreur qui empêche d'atteindre data.gouv par ex).
		row += 1
		if row >=9:
			subprocess.run(["python", script_sms, f"WARN - DIM_Script_Brest.py : Rien n'a été modifié pour plus de {row} jours consécutifs. You should take a look at it. :P Prochain rappel dans 10 jours sans modification."])
			row = 0
			with open(row_path, "w") as file:
				file.write(str(row))
		print("WARN - Pas de changement ni dans la date, ni dans le contenu.")
		#Cas courant le WE, vacances, férié etc.. Mais anormal sur une trop longue période.
		with open(row_path, "w") as file:
			file.write(str(row))

	else:
		#Si jamais aucune des conditions précédente n'est remplie (ce qui n'est pas normal).
		subprocess.run(["python", script_sms, f"ERROR - DIM_Script_Brest.py : Shit happened."])

	h_fin = datetime.now().strftime("%H:%M:%S")
	print(f"Fin d'éxécution le {date_fr} à {h_fin}")

	
except Exception as e:
	#Si une erreur Python a lieu, elle est également remontée.
	subprocess.run(["python", script_sms, f"ERROR - DIM_Script_Brest.py : Shit happened (py-error) : {str(e)}."])
	print(e)