# Práctica 4: Relaciones con base de datos
# Equipo:
# Beltrán Saucedo Axel Alejandro
# Cerón Samperio Lizeth Montserrat
# Higuera Pineda Angel Abraham
# Lorenzo Silva Abad Rey

# Para que pueda arrancar, se debe instalar sqlmodel: pip install sqlmodel
# Recordar que se debe ejecutar/iniciar el servidor en la terminal
# Con el comando: python -m uvicorn practica1_BCHL:app --reload # Ajusta practica1_BCHL al nombre de tu archivo si es diferente
# Para ver la pagina y realizar operaciones, visitar: http://127.0.0.1:8000/docs

# --- Importaciones de Módulos Necesarios ---

# FastAPI es el módulo principal para crear la API.
# HTTPException se usa para manejar errores HTTP (ej. "no encontrado").
# status contiene códigos de estado HTTP estándar (ej. 404, 201).
# Depends se usa para la inyección de dependencias (ej. obtener la sesión de BD).
from fastapi import FastAPI, HTTPException, status, Depends

# SQLModel es la base para definir nuestros modelos de datos que se mapearán en la BD.
# Field se usa para configurar detalles de los campos del modelo (ej. primary_key, foreign_key).
# create_engine crea el motor de conexión a la base de datos.
# Session maneja la comunicación (transacciones) con la base de datos.
# Relationship define las relaciones entre diferentes modelos/tablas (ej. un Item pertenece a una Categoria).
from sqlmodel import Field, create_engine, Session, SQLModel, Relationship, select

# Optional y List son tipos de datos de Python para definir campos que pueden ser None o listas.
from typing import Optional, List

# Annotated se usa junto con Depends para crear un tipo anotado para la inyección de dependencias de la sesión.
from typing_extensions import Annotated


from sqlalchemy.orm import joinedload

from .Algoritmo_genetico import AlgoritmoGenetico, SeleccionRuleta
# --- Definición de Modelos Base ---
# Estos modelos definen la estructura fundamental de los datos,
# sin incluir IDs o detalles específicos de la tabla de BD.

class CategoriaBase(SQLModel):
    """Modelo base para Categoría: define los campos esenciales."""
    # MODIFICADO: Se añade 'unique=True' para asegurar que no haya nombres duplicados.
    nombre: str = Field(index=True, description="Nombre de la categoría (ej. Frágil, Peligroso)", unique=True)
    descripcion: Optional[str] = Field(default=None, description="Materiales o descripción de la categoría")

class ItemBase(SQLModel):
    """Modelo base para Item: campos originales sin IDs de relación."""
    # MODIFICADO: Se elimina 'categoria_id' para permitir una relación muchos-a-muchos.
    ganancia: float
    peso: float

class EnvioBase(SQLModel):
    """Modelo base para Envío: define el destino."""
    destino: str

# --- Definición de Modelos de Tabla (BD) ---
# Estos modelos representan las tablas en la base de datos.
# Heredan de los modelos Base y añaden el ID y las relaciones.
# 'table=True' le indica a SQLModel que cree una tabla para este modelo.

# --- NUEVO ---
class ItemCategoria(SQLModel, table=True):
    """
    Tabla de enlace (asociativa) para la relación muchos-a-muchos
    entre Item y Categoria. Contiene las claves foráneas de ambas tablas.
    """
    item_id: Optional[int] = Field(
        default=None, foreign_key="item.id", primary_key=True # Parte de la clave primaria compuesta.
    )
    categoria_id: Optional[int] = Field(
        default=None, foreign_key="categoria.id", primary_key=True # Parte de la clave primaria compuesta.
    )

class Categoria(CategoriaBase, table=True):
    """Modelo de la tabla 'categoria'. Incluye ID y la relación con Items."""
    id: Optional[int] = Field(default=None, primary_key=True) # Clave primaria autogenerada.
    
    # MODIFICADO: Relación muchos-a-muchos: Una categoría puede tener muchos 'Item'.
    # 'back_populates' conecta esta relación con el atributo 'categorias' (plural) en el modelo 'Item'.
    items: List["Item"] = Relationship(back_populates="categorias", link_model=ItemCategoria)

class ItemEnvio(SQLModel, table=True):
    """
    Tabla de enlace (asociativa) para la relación muchos-a-muchos
    entre Item y Envio. Contiene las claves foráneas de ambas tablas.
    """
    item_id: Optional[int] = Field(
        default=None, foreign_key="item.id", primary_key=True # Parte de la clave primaria compuesta.
    )
    envio_id: Optional[int] = Field(
        default=None, foreign_key="envio.id", primary_key=True # Parte de la clave primaria compuesta.
    )

class Item(ItemBase, table=True):
    """Modelo de la tabla 'item'. Incluye ID y relaciones con Categoria y Envio."""
    id: Optional[int] = Field(default=None, primary_key=True) # Clave primaria autogenerada.
    
    # MODIFICADO: Se elimina la relación 'categoria' (muchos-a-uno) anterior.
    
    # --- NUEVO ---
    # Relación muchos-a-muchos: Un item puede tener muchas 'Categoria'.
    # 'link_model=ItemCategoria' especifica la tabla de enlace a usar.
    # 'back_populates' conecta con el atributo 'items' en 'Categoria'.
    categorias: List[Categoria] = Relationship(back_populates="items", link_model=ItemCategoria)
    
    # Relación muchos-a-muchos: Un item puede estar en muchos 'Envio'.
    # 'link_model=ItemEnvio' especifica la tabla de enlace a usar.
    # 'back_populates' conecta con el atributo 'items' en 'Envio'.
    envios: List["Envio"] = Relationship(back_populates="items", link_model=ItemEnvio)

class Envio(EnvioBase, table=True):
    """Modelo de la tabla 'envio'. Incluye ID y la relación con Items."""
    id: Optional[int] = Field(default=None, primary_key=True) # Clave primaria autogenerada.
    
    # Relación muchos-a-muchos: Un envío puede contener muchos 'Item'.
    items: List[Item] = Relationship(back_populates="envios", link_model=ItemEnvio)

# ---  Definición de Modelos de Creación (Input - POST) ---
# Estos modelos se usan para validar los datos que se reciben en las peticiones POST.
# Heredan de los modelos Base correspondientes.

class CategoriaCreate(CategoriaBase):
    """Esquema de datos esperado al crear una Categoría."""
    pass # No necesita campos adicionales a CategoriaBase

class ItemCreate(ItemBase):
    """Esquema de datos esperado al crear un Item."""
    # MODIFICADO: Se usa una lista de nombres de categorías en lugar de un ID.
    categoria_nombres: List[str] = Field(default=[], description="Lista de nombres de categorías a las que pertenece el item.")

class EnvioCreate(EnvioBase):
    """Esquema de datos esperado al crear un Envío. Se añade lista de IDs de Items."""
    item_ids: List[int] = [] # Lista de IDs de los items a incluir inicialmente.

# --- Definición de Modelos de Salida (Output - GET) ---
# Estos modelos definen qué campos se devolverán en las respuestas de la API.
# Ayudan a evitar referencias circulares y a mostrar datos relacionados de forma legible.

class CategoriaOut(CategoriaBase):
    """Cómo se verá una Categoría en la respuesta (incluye ID)."""
    id: int

class ItemOut(ItemBase):
    """Cómo se verá un Item en la respuesta (incluye ID y datos de sus categorías)."""
    # MODIFICADO: Se cambia 'categoria' por 'categorias' (plural).
    id: int
    categorias: List[CategoriaOut] = [] # Muestra la lista de categorías asociadas.

class EnvioOut(EnvioBase):
    """Cómo se verá un Envío en la respuesta (incluye ID y la lista de Items)."""
    id: int
    items: List[ItemOut] = [] # Muestra los items completos asociados.

# --- Definición de Modelos de Actualización (Input - PATCH) ---
# Estos modelos se usan para validar los datos en peticiones PATCH.
# Todos los campos son opcionales, permitiendo las actualizaciones parciales.

class CategoriaUpdate(SQLModel):
    """Esquema para actualizar una Categoría (nombre y/o descripción)."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class ItemUpdate(SQLModel):
    """Esquema para actualizar un Item (peso, ganancia y/o categorías)."""
    # MODIFICADO: Se cambia 'categoria_id' por 'categoria_nombres'.
    peso: Optional[float] = None
    ganancia: Optional[float] = None
    categoria_nombres: Optional[List[str]] = Field(default=None, description="Lista de nombres para reemplazar las categorías del item.")

class EnvioUpdate(SQLModel):
    """Esquema para actualizar un Envío (destino y/o lista de items)."""
    destino: Optional[str] = None
    item_ids: Optional[List[int]] = None # Permite reemplazar la lista de items.

# --- Configuración de la Base de Datos ---

# Define la URL de conexión. 'sqlite:///database.db' indica usar un archivo SQLite local.
sql_url="sqlite:///database.db"
# Crea el 'engine', que es el punto central de comunicación con la BD.
engine=create_engine(sql_url) # Puedes añadir echo=True para ver las consultas SQL: create_engine(sql_url, echo=True)

def create_db_and_tables():
    """Crea todas las tablas definidas por los modelos SQLModel (si no existen)."""
    # SQLModel.metadata contiene la información de todas las tablas definidas.
    # .create_all() ejecuta los comandos SQL necesarios para crearlas.
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Generador de sesiones de base de datos para inyección de dependencias.
    Asegura que cada petición tenga su propia sesión y se cierre al final.
    """
    # 'with Session(engine)' crea una nueva sesión y la maneja (abre y cierra).
    with Session(engine) as session:
        yield session # Entrega la sesión a la función del endpoint.

# Crea un tipo anotado 'SessionDep' que FastAPI usará para inyectar
# una sesión de BD (obtenida de get_session) en los parámetros de los endpoints.
SessionDep=Annotated[Session, Depends(get_session)] 

# --- Instancia y Arranque de FastAPI ---

# Crea la aplicación FastAPI principal.
app = FastAPI(
    title= "Practica 4: Relaciones de Datos con una Base de Datos",
    description= "API para gestionar Items, Categorías editables y Envíos, con persistencia de datos."
)

# Registra una función para que se ejecute una vez al inicio de la aplicación.
@app.on_event("startup")
def on_startup():
    """Función que se ejecuta al iniciar la API para crear las tablas."""
    create_db_and_tables()

# --- Endpoints para Categorías (Catálogo Editable) ---

# Define un endpoint para crear nuevas categorías.
@app.post("/categorias/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED, tags=["Categorías"])
def create_categoria(categoria: CategoriaCreate, db: SessionDep):
    """Crea una nueva categoría (Frágil, Peligroso, etc.)."""
    
    # MODIFICADO: Validación para asegurar que el nombre sea único
    db_categoria_existente = db.query(Categoria).filter(Categoria.nombre == categoria.nombre).first()
    if db_categoria_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de la categoría ya existe")
        
    # Valida los datos recibidos (categoria) contra el modelo CategoriaCreate.
    # Crea una instancia del modelo de tabla Categoria.
    db_categoria = Categoria.model_validate(categoria)
    db.add(db_categoria) # Añade el nuevo objeto a la sesión.
    db.commit() # Guarda los cambios en la BD.
    db.refresh(db_categoria) # Recarga el objeto desde la BD (para obtener el ID asignado).
    return db_categoria # Devuelve el objeto creado.

# Define un endpoint para obtener todas las categorías.
@app.get("/categorias/", response_model=List[CategoriaOut], tags=["Categorías"])
def get_all_categorias(db: SessionDep):
    """Obtiene la lista de todas las categorías."""
    # Ejecuta una consulta para seleccionar todos los registros de la tabla Categoria.
    categorias = db.query(Categoria).all()
    return categorias # Devuelve la lista de categorías.

# Define un endpoint para obtener una categoría por su ID.
@app.get("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
def get_categoria_by_id(categoria_id: int, db: SessionDep):
    """Obtiene una categoría específica por su ID."""
    # Busca la categoría con el ID proporcionado.
    categoria = db.get(Categoria, categoria_id)
    # Si no se encuentra, lanza un error 404.
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    return categoria # Devuelve la categoría encontrada.

# Define un endpoint para actualizar parcialmente una categoría.
@app.patch("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
def update_categoria(categoria_id: int, categoria_data: CategoriaUpdate, db: SessionDep):
    """Actualiza el nombre o descripción de una categoría."""
    # Busca la categoría a actualizar.
    db_categoria = db.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    
    # Convierte los datos de actualización a un diccionario, excluyendo los no enviados.
    update_data = categoria_data.model_dump(exclude_unset=True)
    
    # MODIFICADO: Validación de unicidad si se cambia el nombre
    if "nombre" in update_data:
        nombre_nuevo = update_data["nombre"]
        db_categoria_existente = db.query(Categoria).filter(Categoria.nombre == nombre_nuevo).first()
        if db_categoria_existente and db_categoria_existente.id != categoria_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de la categoría ya existe")

    # Actualiza solo los campos proporcionados en el objeto de la BD.
    for key, value in update_data.items():
        setattr(db_categoria, key, value)
    
    db.add(db_categoria) # Marca el objeto como modificado en la sesión.
    db.commit() # Guarda los cambios.
    db.refresh(db_categoria) # Recarga desde la BD.
    return db_categoria # Devuelve el objeto actualizado.

# Define un endpoint para eliminar una categoría.
@app.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categorías"])
def delete_categoria(categoria_id: int, db: SessionDep):
    """Elimina una categoría. Falla si hay items usándola."""
    # Busca la categoría a eliminar.
    db_categoria = db.get(Categoria, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    
    # Validación importante: Verifica si la relación 'items' no está vacía.
    # Esta validación funciona igual para relaciones M2M.
    if db_categoria.items:
        # Si hay items, no permite borrar y lanza un error 400.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede eliminar la categoría, tiene items asociados.")
        
    db.delete(db_categoria) # Marca la categoría para eliminarla.
    db.commit() # Ejecuta la eliminación.
    # No se devuelve contenido (status 204).
    return

# --- Métodos de la API para Items (Actualizados con Categoría) ---

# Define un endpoint para crear un nuevo item.
# MODIFICADO: Se cambia la lógica para aceptar nombres de categorías (M2M).
@app.post("/items/", response_model=ItemOut, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item_data: ItemCreate, db: SessionDep):
    """Crea un nuevo item, asignándolo a una o más categorías existentes por nombre."""
    
    categorias = []
    # 1. Buscar las categorías por nombre si se proporcionaron
    if item_data.categoria_nombres:
        # Busca en la BD todas las Categorias cuyos nombres estén en la lista.
        categorias = db.query(Categoria).filter(Categoria.nombre.in_(item_data.categoria_nombres)).all()
        
        # 2. Validación: Comprueba si se encontraron todas las categorías solicitadas.
        if len(categorias) != len(set(item_data.categoria_nombres)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Una o más categorías no fueron encontradas")
    
    # 3. Crea el diccionario de datos del item base (excluyendo la lista de nombres).
    item_dict = item_data.model_dump(exclude={"categoria_nombres"})
    # 4. Crea la instancia del modelo Item.
    new_item = Item(**item_dict)
    
    # 5. Asigna la lista de objetos Categoria encontrados a la relación.
    # SQLModel se encargará de crear las entradas en la tabla de enlace 'ItemCategoria'.
    new_item.categorias = categorias
    
    # 6. Guarda en la BD
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    # SQLModel cargará automáticamente las categorías para el 'ItemOut'.
    return new_item

# Define un endpoint para obtener todos los items.
@app.get("/items/", response_model=List[ItemOut], tags=["Items"])
def get_all_items(db: SessionDep):
    """Obtiene todos los items y la información de sus categorías."""
    # Consulta todos los items. SQLModel se encarga de cargar las relaciones necesarias
    # para el modelo de respuesta ItemOut (incluyendo las categorías).
    items=db.query(Item).all()
    return items

# Define un endpoint para obtener un item por ID.
@app.get("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def get_item_by_id(item_id: int, db: SessionDep):
    """Obtiene un item por su ID y la información de sus categorías."""
    # Busca el item por ID.
    item=db.get(Item, item_id)
    if not item :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    # Devuelve el item encontrado (con sus categorías cargadas si existen).
    return item

# Define un endpoint para actualizar parcialmente un item.
# MODIFICADO: Se cambia la lógica para actualizar la lista de categorías por nombre.
@app.patch("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def update_item_partially(item_id: int, item_update: ItemUpdate, db: SessionDep):
    """Actualiza parcialmente un item (peso, ganancia o lista de categorías por nombre)."""
    # Busca el item a actualizar.
    db_item=db.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")

    # Obtiene los datos a actualizar (solo los enviados por el cliente).
    update_data=item_update.model_dump(exclude_unset=True)
    
    # 1. Manejo especial para la lista de categorías
    if "categoria_nombres" in update_data:
        # 2. Extrae la lista de nombres (puede ser None, [], o ["nombre1", ...])
        nombres = update_data.pop("categoria_nombres") 
        
        categorias = []
        # 3. Si la lista no es None (permitiendo que '[]' borre todas las categorías)
        if nombres is not None: 
            # 4. Busca los items correspondientes a los nuevos IDs.
            categorias = db.query(Categoria).filter(Categoria.nombre.in_(nombres)).all()
            # 5. Validación
            if len(categorias) != len(set(nombres)):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Una o más categorías no fueron encontradas para actualizar")
        
        # 6. Reemplaza completamente la lista de categorías asociadas.
        # SQLModel actualizará la tabla de enlace 'ItemCategoria'.
        db_item.categorias = categorias

    # 7. Actualiza los atributos restantes del objeto en memoria (peso, ganancia).
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    # Devuelve el item actualizado (con la lista de categorías actualizada).
    return db_item

# Define un endpoint para eliminar un item.
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int, db: SessionDep):
    """Elimina un item (esto lo quitará también de cualquier envío y categoría)."""
    # Busca el item a eliminar.
    item_to_delete = db.get(Item, item_id)
    if not item_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    
    # Al borrar el Item, SQLAlchemy/SQLModel se encarga automáticamente
    # de eliminar las referencias en las tablas de enlace 'ItemEnvio' y 'ItemCategoria'.
    db.delete(item_to_delete)
    db.commit()
    # No devuelve contenido.
    return

# --- Métodos de la API para Envíos ---

# Define un endpoint para crear un nuevo envío.
@app.post("/envios/", response_model=EnvioOut, status_code=status.HTTP_201_CREATED, tags=["Envíos"])
def create_envio(envio_data: EnvioCreate, db: SessionDep):
    """Crea un nuevo envío, asociando una lista de IDs de items existentes."""
    items = [] # Lista para guardar los objetos Item encontrados.
    # Si se proporcionaron IDs de items...
    if envio_data.item_ids:
        # ...busca en la BD todos los Items cuyos IDs estén en la lista proporcionada.
        items = db.query(Item).filter(Item.id.in_(envio_data.item_ids)).all()
        # Validación: Comprueba si el número de items encontrados coincide con el número de IDs únicos pedidos.
        if len(items) != len(set(envio_data.item_ids)):
            # Si no coinciden, significa que al menos un ID no correspondía a un item existente.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más IDs de items no fueron encontrados")

    # Crea la instancia del modelo Envio solo con el destino.
    db_envio = Envio(destino=envio_data.destino)
    # Asigna la lista de objetos Item encontrados a la relación 'items' del envío.
    # SQLModel/SQLAlchemy se encargará de gestionar la tabla de enlace 'ItemEnvio'.
    db_envio.items = items
    
    db.add(db_envio) # Añade el nuevo envío a la sesión.
    db.commit() # Guarda el envío y las relaciones en la BD.
    db.refresh(db_envio) # Recarga el envío para obtener su ID.
    # Devuelve el envío creado, incluyendo la lista de items asociados.
    return db_envio

# Define un endpoint para obtener todos los envíos.
@app.get("/envios/", response_model=List[EnvioOut], tags=["Envíos"])
def get_all_envios(db: SessionDep):
    """Obtiene todos los envíos, incluyendo los items que contiene cada uno."""
    # Consulta todos los envíos. SQLModel cargará automáticamente la lista 'items'
    # para que coincida con el modelo de respuesta EnvioOut.
    envios = db.query(Envio).all()
    return envios

# Define un endpoint para obtener un envío por ID.
@app.get("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
def get_envio_by_id(envio_id: int, db: SessionDep):
    """Obtiene un envío específico por ID, incluyendo sus items."""
    # Busca el envío por ID.
    envio = db.get(Envio, envio_id)
    if not envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")
    # Devuelve el envío encontrado (con su lista de items cargada).
    return envio

# Define un endpoint para actualizar parcialmente un envío.
@app.patch("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
def update_envio(envio_id: int, envio_data: EnvioUpdate, db: SessionDep):
    """Actualiza un envío (destino y/o la lista completa de items que contiene)."""
    # Busca el envío a actualizar.
    db_envio = db.get(Envio, envio_id)
    if not db_envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")

    # Obtiene los datos a actualizar (solo los enviados).
    update_data = envio_data.model_dump(exclude_unset=True)

    # Manejo especial para la lista de items: si se incluye 'item_ids' en la petición...
    if "item_ids" in update_data:
        # ...extrae la lista de IDs del diccionario de datos.
        item_ids = update_data.pop("item_ids") 
        
        items = [] # Lista para los nuevos objetos Item.
        # Si la lista de IDs no es None (puede ser una lista vacía `[]` para quitar todos los items)...
        if item_ids is not None: 
            # ...busca los items correspondientes a los nuevos IDs.
            items = db.query(Item).filter(Item.id.in_(item_ids)).all()
            # Validación: Asegura que todos los IDs proporcionados existan.
            if len(items) != len(set(item_ids)):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más IDs de items no fueron encontrados para actualizar")
        
        # Reemplaza completamente la lista de items asociados al envío.
        # SQLModel/SQLAlchemy actualizará la tabla de enlace 'ItemEnvio'.
        db_envio.items = items

    # Actualiza los campos restantes (en este caso, solo 'destino').
    for key, value in update_data.items():
        setattr(db_envio, key, value)
        
    db.add(db_envio) # Marca el envío como modificado.
    db.commit() # Guarda los cambios.
    db.refresh(db_envio) # Recarga el envío desde la BD.
    # Devuelve el envío actualizado (con la nueva lista de items).
    return db_envio

# Define un endpoint para eliminar un envío.
@app.delete("/envios/{envio_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Envíos"])
def delete_envio(envio_id: int, db: SessionDep):
    """Elimina un envío (esto NO elimina los items, solo la asociación en la tabla de enlace)."""
    # Busca el envío a eliminar.
    db_envio = db.get(Envio, envio_id)
    if not db_envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")
        
    # Al borrar el Envio, SQLAlchemy/SQLModel elimina automáticamente
    # las filas correspondientes en la tabla de enlace 'ItemEnvio'.
    db.delete(db_envio)
    db.commit()
    # No devuelve contenido.
    return


# --- Métodos PUT (Reemplazo Completo) ---
# Se omiten para simplificar, pero podrían añadirse si se necesita reemplazar
# un recurso completo en lugar de actualizarlo parcialmente.
# Su implementación sería similar al PATCH, pero usando model_dump() sin exclude_unset.



@app.post("/optimizar/{envio_id}", tags=["Algoritmo Genético"])
def optimizar_envio(envio_id: int, capacidad: float):
    with Session(engine) as session:
        #Obtenemos el envío por su ID
        envio = session.get(Envio, envio_id)
        if not envio:
            raise HTTPException(status_code=404, detail="Envío no encontrado")

        #Los items se obtienen directamente desde la relación
        items = envio.items
        if not items:
            raise HTTPException(status_code=400, detail="Este envío no tiene items")

        # Obtenemos pesos y ganancias
        pesos = [i.peso for i in items]
        ganancias = [i.ganancia for i in items]

        # Ejecutamos el algoritmo genético
        ag = AlgoritmoGenetico(pesos, ganancias, capacidad, SeleccionRuleta())
        
        # 1. 'ejecutar()' devuelve un objeto 'Sujetos', lo llamamos 'mejor_solucion'
        mejor_solucion = ag.ejecutar()

        # 2. Obtenemos la LISTA de genes desde el objeto
        mejor_genes_lista = mejor_solucion.genes

        # 3. La ganancia total es la aptitud ya calculada en el objeto
        ganancia_total = mejor_solucion.aptitud

        # 4. Calculamos el peso total usando la lista de genes
        peso_total = 0
        for i, gen in enumerate(mejor_genes_lista):
            if gen == 1:
                peso_total += pesos[i]

        # 5. Creamos la lista de items usando 'mejor_genes_lista'
        items_seleccionados = [
            {
                "indice": i,
                "id": items[i].id,
                # Aquí tenías "nombre", pero el item no tiene "nombre". 
                # Asumo que querías el nombre de la CATEGORÍA.
                "nombres_categorias": [cat.nombre for cat in items[i].categorias] if items[i].categorias else [],
                "peso": items[i].peso,
                "ganancia": items[i].ganancia,
            }
            for i, gen in enumerate(mejor_genes_lista) # <-- Usamos la lista
            if gen == 1
        ]

        # 6. Devolvemos la lista de genes y los valores correctos
        return {
            "envio_id": envio.id,
            "destino": envio.destino,
            "mejor_genes": mejor_genes_lista, # <-- Devolvemos la lista
            "ganancia_total": ganancia_total,
            "peso_total": peso_total,
            "items_seleccionados": items_seleccionados,
        }