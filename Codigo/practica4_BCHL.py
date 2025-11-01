#Práctica 4: Relaciones con base de datos
#Equipo:
#Beltrán Saucedo Axel Alejandro
#Cerón Samperio Lizeth Montserrat
#Higuera Pineda Angel Abraham
#Lorenzo Silva Abad Rey


#--- Modulos ---
from fastapi import FastAPI, HTTPException, status, Depends
from sqlmodel import Field, create_engine, Session, SQLModel, Relationship
from typing import Optional, List
from typing_extensions import Annotated
#Importa las clases del algoritmo genetico que esta en otro achivo.
from .Algoritmo_genetico import AlgoritmoGenetico, SeleccionRuleta

#--- Base de Datos ---
sql_url="sqlite:///database.db"
engine=create_engine(sql_url)

#Define una funcion para crear la base de datos y las tablas.
def create_db_and_tables():
    #Ordena a SQLModel que cree todas las tablas que heredan de 'SQLModel' (con table=True).
    SQLModel.metadata.create_all(engine)

#--- Modelos de Datos ---

#Define el modelo Pydantic/SQLModel base para una Categoria.
class CategoriaBase(SQLModel):
    #Define el campo 'nombre' como un string, indexado en la BD y unico.
    nombre: str = Field(index=True, description="Nombre de la categoría (ej. Frágil, Peligroso)", unique=True)
    #Define un campo opcional 'descripcion' con un valor por defecto Nulo.
    descripcion: Optional[str] = Field(default=None, description="Materiales o descripción de la categoría")

#Define el modelo Pydantic/SQLModel base para un Item.
class ItemBase(SQLModel):
    #Define el campo 'ganancia' como un numero de punto flotante.
    ganancia: float
    #Define el campo 'peso' como un numero de punto flotante.
    peso: float

#Define el modelo Pydantic/SQLModel base para un Envio.
class EnvioBase(SQLModel):
    #Define el campo 'destino' como un string.
    destino: str

#Define la tabla de enlace (asociativa) para la relacion Item <-> Categoria.
class ItemCategoria(SQLModel, table=True):
    #Define el campo 'item_id' como clave foranea a 'item.id' y parte de la clave primaria.
    item_id: Optional[int] = Field(
        default=None, foreign_key="item.id", primary_key=True
    )
    #Define el campo 'categoria_id' como clave foranea a 'categoria.id' y parte de la clave primaria.
    categoria_id: Optional[int] = Field(
        default=None, foreign_key="categoria.id", primary_key=True
    )

#Define el modelo de la tabla 'categoria' en la BD, heredando de CategoriaBase.
class Categoria(CategoriaBase, table=True):
    #Define la clave primaria 'id' como un entero opcional autogenerado.
    id: Optional[int] = Field(default=None, primary_key=True)
    
    #Define la relacion muchos-a-muchos con 'Item', usando 'ItemCategoria' como tabla de enlace.
    items: List["Item"] = Relationship(back_populates="categorias", link_model=ItemCategoria)

#Define la tabla de enlace (asociativa) para la relacion Item <-> Envio.
class ItemEnvio(SQLModel, table=True):
    #Define el campo 'item_id' como clave foranea a 'item.id' y parte de la clave primaria.
    item_id: Optional[int] = Field(
        default=None, foreign_key="item.id", primary_key=True
    )
    #Define el campo 'envio_id' como clave foranea a 'envio.id' y parte de la clave primaria.
    envio_id: Optional[int] = Field(
        default=None, foreign_key="envio.id", primary_key=True
    )

#Define el modelo de la tabla 'item' en la BD, heredando de ItemBase.
class Item(ItemBase, table=True):
    #Define la clave primaria 'id'.
    id: Optional[int] = Field(default=None, primary_key=True)
    
    #Define la relacion muchos-a-muchos con 'Categoria', vinculada por 'ItemCategoria'.
    categorias: List[Categoria] = Relationship(back_populates="items", link_model=ItemCategoria)
    
    #Define la relacion muchos-a-muchos con 'Envio', vinculada por 'ItemEnvio'.
    envios: List["Envio"] = Relationship(back_populates="items", link_model=ItemEnvio)

#Define el modelo de la tabla 'envio' en la BD, heredando de EnvioBase.
class Envio(EnvioBase, table=True):
    #Define la clave primaria 'id'.
    id: Optional[int] = Field(default=None, primary_key=True)
    
    #Define la relacion muchos-a-muchos con 'Item', vinculada por 'ItemEnvio'.
    items: List[Item] = Relationship(back_populates="envios", link_model=ItemEnvio)

#Define el modelo de datos esperado para CREAR una Categoria (entrada POST).
class CategoriaCreate(CategoriaBase):
    #No necesita campos adicionales, hereda 'nombre' y 'descripcion' de CategoriaBase.
    pass

#Define el modelo de datos esperado para CREAR un Item (entrada POST).
class ItemCreate(ItemBase):
    #Espera una lista de nombres de categorias a las que se asociara el item.
    categoria_nombres: List[str] = Field(default=[], description="Lista de nombres de categorías a las que pertenece el item.")

#Define el modelo de datos esperado para CREAR un Envio (entrada POST).
class EnvioCreate(EnvioBase):
    #Espera una lista de IDs de items que se incluiran en el envio.
    item_ids: List[int] = []

#Define el modelo de datos de RESPUESTA para una Categoria (salida GET).
class CategoriaOut(CategoriaBase):
    #Incluye el 'id' en la respuesta.
    id: int

#Define el modelo de datos de RESPUESTA para un Item (salida GET).
class ItemOut(ItemBase):
    #Incluye el 'id' en la respuesta.
    id: int
    #Incluye una lista de las categorias asociadas, usando el modelo CategoriaOut.
    categorias: List[CategoriaOut] = []

#Define el modelo de datos de RESPUESTA para un Envio (salida GET).
class EnvioOut(EnvioBase):
    #Incluye el 'id' en la respuesta.
    id: int
    #Incluye una lista de los items asociados, usando el modelo ItemOut.
    items: List[ItemOut] = []

#Define el modelo de datos para ACTUALIZAR una Categoria (entrada PATCH).
class CategoriaUpdate(SQLModel):
    #Todos los campos son opcionales para permitir actualizaciones parciales.
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

#Define el modelo de datos para ACTUALIZAR un Item (entrada PATCH).
class ItemUpdate(SQLModel):
    #Define 'peso' como opcional.
    peso: Optional[float] = None
    #Define 'ganancia' como opcional.
    ganancia: Optional[float] = None
    #Permite reemplazar la lista de categorias usando sus nombres.
    categoria_nombres: Optional[List[str]] = Field(default=None, description="Lista de nombres para reemplazar las categorías del item.")

#Define el modelo de datos para ACTUALIZAR un Envio (entrada PATCH).
class EnvioUpdate(SQLModel):
    #Define 'destino' como opcional.
    destino: Optional[str] = None
    #Permite reemplazar la lista de items usando sus IDs.
    item_ids: Optional[List[int]] = None

#--- Aplicacion FastAPI ---

#Define un generador para gestionar las sesiones de la base de datos.
def get_session():
    #Crea una nueva sesion usando el motor.
    with Session(engine) as session:
        #Proporciona la sesion a la funcion del endpoint.
        yield session
        #El bloque 'with' asegura que la sesion se cierre automaticamente.

#Crea un alias 'SessionDep' para la inyeccion de dependencias de la sesion.
SessionDep=Annotated[Session, Depends(get_session)] 

#Crea la instancia principal de la aplicacion FastAPI.
app = FastAPI(
    #Establece el titulo de la documentacion de la API.
    title= "Practica 4: Relaciones de Datos con una Base de Datos",
    #Establece la descripcion de la documentacion.
    description= "API para gestionar Items, Categorías editables y Envíos, con persistencia de datos."
)

#Define una funcion que se ejecutara cuando la aplicacion inicie.
@app.on_event("startup")
def on_startup():
    #Llama a la funcion para crear las tablas de la BD.
    create_db_and_tables()

#Define el endpoint POST para crear una nueva categoria.
@app.post("/categorias/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED, tags=["Categorías"])
#Define la funcion que maneja el endpoint, recibiendo los datos (categoria) y la sesion (db).
def create_categoria(categoria: CategoriaCreate, db: SessionDep):
    """Crea una nueva categoría (Frágil, Peligroso, etc.)."""
    
    #Busca en la BD si ya existe una categoria con el mismo nombre.
    db_categoria_existente = db.query(Categoria).filter(Categoria.nombre == categoria.nombre).first()
    #Si existe, lanza un error HTTP 400 (Solicitud Incorrecta).
    if db_categoria_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de la categoría ya existe")
        
    #Convierte el modelo de entrada (CategoriaCreate) al modelo de tabla (Categoria).
    db_categoria = Categoria.model_validate(categoria)
    #Anade el nuevo objeto a la sesion de la BD.
    db.add(db_categoria)
    #Confirma (guarda) los cambios en la BD.
    db.commit()
    #Refresca el objeto para obtener el ID asignado por la BD.
    db.refresh(db_categoria)
    #Devuelve el objeto de la categoria recien creada.
    return db_categoria

#Define el endpoint GET para obtener una lista de todas las categorias.
@app.get("/categorias/", response_model=List[CategoriaOut], tags=["Categorías"])
def get_all_categorias(db: SessionDep):
    """Obtiene la lista de todas las categorías."""
    #Realiza una consulta para seleccionar todas las entradas de la tabla Categoria.
    categorias = db.query(Categoria).all()
    #Devuelve la lista de categorias.
    return categorias

#Define el endpoint GET para obtener una categoria especifica por su ID.
@app.get("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
def get_categoria_by_id(categoria_id: int, db: SessionDep):
    """Obtiene una categoría específica por su ID."""
    #Busca la categoria por su clave primaria (ID).
    categoria = db.get(Categoria, categoria_id)
    #Si no se encuentra la categoria, lanza un error HTTP 404 (No Encontrado).
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    #Devuelve la categoria encontrada.
    return categoria

#Define el endpoint PATCH para actualizar parcialmente una categoria.
@app.patch("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
def update_categoria(categoria_id: int, categoria_data: CategoriaUpdate, db: SessionDep):
    """Actualiza el nombre o descripción de una categoría."""
    #Obtiene la categoria de la BD que se va a actualizar.
    db_categoria = db.get(Categoria, categoria_id)
    #Si no existe, lanza un error 404.
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    
    #Convierte los datos de actualizacion a un diccionario, excluyendo los campos no enviados.
    update_data = categoria_data.model_dump(exclude_unset=True)
    
    #Verifica si el campo 'nombre' esta siendo actualizado.
    if "nombre" in update_data:
        #Si es asi, obtiene el nuevo nombre.
        nombre_nuevo = update_data["nombre"]
        #Busca si ya existe otra categoria con ese nuevo nombre.
        db_categoria_existente = db.query(Categoria).filter(Categoria.nombre == nombre_nuevo).first()
        #Si existe y no es la misma categoria que estamos actualizando, lanza un error 400.
        if db_categoria_existente and db_categoria_existente.id != categoria_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de la categoría ya existe")

    #Itera sobre los datos de actualizacion y los aplica al objeto de la BD.
    for key, value in update_data.items():
        setattr(db_categoria, key, value)
    
    #Anade el objeto modificado a la sesion.
    db.add(db_categoria)
    #Guarda los cambios.
    db.commit()
    #Refresca el objeto desde la BD.
    db.refresh(db_categoria)
    #Devuelve la categoria actualizada.
    return db_categoria

#Define el endpoint DELETE para eliminar una categoria.
@app.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categorías"])
def delete_categoria(categoria_id: int, db: SessionDep):
    """Elimina una categoría. Falla si hay items usándola."""
    #Busca la categoria que se va a eliminar.
    db_categoria = db.get(Categoria, categoria_id)
    #Si no existe, lanza un error 404.
    if not db_categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    
    #Verifica si la categoria tiene items asociados (si la lista 'items' no esta vacia).
    if db_categoria.items:
        #Si tiene items, no permite borrarla y lanza un error 400.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede eliminar la categoría, tiene items asociados.")
        
    #Marca la categoria para ser eliminada de la BD.
    db.delete(db_categoria)
    #Ejecuta la eliminacion.
    db.commit()
    #Devuelve una respuesta sin contenido (status 204).
    return

#Define el endpoint POST para crear un nuevo item.
@app.post("/items/", response_model=ItemOut, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item_data: ItemCreate, db: SessionDep):
    """Crea un nuevo item, asignándolo a una o más categorías existentes por nombre."""
    
    #Crea una lista vacia para almacenar los objetos Categoria encontrados.
    categorias = []
    #Si el cliente envio nombres de categorias en la solicitud.
    if item_data.categoria_nombres:
        #Busca en la BD los objetos Categoria que coincidan con los nombres de la lista.
        categorias = db.query(Categoria).filter(Categoria.nombre.in_(item_data.categoria_nombres)).all()
        
        #Valida si se encontraron todas las categorias solicitadas.
        if len(categorias) != len(set(item_data.categoria_nombres)):
            #Si no se encontraron, lanza un error 404.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Una o más categorías no fueron encontradas")
    
    #Crea un diccionario con los datos base del item (excluyendo la lista de nombres).
    item_dict = item_data.model_dump(exclude={"categoria_nombres"})
    #Crea la instancia del modelo Item usando los datos del diccionario.
    new_item = Item(**item_dict)
    
    #Asigna la lista de objetos Categoria a la relacion del nuevo item.
    #SQLModel gestionara la creacion de las entradas en la tabla 'ItemCategoria'.
    new_item.categorias = categorias
    
    #Guarda el nuevo item en la BD.
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    #Devuelve el item recien creado.
    return new_item

#Define el endpoint GET para obtener una lista de todos los items.
@app.get("/items/", response_model=List[ItemOut], tags=["Items"])
def get_all_items(db: SessionDep):
    """Obtiene todos los items y la información de sus categorías."""
    #Realiza una consulta para obtener todos los items.
    #SQLModel se encarga de cargar las relaciones (categorias) necesarias para el 'ItemOut'.
    items=db.query(Item).all()
    #Devuelve la lista de items.
    return items

#Define el endpoint GET para obtener un item especifico por su ID.
@app.get("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def get_item_by_id(item_id: int, db: SessionDep):
    """Obtiene un item por su ID y la información de sus categorías."""
    #Busca el item en la BD por su clave primaria.
    item=db.get(Item, item_id)
    #Si no se encuentra el item, lanza un error 404.
    if not item :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    #Devuelve el item encontrado.
    return item

#Define el endpoint PATCH para actualizar parcialmente un item.
@app.patch("/items/{item_id}", response_model=ItemOut, tags=["Items"])
def update_item_partially(item_id: int, item_update: ItemUpdate, db: SessionDep):
    """Actualiza parcialmente un item (peso, ganancia o lista de categorías por nombre)."""
    #Busca el item en la BD que se va a actualizar.
    db_item=db.get(Item, item_id)
    #Si no se encuentra, lanza un error 404.
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")

    #Convierte los datos de actualizacion (solo los enviados) en un diccionario.
    update_data=item_update.model_dump(exclude_unset=True)
    
    #Verifica si el campo 'categoria_nombres' fue incluido en la actualizacion.
    if "categoria_nombres" in update_data:
        #Extrae la lista de nombres del diccionario (puede ser None, [], o una lista).
        nombres = update_data.pop("categoria_nombres") 
        
        #Prepara una lista vacia para los nuevos objetos Categoria.
        categorias = []
        #Si la lista 'nombres' no es Nula (si es [] significa "quitar todas").
        if nombres is not None: 
            #Busca los objetos Categoria que coincidan con los nombres.
            categorias = db.query(Categoria).filter(Categoria.nombre.in_(nombres)).all()
            #Valida si se encontraron todas las categorias solicitadas.
            if len(categorias) != len(set(nombres)):
                #Si no se encontraron, lanza un error 404.
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Una o más categorías no fueron encontradas para actualizar")
        
        #Reemplaza la lista de categorias del item con la nueva lista encontrada.
        #SQLModel actualizara la tabla 'ItemCategoria'.
        db_item.categorias = categorias

    #Actualiza los atributos restantes (peso, ganancia) en el objeto.
    for key, value in update_data.items():
        setattr(db_item, key, value)

    #Guarda los cambios en la sesion y en la BD.
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    #Devuelve el item actualizado.
    return db_item

#Define el endpoint DELETE para eliminar un item.
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int, db: SessionDep):
    """Elimina un item (esto lo quitará también de cualquier envío y categoría)."""
    #Busca el item que se va a eliminar.
    item_to_delete = db.get(Item, item_id)
    #Si no se encuentra, lanza un error 404.
    if not item_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    
    #SQLModel elimina automaticamente las referencias en las tablas de enlace ('ItemEnvio', 'ItemCategoria').
    db.delete(item_to_delete)
    #Confirma la eliminacion en la BD.
    db.commit()
    #No devuelve contenido (status 204).
    return

#Define el endpoint POST para crear un nuevo envio.
@app.post("/envios/", response_model=EnvioOut, status_code=status.HTTP_201_CREATED, tags=["Envíos"])
def create_envio(envio_data: EnvioCreate, db: SessionDep):
    """Crea un nuevo envío, asociando una lista de IDs de items existentes."""
    #Prepara una lista vacia para los objetos Item.
    items = []
    #Si se proporcionaron IDs de items en la solicitud.
    if envio_data.item_ids:
        #Busca en la BD los objetos Item que coincidan con los IDs de la lista.
        items = db.query(Item).filter(Item.id.in_(envio_data.item_ids)).all()
        #Valida si se encontraron todos los items solicitados.
        if len(items) != len(set(envio_data.item_ids)):
            #Si algun ID no se encontro, lanza un error 404.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más IDs de items no fueron encontrados")

    #Crea la instancia del Envio solo con el destino.
    db_envio = Envio(destino=envio_data.destino)
    #Asigna la lista de objetos Item encontrados a la relacion 'items' del envio.
    #SQLModel gestionara la tabla de enlace 'ItemEnvio'.
    db_envio.items = items
    
    #Guarda el nuevo envio y sus relaciones en la BD.
    db.add(db_envio)
    db.commit()
    db.refresh(db_envio)
    #Devuelve el envio recien creado (con su lista de items).
    return db_envio

#Define el endpoint GET para obtener una lista de todos los envios.
@app.get("/envios/", response_model=List[EnvioOut], tags=["Envíos"])
def get_all_envios(db: SessionDep):
    """Obtiene todos los envíos, incluyendo los items que contiene cada uno."""
    #Realiza una consulta para obtener todos los envios.
    #SQLModel carga automaticamente la lista 'items' para el 'EnvioOut'.
    envios = db.query(Envio).all()
    #Devuelve la lista de envios.
    return envios

#Define el endpoint GET para obtener un envio especifico por su ID.
@app.get("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
def get_envio_by_id(envio_id: int, db: SessionDep):
    """Obtiene un envío específico por ID, incluyendo sus items."""
    #Busca el envio en la BD por su clave primaria.
    envio = db.get(Envio, envio_id)
    #Si no se encuentra, lanza un error 404.
    if not envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")
    #Devuelve el envio encontrado.
    return envio

#Define el endpoint PATCH para actualizar parcialmente un envio.
@app.patch("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
def update_envio(envio_id: int, envio_data: EnvioUpdate, db: SessionDep):
    """Actualiza un envío (destino y/o la lista completa de items que contiene)."""
    #Busca el envio en la BD que se va a actualizar.
    db_envio = db.get(Envio, envio_id)
    #Si no se encuentra, lanza un error 404.
    if not db_envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")

    #Convierte los datos de actualizacion (solo los enviados) en un diccionario.
    update_data = envio_data.model_dump(exclude_unset=True)

    #Verifica si el campo 'item_ids' fue incluido en la actualizacion.
    if "item_ids" in update_data:
        #Extrae la lista de IDs del diccionario.
        item_ids = update_data.pop("item_ids") 
        
        #Prepara una lista vacia para los nuevos objetos Item.
        items = []
        #Si la lista 'item_ids' no es Nula (si es [] significa "quitar todos").
        if item_ids is not None: 
            #Busca los objetos Item que coincidan con los IDs.
            items = db.query(Item).filter(Item.id.in_(item_ids)).all()
            #Valida si se encontraron todos los items solicitados.
            if len(items) != len(set(item_ids)):
                #Si no se encontraron, lanza un error 404.
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más IDs de items no fueron encontrados para actualizar")
        
        #Reemplaza la lista de items del envio con la nueva lista encontrada.
        #SQLModel actualizara la tabla 'ItemEnvio'.
        db_envio.items = items

    #Actualiza los atributos restantes (solo 'destino') en el objeto.
    for key, value in update_data.items():
        setattr(db_envio, key, value)
        
    #Guarda los cambios en la sesion y en la BD.
    db.add(db_envio)
    db.commit()
    db.refresh(db_envio)
    #Devuelve el envio actualizado.
    return db_envio

#Define el endpoint DELETE para eliminar un envio.
@app.delete("/envios/{envio_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Envíos"])
def delete_envio(envio_id: int, db: SessionDep):
    """Elimina un envío (esto NO elimina los items, solo la asociación en la tabla de enlace)."""
    #Busca el envio que se va a eliminar.
    db_envio = db.get(Envio, envio_id)
    #Si no se encuentra, lanza un error 404.
    if not db_envio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Envío no encontrado")
        
    #Al borrar el Envio, SQLModel elimina automaticamente las filas en 'ItemEnvio'.
    db.delete(db_envio)
    #Confirma la eliminacion.
    db.commit()
    #No devuelve contenido (status 204).
    return

#--- Algoritmo Genético para Optimización de Envíos ---

#Define el endpoint POST para ejecutar el algoritmo genetico sobre un envio.
@app.post("/optimizar/{envio_id}", tags=["Algoritmo Genético"])
def optimizar_envio(envio_id: int, capacidad: float):
    #Maneja la sesion de BD manualmente para esta operacion.
    with Session(engine) as session:
        #Obtiene el envio por su ID usando la sesion.
        envio = session.get(Envio, envio_id)
        #Si no se encuentra el envio, lanza un error 404.
        if not envio:
            raise HTTPException(status_code=404, detail="Envío no encontrado")

        #Obtiene la lista de items directamente desde la relacion del envio.
        items = envio.items
        #Si el envio no tiene items, lanza un error 400.
        if not items:
            raise HTTPException(status_code=400, detail="Este envío no tiene items")

        #Prepara la lista de pesos para el algoritmo genetico.
        pesos = [i.peso for i in items]
        #Prepara la lista de ganancias para el algoritmo genetico.
        ganancias = [i.ganancia for i in items]

        #Crea una instancia del AlgoritmoGenetico con los datos y el metodo de seleccion.
        ag = AlgoritmoGenetico(pesos, ganancias, capacidad, SeleccionRuleta())
        
        #Ejecuta el algoritmo, que devuelve el mejor 'Sujeto' (la mejor solucion).
        mejor_solucion = ag.ejecutar()

        #Obtiene la lista de genes (ej. [1, 0, 1]) del mejor sujeto.
        mejor_genes_lista = mejor_solucion.genes

        #Obtiene la ganancia total, que es la aptitud (fitness) del mejor sujeto.
        ganancia_total = mejor_solucion.aptitud

        #Calcula el peso total de la solucion seleccionada.
        peso_total = 0
        #Itera sobre la lista de genes.
        for i, gen in enumerate(mejor_genes_lista):
            #Si el gen es 1, significa que el item fue seleccionado.
            if gen == 1:
                #Suma el peso del item correspondiente al peso total.
                peso_total += pesos[i]

        #Construye la lista de los items que fueron seleccionados por el algoritmo.
        items_seleccionados = [
            #Crea un diccionario por cada item seleccionado.
            {
                "indice": i,
                "id": items[i].id,
                #Obtiene los nombres de las categorias del item.
                "nombres_categorias": [cat.nombre for cat in items[i].categorias] if items[i].categorias else [],
                "peso": items[i].peso,
                "ganancia": items[i].ganancia,
            }
            #Itera sobre la lista de genes.
            for i, gen in enumerate(mejor_genes_lista)
            #Incluye el item solo si el gen es 1.
            if gen == 1
        ]

        #Devuelve la respuesta final en formato JSON.
        return {
            "envio_id": envio.id,
            "destino": envio.destino,
            "mejor_genes": mejor_genes_lista,
            "ganancia_total": ganancia_total,
            "peso_total": peso_total,
            "items_seleccionados": items_seleccionados,
        }
    
