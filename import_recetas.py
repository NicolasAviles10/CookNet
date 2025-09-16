import csv
from app_inicio.models import Receta
from django.utils.dateparse import parse_date

def run():
    with open('D:/Admin sist/RAW_recipes.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        recetas = []
        for row in reader:
            receta = Receta(
                name=row['name'],
                receta_id=int(row['id']),
                minutes=int(row['minutes']),
                contributor_id=int(row['contributor_id']),
                submitted=parse_date(row['submitted']),
                tags=str(row['tags']),
                nutrition=str(row['nutrition']),
                n_steps=int(row['n_steps']),
                steps=str(row['steps']),
                description=row['description'],
                ingredients=str(row['ingredients']),
                n_ingredients=int(row['n_ingredients'])
            )
            recetas.append(receta)
        Receta.objects.bulk_create(recetas, batch_size=500)
    print("¡Importación completada!")