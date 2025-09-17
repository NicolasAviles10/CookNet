from deep_translator import GoogleTranslator

"""
RecipeBot — Healthy Recipe AI Assistant

Este módulo implementa un agente conversacional que sugiere recetas saludables usando IA, embeddings y búsqueda vectorial.

Requisitos:
- Instala los paquetes necesarios:
  pip install langgraph==0.3.21 langchain-google-genai==2.1.2 langgraph-prebuilt==0.1.7 google-genai faiss-cpu sentence-transformers huggingface_hub[hf_xet] python-dotenv
- Descarga el dataset de recetas (ejemplo: RAW_recipes.csv de Kaggle) y colócalo en la carpeta 'data/'
- Crea un archivo .env con tu GOOGLE_API_KEY
"""

import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from dotenv import load_dotenv
import faiss
import json
from google import genai
from google.genai import types

# Cargar clave API
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# Usar modelo Django para obtener recetas
from django.apps import apps




def cargar_recetas_embeddings(ingredientes_usuario=None):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        Receta = apps.get_model('app_inicio', 'Receta')
        recetas_qs = Receta.objects.all()
        # Si hay ingredientes, filtra las recetas relevantes
        if ingredientes_usuario:
            lista_ingredientes = [i.strip() for i in ingredientes_usuario.replace(',', ' ').split() if i.strip()]
            from django.db.models import Q
            query = Q()
            for ingr in lista_ingredientes:
                query |= Q(ingredients__icontains=ingr)
            recetas_qs = recetas_qs.filter(query)
        recetas_qs = recetas_qs[:100] 
        translator = GoogleTranslator(source='en', target='es')
        recipe_texts = []
        recipe_vectors = []
        for index, receta in enumerate(recetas_qs):
            nombre_es = translator.translate(receta.name) if receta.name else ''
            descripcion_es = translator.translate(receta.description) if receta.description else ''
            ingredientes_es = translator.translate(receta.ingredients) if receta.ingredients else ''
            pasos_es = translator.translate(receta.steps) if receta.steps else ''
            tags_es = translator.translate(receta.tags) if receta.tags else ''
            text = f"""
            Nombre de la receta: {nombre_es}
            Descripción: {descripcion_es}
            Ingredientes: {ingredientes_es}
            Pasos: {pasos_es}
            Etiquetas: {tags_es}
            """
            recipe_texts.append(text)
            embedding = model.encode(text, show_progress_bar=False)
            recipe_vectors.append(embedding)
            if index % 20 == 0:
                print(f"Embedded {index} recetas...")
        if not recipe_vectors:
            print("No se encontraron recetas relevantes para los ingredientes dados.")
            return model, [], np.array([])
        embeddings = np.array(recipe_vectors)
        print(f"✅ Embeddings generados para {len(recipe_texts)} recetas relevantes.")
        return model, recipe_texts, embeddings
        nombre_es = translator.translate(receta.name) if receta.name else ''
        descripcion_es = translator.translate(receta.description) if receta.description else ''
        ingredientes_es = translator.translate(receta.ingredients) if receta.ingredients else ''
        pasos_es = translator.translate(receta.steps) if receta.steps else ''
        tags_es = translator.translate(receta.tags) if receta.tags else ''
        text = f"""
        Nombre de la receta: {nombre_es}
        Descripción: {descripcion_es}
        Ingredientes: {ingredientes_es}
        Pasos: {pasos_es}
        Etiquetas: {tags_es}
        """
        recipe_texts.append(text)
        embedding = model.encode(text, show_progress_bar=False)
        recipe_vectors.append(embedding)
        if index % 500 == 0:
            print(f"Embedded {index} recetas...")
        embeddings = np.array(recipe_vectors)
        print("✅ Embeddings generados y traducidos al español desde la base de datos.")
        return model, recipe_texts, embeddings

# Recuperar recetas similares
def retrieve_similar_recipes(model, recipe_texts, embeddings, user_ingredients, top_k=3):
    embeddings_dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(embeddings_dim)
    faiss_index.add(embeddings)
    query_vector = model.encode([user_ingredients])
    query_vector = np.array(query_vector).astype('float32')
    D, I = faiss_index.search(query_vector, top_k)
    return [recipe_texts[idx] for idx in I[0]]

# Ejemplos para few-shot prompting
FEW_SHOTS_EXAMPLE = """
Example 1:
{
  "name": "Tomato Pasta",
  "ingredients": ["tomato", "onion", "pasta"],
  "description": "A simple and dairy-free pasta with tomato sauce and onions.",
  "steps": ["Boil water", "Add oil, salt (to taste) and Pasta to boiled water", "Chop Italian tomatoes, vegetables", "Check pasta cooked well, becomes soft"],
  "estimated_time": 25,
  "healthy": true
}

Example 2:
{
  "name": "Pasta with Vegan Cheese and Vegetables",
  "ingredients": ["pasta", "vegan cheese", "broccoli", "bell peppers", "olive oil", "garlic"],
  "description": "A quick and healthy pasta dish using dairy-free cheese and your favorite vegetables.",
  "steps": ["Boil water", "Add oil, salt (to taste) and Pasta to boiled water", "Chop vegetables, onions, garlic, spinatch", "Check pasta cooked well, becomes soft"],
  "estimated_time": 30,
  "healthy": true
}

Example 3:
{
  "name": "Avocado Toast",
  "ingredients": ["bread", "avocado", "salt"],
  "description": "Avocado toast sandwich",
  "steps": ["Toast bread", "Mash avocado", "Assemble and season."],
  "estimated_time": 20,
  "healthy": true
}
"""

# Agente principal
def recipebot_agent(user_ingredients, user=None):
    """
    RecipeBot Agent Function:
    - Busca recetas similares usando vector search (RAG)
    - Prioriza favoritos del usuario
    - Construye prompt few-shot para Gemini
    - Llama Gemini 2.0 Flash para generar receta saludable en JSON
    """
    # Recupera favoritos si hay usuario
    favoritos_texts = []
    if user is not None:
        from app_inicio.models import UsuarioFavorito
        favoritos = UsuarioFavorito.objects.filter(user=user).select_related('receta')
        for fav in favoritos:
            favoritos_texts.append(fav.receta.name)
    model, recipe_texts, embeddings = cargar_recetas_embeddings(user_ingredients)
    if not recipe_texts or embeddings.size == 0:
        return "No se encontraron recetas relevantes para los ingredientes dados."
    retrieved = retrieve_similar_recipes(model, recipe_texts, embeddings, user_ingredients)
    # Agrega favoritos al prompt si existen
    favoritos_context = ""
    if favoritos_texts:
        favoritos_context = f"Recetas favoritas del usuario: {', '.join(favoritos_texts)}. Prioriza estas recetas en tu sugerencia si son relevantes."
    prompt = f"""
{favoritos_context}
Responde SIEMPRE en español. Eres un chef experto en cocina saludable y tu tarea es sugerir una receta clara, fácil y sabrosa usando los ingredientes del usuario y sus favoritos si existen.
Si alguna de las recetas favoritas del usuario es relevante para los ingredientes, priorízala y explica la razón en el campo "razon".
Formato de respuesta: JSON con los campos name, razon, ingredients, description, steps, estimated_time, healthy.
El campo "razon" debe explicar brevemente por qué elegiste esa receta para el usuario (por ejemplo: por los ingredientes, por ser saludable, por ser favorita, etc).
Ejemplo:
{{
    "name": "Tomato Pasta",
    "razon": "Elegí esta receta porque el usuario tiene tomate y pasta, y es una opción saludable y fácil de preparar.",
    "ingredients": ["tomate", "cebolla", "pasta"],
    "description": "Una pasta sencilla y sin lácteos con salsa de tomate y cebolla.",
    "steps": ["Hervir agua", "Agregar aceite, sal y pasta", "Picar tomates italianos y verduras", "Verificar que la pasta esté cocida y suave"],
    "estimated_time": 25,
    "healthy": true
}}
{FEW_SHOTS_EXAMPLE}
Ahora, usando los siguientes ingredientes y contexto, genera una receta saludable y bien explicada en español:
Ingredientes del usuario: {user_ingredients}
Recetas similares encontradas: {retrieved}
Recuerda: la respuesta debe ser solo el JSON, sin texto adicional, y todo en español.
"""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return response.text

# Bucle de interacción por consola

def call_with_loop_until_exit():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye! Happy Cooking")
            break
        print("🤖 RecipeBot is thinking...")
        recipe = recipebot_agent(user_input)
        print("\n✅ Here’s a healthy recipe for you:\n")
        print(recipe)
        print("\n---------------------------------------")

# Prueba rápida
if __name__ == "__main__":
    res = json.loads(recipebot_agent("suggest a chicken recipe for dinner for two"))
    print(json.dumps(res, indent=2))
    # call_with_loop_until_exit()  # Descomenta para usar el bot en bucle
