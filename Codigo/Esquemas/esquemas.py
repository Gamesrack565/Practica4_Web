from typing import List, Optional
from sqlmodel import SQLModel, Field


#Define el modelo Pydantic/SQLModel base para una Categoria.
class CategoriaBase(SQLModel):
    #Define el campo 'nombre' como un string, indexado en la BD y unico.
    nombre: str = Field(index=True, description="Nombre de la categoría (ej. Frágil, Peligroso)", unique=True)
    #Define un campo opcional 'descripcion' con un valor por defecto Nulo.
    descripcion: Optional[str] = Field(default=None, description="Materiales o descripción de la categoría")

#Define el modelo de datos esperado para CREAR una Categoria (entrada POST).
class CategoriaCreate(CategoriaBase):
    #No necesita campos adicionales, hereda 'nombre' y 'descripcion' de CategoriaBase.
    pass

#Define el modelo de datos de RESPUESTA para una Categoria (salida GET).
class CategoriaOut(CategoriaBase):
    #Incluye el 'id' en la respuesta.
    id: int

class CategoriaUpdate(SQLModel):
    #Todos los campos son opcionales para permitir actualizaciones parciales.
    nombre: Optional[str] = None
    descripcion: Optional[str] = None



#Define el modelo Pydantic/SQLModel base para un Item.
class ItemBase(SQLModel):
    #Define el campo 'ganancia' como un numero de punto flotante.
    ganancia: float
    #Define el campo 'peso' como un numero de punto flotante.
    peso: float

#Define el modelo de datos esperado para CREAR un Item (entrada POST).
class ItemCreate(ItemBase):
    #Espera una lista de nombres de categorias a las que se asociara el item.
    categoria_nombres: List[str] = Field(default=[], description="Lista de nombres de categorías a las que pertenece el item.")

#Define el modelo de datos de RESPUESTA para un Item (salida GET).
class ItemOut(ItemBase):
    #Incluye el 'id' en la respuesta.
    id: int
    #Incluye una lista de las categorias asociadas, usando el modelo CategoriaOut.
    categorias: List[CategoriaOut] = []

#Define el modelo de datos para ACTUALIZAR un Item (entrada PATCH).
class ItemUpdate(SQLModel):
    #Define 'peso' como opcional.
    peso: Optional[float] = None
    #Define 'ganancia' como opcional.
    ganancia: Optional[float] = None
    #Permite reemplazar la lista de categorias usando sus nombres.
    categoria_nombres: Optional[List[str]] = Field(default=None, description="Lista de nombres para reemplazar las categorías del item.")



#Define el modelo Pydantic/SQLModel base para un Envio.
class EnvioBase(SQLModel):
    #Define el campo 'destino' como un string.
    destino: str

#Define el modelo de datos esperado para CREAR un Envio (entrada POST).
class EnvioCreate(EnvioBase):
    #Espera una lista de IDs de items que se incluiran en el envio.
    item_ids: List[int] = []

#Define el modelo de datos de RESPUESTA para un Envio (salida GET).
class EnvioOut(EnvioBase):
    #Incluye el 'id' en la respuesta.
    id: int
    #Incluye una lista de los items asociados, usando el modelo ItemOut.
    items: List[ItemOut] = []

#Define el modelo de datos para ACTUALIZAR un Envio (entrada PATCH).
class EnvioUpdate(SQLModel):
    #Define 'destino' como opcional.
    destino: Optional[str] = None
    #Permite reemplazar la lista de items usando sus IDs.
    item_ids: Optional[List[int]] = None