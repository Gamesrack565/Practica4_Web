from fastapi import APIRouter, HTTPException, status
from Servicios.base_Datos import SessionDep
from Modelos.modelos import Item, Categoria, Envio
from Esquemas.esquemas import ItemCreate, ItemOut, ItemUpdate
from typing import List

router = APIRouter(prefix="/items", tags=["Items"])


#Define el endpoint POST para crear un nuevo item.
@router.post("/items/", response_model=ItemOut, status_code=status.HTTP_201_CREATED, tags=["Items"])
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
@router.get("/items/", response_model=List[ItemOut], tags=["Items"])
def get_all_items(db: SessionDep):
    """Obtiene todos los items y la información de sus categorías."""
    #Realiza una consulta para obtener todos los items.
    #SQLModel se encarga de cargar las relaciones (categorias) necesarias para el 'ItemOut'.
    items=db.query(Item).all()
    #Devuelve la lista de items.
    return items

#Define el endpoint GET para obtener un item especifico por su ID.
@router.get("/items/{item_id}", response_model=ItemOut, tags=["Items"])
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
@router.patch("/items/{item_id}", response_model=ItemOut, tags=["Items"])
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
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
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