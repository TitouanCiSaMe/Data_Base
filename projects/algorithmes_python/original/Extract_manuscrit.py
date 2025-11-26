import json
import requests
from tqdm import tqdm
import time  # Ajoutez cette ligne

def extract_ids(json_obj, key):
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            if k == key:
                yield v
            else:
                yield from extract_ids(v, key)
    elif isinstance(json_obj, list):
        for item in json_obj:
            yield from extract_ids(item, key)

def download_image(url, path):
    response = requests.get(url)
    with open(path, 'wb') as f:
        f.write(response.content)

# Remplacez 'your_file.json' par le chemin de votre fichier JSON
with open('/home/titouan/Téléchargements/Manuscrit_télécharger/manifest.json', 'r') as f:
    data = json.load(f)

ids = list(extract_ids(data, '@id'))

# Écriture des ids dans un fichier texte
jpg_ids = [id for id in ids if id.endswith('.jpg')]
with open('/home/titouan/Téléchargements/Manuscrit_télécharger/urls_to_download.txt', 'w') as f:
    for id in jpg_ids:
        f.write(id + '\n')

# Téléchargement des images avec une barre de progression
for i in tqdm(range(1, len(jpg_ids))):
    id = jpg_ids[i]
    download_image(id, f'//home/titouan/Téléchargements/Manuscrit_télécharger/Latin_18108/Latin_18108_{i}.jpg')
    time.sleep(5)  # Augmentez le délai à 20 secondes