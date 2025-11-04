from fastapi import APIRouter, HTTPException, status
from Servicios.base_Datos import SessionDep
from Modelos.modelos import Categoria
from Esquemas.esquemas import CategoriaCreate, CategoriaOut, CategoriaUpdate
from typing import List

router = APIRouter(prefix="/categorias", tags=["Categorías"])

#Define el endpoint POST para crear una nueva categoria.
@router.post("/categorias/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED, tags=["Categorías"])
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
@router.get("/categorias/", response_model=List[CategoriaOut], tags=["Categorías"])
def get_all_categorias(db: SessionDep):
    """Obtiene la lista de todas las categorías."""
    #Realiza una consulta para seleccionar todas las entradas de la tabla Categoria.
    categorias = db.query(Categoria).all()
    #Devuelve la lista de categorias.
    return categorias

#Define el endpoint GET para obtener una categoria especifica por su ID.
@router.get("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
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
@router.patch("/categorias/{categoria_id}", response_model=CategoriaOut, tags=["Categorías"])
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
@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categorías"])
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