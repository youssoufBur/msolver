#!/bin/bash
#Suppression les dossiers de migration...
echo "Suppression les dossiers de migration..."
find . -type d -name "migrations" -exec rm -rf {} +

#Suppresion de la base de données
echo "Suppresion de la base de données..."
rm -f db.sqlite3
#Migrations
echo "Effectuons les migrations...."
python3 manage.py makemigrations parameter xauth pharmacie health caisse calendarapp hospitalisation actually configuration


python3 manage.py migrate

echo "Insertion de données..."
python3 manage.py pharma
python3 manage.py parametre

echo "Insertion d'un user ..."
python3 manage.py populate

echo "Oppérations éffectuées avec succès!"

echo "Lançons le serveur!"
python3 manage.py runserver