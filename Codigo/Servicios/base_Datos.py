from sqlmodel import SQLModel, create_engine, Session
from typing_extensions import Annotated
from fastapi import Depends

#--- Base de Datos ---
sql_url="sqlite:///database.db"
engine=create_engine(sql_url)

#Define una funcion para crear la base de datos y las tablas.
def create_db_and_tables():
    #Ordena a SQLModel que cree todas las tablas que heredan de 'SQLModel' (con table=True).
    SQLModel.metadata.create_all(engine)

#Define un generador para gestionar las sesiones de la base de datos.
def get_session():
    #Crea una nueva sesion usando el motor.
    with Session(engine) as session:
        #Proporciona la sesion a la funcion del endpoint.
        yield session
        #El bloque 'with' asegura que la sesion se cierre automaticamente.

#Crea un alias 'SessionDep' para la inyeccion de dependencias de la sesion.
SessionDep=Annotated[Session, Depends(get_session)] 