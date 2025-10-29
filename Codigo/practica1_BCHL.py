#Práctica 4: Relaciones de Datos con Base de Datos
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
# === AJUSTE: Se añade Relationship para las nuevas tablas ===
from sqlmodel import Field, create_engine, Session, SQLModel, Relationship 
#Optional y List son tipos de datos que permiten definir campos opcionales y listas
#Se usan para definir los modelos de datos y las respuestas de la API
from typing import Optional, List
#Annotated es una forma para escribir tipos con metadatos
from typing_extensions import Annotated

# --- 1. Definición de Modelos Base ---

class CategoriaBase(SQLModel):
    """
    Modelo base para una Categoría. Define los campos comunes
    que se usarán para crear y leer categorías.
    """
    nombre: str = Field(index=True, description="Nombre de la categoría (ej. Frágil, Peligroso)")
    descripcion: Optional[str] = Field(default=None, description="Materiales o descripción de la categoría")

class ItemBase(SQLModel):
    """
    Modelo base para un Item. Incluye los campos originales
    y el nuevo campo para la categoría.
    """
    ganancia: float
    peso: float
    # Clave foránea (foreign_key) que apunta al 'id' de la tabla 'categoria'
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id")

class EnvioBase(SQLModel):
    """
    Modelo base para un Envío. Define el destino.
    """
    destino: str

# --- 2. Definición de Modelos de Tabla (BD) ---

class Categoria(CategoriaBase, table=True):
    """
    Modelo de la tabla 'categoria' en la BD.
    Hereda de CategoriaBase y añade un ID.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relación uno-a-muchos:
    # Una categoría puede tener muchos items.
    # "back_populates" enlaza esta relación con "categoria" en el modelo Item.
    items: List["Item"] = Relationship(back_populates="categoria")

class ItemEnvio(SQLModel, table=True):
    """
    Tabla de enlace (link table) para la relación muchos-a-muchos
    entre Item y Envio.
    """
    item_id: Optional[int] = Field(
        default=None, foreign_key="item.id", primary_key=True
    )
    envio_id: Optional[int] = Field(
        default=None, foreign_key="envio.id", primary_key=True
    )

class Item(ItemBase, table=True):
    """
    Modelo de la tabla 'item' en la BD.
    Hereda de ItemBase y añade ID y relaciones.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relación muchos-a-uno:
    # Un item pertenece a una categoría.
    categoria: Optional[Categoria] = Relationship(back_populates="items")
    
    # Relación muchos-a-muchos:
    # Un item puede estar en muchos envíos.
    # "link_model" le dice a SQLModel que use 'ItemEnvio' para esta relación.
    envios: List["Envio"] = Relationship(back_populates="items", link_model=ItemEnvio)

class Envio(EnvioBase, table=True):
    """
    Modelo de la tabla 'envio' en la BD.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relación muchos-a-muchos:
    # Un envío puede contener muchos items.
    items: List[Item] = Relationship(back_populates="envios", link_model=ItemEnvio)

# --- 3. Definición de Modelos de Creación (Input - POST) ---

class CategoriaCreate(CategoriaBase):
    """Modelo para crear una nueva Categoría."""
    pass

class ItemCreate(ItemBase):
    """Modelo para crear un nuevo Item."""
    pass

class EnvioCreate(EnvioBase):
    """Modelo para crear un nuevo Envío. Incluye una lista de IDs de items."""
    item_ids: List[int] = []

# --- 4. Definición de Modelos de Salida (Output - GET) ---
# Usamos modelos "Out" para controlar qué datos se devuelven
# y evitar bucles infinitos en las relaciones.

class CategoriaOut(CategoriaBase):
    """Modelo de salida para Categoría (solo sus datos)."""
    id: int

class ItemOut(ItemBase):
    """Modelo de salida para Item (incluye su categoría si existe)."""
    id: int
    categoria: Optional[CategoriaOut] = None

class EnvioOut(EnvioBase):
    """Modelo de salida para Envío (incluye los items que contiene)."""
    id: int
    items: List[ItemOut] = [] # Devuelve la lista de items completos

# --- 5. Definición de Modelos de Actualización (Input - PATCH) ---

class CategoriaUpdate(SQLModel):
    """Modelo para actualizar una Categoría (todos los campos son opcionales)."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class ItemUpdate(SQLModel):
    """Modelo para actualizar un Item (campos opcionales)."""
    peso: Optional[float] = None
    ganancia: Optional[float] = None
    categoria_id: Optional[int] = None

class EnvioUpdate(SQLModel):
    """Modelo para actualizar un Envío (campos opcionales)."""
    destino: Optional[str] = None
    item_ids: Optional[List[int]] = None # Permite cambiar la lista de items


# --- Configuración de la Base de Datos ---

sql_url="sqlite:///database.db"
engine=create_engine(sql_url)

def create_db_and_tables():
    # SQLModel.metadata.create_all creará TODAS las tablas que heredan de SQLModel
    # (Item, Categoria, Envio, y ItemEnvio)
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep=Annotated[Session, Depends(get_session)] 

# --- Instancia y Arranque de FastAPI ---
app = FastAPI(
    title= "Practica 4: Relaciones de Datos con una Base de Datos",
    description= "API para gestionar Items, Categorías editables y Envíos, con persistencia de datos."
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Endpoints para Categorías (Catálogo Editable) ---

@app.post("/categorias/", response_model=CategoriaOut, tags=["Categorías"])
def create_categoria(categoria: CategoriaCreate, db: SessionDep):
    """Crea una nueva categoría (Frágil, Peligroso, etc.)."""
    db_categoria = Categoria.model_validate(categoria)
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.get("/categorias/", response_model=List[CategoriaOut], tags=["Categorías"])
def get_all_categorias(db: SessionDep):
    """Obtiene la lista de todas las categorías."""
    categorias = db.query(Categoria).all()
    return categorias

@app.get("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
def get_categoria_by_id(categoria_id: int, db: SessionDep):
    """Obtiene una categoría específica por su ID."""
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    return categoria

@app.patch("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
def update_categoria(categoria_id: int, categoria_data: CategoriaUpdate, db: SessionDep):
    """Actualiza el nombre o descripción de una categoría."""
    db_categoria = db.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    
    update_data = categoria_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_categoria, key, value)
    
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categorías"])
def delete_categoria(categoria_id: int, db: SessionDep):
    """Elimina una categoría. Falla si hay items usándola."""
    db_categoria = db.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    
    # Validación: No permitir borrar si hay items asociados
    if db_categoria.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede eliminar la categoría, tiene items asociados.")
        
    db.delete(db_categoria)
    db.commit()
    return

# --- Métodos de la API para Items (Actualizados) ---

@app.post("/items/", response_model=ItemOut, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item_data: ItemCreate, db: SessionDep):
    """Crea un nuevo item, asignándolo opcionalmente a una categoría."""
    # Validar que la categoría exista, si se provee un categoria_id
    if item_data.categoria_id:
        categoria = db.get(Categoria, item_data.categoria_id)
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría con id={item_data.categoria_id} no encontrada")
            
    new_item=Item.model_validate(item_data)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.get("/items/", response_model=List[ItemOut], tags=["Items"])
def get_all_items(db: SessionDep):
    """Obtiene todos los items y la información de su categoría."""
    items=db.query(Item).all()
    return items

@app.get("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def get_item_by_id(item_id: int, db: SessionDep):
    """Obtiene un item por su ID y la información de su categoría."""
    item=db.get(Item, item_id)
    if not item :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    return item

@app.patch("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def update_item_partially(item_id: int, item_update: ItemUpdate, db: SessionDep):
    """Actualiza parcialmente un item (peso, ganancia o categoria_id)."""
    db_item=db.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")

    update_data=item_update.model_dump(exclude_unset=True)
    
    # Validar si se está cambiando la categoría y si la nueva existe
    if "categoria_id" in update_data and update_data["categoria_id"] is not None:
        categoria = db.get(Categoria, update_data["categoria_id"])
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría con id={update_data['categoria_id']} no encontrada")

    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int, db: SessionDep):
    """Elimina un item (esto lo quitará también de cualquier envío)."""
    item_to_delete = db.get(Item, item_id)
    if not item_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    
    # SQLModel/SQLAlchemy se encargará de borrar las entradas
    # en la tabla de enlace 'ItemEnvio' automáticamente.
    db.delete(item_to_delete)
    db.commit()
    return

# --- Métodos de la API para Envíos ---

@app.post("/envios/", response_model=EnvioOut, status_code=status.HTTP_201_CREATED, tags=["Envíos"])
def create_envio(envio_data: EnvioCreate, db: SessionDep):
    """Crea un nuevo envío, asociando una lista de IDs de items existentes."""
    items = []
    if envio_data.item_ids:
        # Buscar los objetos Item que coincidan con los IDs
        items = db.query(Item).filter(Item.id.in_(envio_data.item_ids)).all()
        # Validar que encontramos todos los items solicitados
        if len(items) != len(set(envio_data.item_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más IDs de items no fueron encontrados")

    # Creamos el envío (sin los items aún)
    db_envio = Envio(destino=envio_data.destino)
    # Asignamos la lista de objetos Item a la relación
    db_envio.items = items
    
    db.add(db_envio)
    db.commit()
    db.refresh(db_envio)
    return db_envio

@app.get("/envios/", response_model=List[EnvioOut], tags=["Envíos"])
def get_all_envios(db: SessionDep):
    """Obtiene todos los envíos, incluyendo los items que contiene cada uno."""
    envios = db.query(Envio).all()
    return envios

@app.get("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
def get_envio_by_id(envio_id: int, db: SessionDep):
    """Obtiene un envío específico por ID, incluyendo sus items."""
    envio = db.get(Envio, envio_id)
    if not envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")
    return envio

@app.patch("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
def update_envio(envio_id: int, envio_data: EnvioUpdate, db: SessionDep):
    """Actualiza un envío (destino y/o la lista de items que contiene)."""
    db_envio = db.get(Envio, envio_id)
    if not db_envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")

    update_data = envio_data.model_dump(exclude_unset=True)

    # Manejo especial para la lista de items
    if "item_ids" in update_data:
        item_ids = update_data.pop("item_ids") # Sacamos 'item_ids' del dict
        
        items = []
        if item_ids: # Si la lista no está vacía
            items = db.query(Item).filter(Item.id.in_(item_ids)).all()
            if len(items) != len(set(item_ids)):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más IDs de items no fueron encontrados para actualizar")
        
        # Reemplazamos la lista de items del envío
        db_envio.items = items

    # Actualizar los campos restantes (ej. destino)
    for key, value in update_data.items():
        setattr(db_envio, key, value)
        
    db.add(db_envio)
    db.commit()
    db.refresh(db_envio)
    return db_envio

@app.delete("/envios/{envio_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Envíos"])
def delete_envio(envio_id: int, db: SessionDep):
    """Elimina un envío (esto NO elimina los items, solo la asociación)."""
    db_envio = db.get(Envio, envio_id)
    if not db_envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")
        
    # SQLModel/SQLAlchemy borrará las entradas en 'ItemEnvio'
    db.delete(db_envio)
    db.commit()
    return

# --- Métodos PUT (Reemplazo) ---
# (Se omiten los PUT de la Práctica 3 para mantener el ejemplo
# enfocado en las nuevas funcionalidades, pero se podrían
# re-implementar de forma similar al PATCH si fueran necesarios)