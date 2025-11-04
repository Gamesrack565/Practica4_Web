#Práctica 4: Relaciones con base de datos
#Equipo:
#Beltrán Saucedo Axel Alejandro
#Cerón Samperio Lizeth Montserrat
#Higuera Pineda Angel Abraham
#Lorenzo Silva Abad Rey

from fastapi import FastAPI
from Servicios.base_Datos import create_db_and_tables
from Rutas import categorias, items, envios, optimizar

app = FastAPI(
    title="Práctica 4: Relaciones con Base de Datos (Ordenado)",
    description="API para gestionar Items, Categorías y Envíos, con persistencia de datos.",
    version="2.1.1"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

#Registrar rutas
app.include_router(categorias.router)
app.include_router(items.router)
app.include_router(envios.router)
app.include_router(optimizar.router)
