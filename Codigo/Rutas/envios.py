from fastapi import APIRouter, HTTPException, status
from Servicios.base_Datos import SessionDep
from Modelos.modelos import Envio, Item, Categoria
from Esquemas.esquemas import EnvioCreate, EnvioOut, EnvioUpdate
from typing import List
router = APIRouter(prefix="/envios", tags=["Envíos"])



#Define el endpoint POST para crear un nuevo envio.
@router.post("/envios/", response_model=EnvioOut, status_code=status.HTTP_201_CREATED, tags=["Envíos"])
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
@router.get("/envios/", response_model=List[EnvioOut], tags=["Envíos"])
def get_all_envios(db: SessionDep):
    """Obtiene todos los envíos, incluyendo los items que contiene cada uno."""
    #Realiza una consulta para obtener todos los envios.
    #SQLModel carga automaticamente la lista 'items' para el 'EnvioOut'.
    envios = db.query(Envio).all()
    #Devuelve la lista de envios.
    return envios

#Define el endpoint GET para obtener un envio especifico por su ID.
@router.get("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
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
@router.patch("/envios/{envio_id}", response_model=EnvioOut, tags=["Envíos"])
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
@router.delete("/envios/{envio_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Envíos"])
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