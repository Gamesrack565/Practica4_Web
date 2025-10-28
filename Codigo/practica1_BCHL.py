#Práctica 3: Permanencia de Datos con Base de Datos
#Equipo:
#Beltrán Saucedo Axel Alejandro
#Cerón Samperio Lizeth Montserrat
#Higuera Pineda Angel Abraham
#Lorenzo Silva Abad Rey

#Para que pueda arrancar, se debe instalar sqlmodel: pip install sqlmodel 
#Recordar que se debe ejecutar/iniciar el servidor en la terminal
#Con el comando: python -m uvicorn Codigo.practica1_BCHL:app --reload
#Al parecer se debe especificar lo de python, ya que puede que no detecte el uvicorn sin el
#Para ver la pagina y realizar operaciones, visitar: http://127.0.0.1:8000/docs

#Importamos los modulos (librerias) necesarias

#FastApi es el modulo principal, HTTPException es un manejador de errores, como el "no encontrado" 
#Status es un modulo de indentificacion de codigos de estado HTTP, como el clasico 404
#Depends es un mecanismo para poder inyectar dependencias
from fastapi import FastAPI, HTTPException, status, Depends
#Field es usado para definir las propieddes de los campos del modelo
#create_engine se usa para crear un motor que conectara la base de datos con la aplicacion
#Session es el enncargado de manejar la comunicacion con la base de datos
#SQLModel sera la base para los modelos de datos
from sqlmodel import Field, create_engine, Session, SQLModel
#Optional y List son tipos de datos que permiten definir campos opcionales y listas
#Se usan para definir los modelos de datos y las respuestas de la API
from typing import Optional, List
#Annotated es una forma para escribir tipos con metadatos
from typing_extensions import Annotated

#Creamos la instancia de FastAPI
#Es el corazon de nuestro programa (API)
app = FastAPI(
    #Nombre y descripcion de la API
    title= "Practica 3: Permanencia de Datos con una Base de Datos",
    description= "API para almacenar, editar, actualizar y borrar la información de los paquetes (items) a ser enviados," 
    "garantizando la persistencia de los datos mediante una base de datos"
)

#Estructura de los datos con Pydantic

#ItemBase es la estructura base de un item, con los campos ganancia y peso
#Digamos que es lo que tiene cada item
#Esta obtiene las funcionalidades de Pydantic y SQLAlchemy heredandolas de SQLModel
class ItemBase(SQLModel):
    ganancia: float
    peso: float
#Item contiene el indentificador unico (id) y hereda los campos de ItemBase
#y con table=True se marca como una tabla
class Item(ItemBase, table=True):
    id: Optional[int]=Field(default=None, primary_key=True)
#Los campos son opcionales, ya que podemos querer actualizar solo uno de ellos
#El valor por defecto es None
#primary_key marca el campo como la clave primaria(ID)

#ItemCreate sera usado para recibir los datos cuando estemos creando un nuevo item
#Hereda de ItemBase
class ItemCreate(ItemBase):
    pass

#ItemOut nos ayudara a colocar en el orden deseado nuestras respuestas
class ItemOut(SQLModel):
    peso: float
    ganancia: float
    id: int

#ItemUpdate sera usado para recibir los datos cuando queramos actualizar un item con PATCH
class ItemUpdate(SQLModel):
    peso: Optional[float] = None
    ganancia: Optional[float] = None

# Conexion a la base de datos

#La cadena sqlite:///database.db indica que vamos a usar un archivo local llamda 'database.db'
#como nuestra base de datos
sql_url="sqlite:///databse.db"
#Crea el motor de la base de datos, que sera el encargado de gestionar la conexion
engine=create_engine(sql_url)

#Funcion encarga de crear la tabla 'item' en la base de datos
def create_db_and_tables():
    #SQLModel.metadata... sera el que checara que todos los modelos que heredan de SQLModel,
    #y que ademas esten marcado con table=True, y les creara sus tablas en la base de datos
    SQLModel.metadata.create_all(engine)

#Funcion encargada de crear y proporcionar una sesion de base de datos por cada peticion
def get_session():
    #Abre una nueva sesion con el motor(engine) de la base de datos
    with Session(engine) as session:
        #Yield dara la sesion al endpoint de nuestra API
        yield session
#SessionDep es una anotacion que usa a Depends para inyectar una sesion de base de datos
#en nuestras funciones
SessionDep=Annotated[Session, Depends(get_session)] 


#On_event le dice a FastAPI que ejecute lo siguiente una sola vez cuando iniciamos la aplicacion
@app.on_event("startup")
def on_startup():
    #Llamamos a create_db... para tener la seguridad de que la base de datos y sus tablas ya fueron
    #creadas antes de que la aplicacion reciba peticiones
    create_db_and_tables()

#Metodos de la API - Lo importante

#Get: Permite obtener todos los items
@app.get("/items/", response_model=list[ItemOut], tags=["Items"])
#La funcion recibira una sesion de base de datos
def get_all_items(db: SessionDep):
    #db.query crea un objeto de consulta para la tabla 'Item'
    #.all devuelve todos los resultados como una lista
    items=db.query(Item).all()
    return items

#En /items/{item_id} -Se debe especificar el id correcto del objeto

#Get: Permite obtener un item por su id 
@app.get("/items/{item_id}", response_model=ItemOut, tags=["Items"])
#La funcion recibe el 'item_id' de la URL, ademas de una sesion de base de datos
def get_item_by_id(item_id: int, db: SessionDep):
    #Recorremos la lista de items para encontrar el que tiene el id que buscamos
    item=db.get(Item, item_id)
    #Si no se encuentra en la base de datos, marcamos un error 404 (no encontrado)
    if not item :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    #Si se encuentra da el item    
    return item

#Post: Permite crear un item nuevo 
#Se devuelve el codigo 201 (creado) si todo sale bien
@app.post("/items/", response_model=ItemOut, status_code=status.HTTP_201_CREATED, tags=["Items"])
#Esta funcion recibe los datos del item nuevo y una sesion de base de datos, cortesia de Session Dep
def create_item(item_data: ItemCreate, db: SessionDep):
    #Transforma el objeto de entrada en un objeto del modelo de la tabla 'item'
    new_item=Item.model_validate(item_data)
    #db.add agrega el nuevo objeto a la sesion
    db.add(new_item)
    #db.commit confirma que los datos se hayan escrito en la base de datos
    db.commit()
    #db.refresh refresca new item con los datos de la base de datos y asi obtener el ID asignado
    db.refresh(new_item)
    return new_item


#Put: Remplaza un item existente por completo por su id 
@app.put("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def replace_item(item_id: int, item_data: ItemBase, db: SessionDep):
    #Se obtiene el item a actualizar de la base de datos
    db_item=db.get(Item, item_id)
    #Si no existe, devolvemos error 404 (no encontrado)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    #model_dump transforma los datos de entrada en un diccionario
    item_data_dict=item_data.model_dump()
    #Se recorre este diccionario con los nuevos datos
    for key, value in item_data_dict.items():
        #setattr actualiza cada uno de los atributos del objeto con el nuevo valor
        setattr(db_item, key, value)

    #Agregamos el objeto actualizado a la sesion de base de datos para marcarlo como cambiado
    db.add(db_item)
    #Los cambios se guardan en la base de datos
    db.commit()
    #Refrescamos el objeto para estar seguros que tenemos la nueva version de la base de datos
    db.refresh(db_item)
    return db_item

#Patch: Actualiza parcialmente un item por su id 
@app.patch("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def update_item_partially(item_id: int, item_update: ItemUpdate, db: SessionDep):
    #Se busca el objeto que queremos actualizar en la base de datos
    db_item=db.get(Item, item_id)
    #Si no lo encontramos, regresamos error 404 (no encontrado)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    #model_dump... transforma el objeto de entrada en un diccionario,
    #pero aqui se excluye los campos que el usuario no envio
    update_data=item_update.model_dump(exclude_unset=True)
    #Se recorre solo los campos que el usuario desea actualizar
    for key, value in update_data.items():
        #setattr actualiza los atributos en el objeto de la base de datos
        setattr(db_item, key, value)

    #Agregamos el objeto actualizado y lo marcamos como cambiado
    db.add(db_item)
    #Los cambios se guardan en la base de datos
    db.commit()
    #Refrescamos el objeto para asegurarnos que sea la version mas reciente
    db.refresh(db_item)
    return db_item

#Delete: Borra un item por su id 
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int, db: SessionDep):
    #Se busca el item a borrar
    item_to_delete = db.get(Item, item_id)
    #Si no se encuentra, marcamos un error 404 (no encontrado)
    if not item_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    #db.delete... marca el item para ser eliminado en la sesion
    db.delete(item_to_delete)
    #db.commit confirma la eliminacion de la base de datos
    db.commit()
    return