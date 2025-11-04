from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from Esquemas.esquemas import CategoriaBase, ItemBase, EnvioBase

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

#Define el modelo de la tabla 'categoria' en la BD, heredando de CategoriaBase.
class Categoria(CategoriaBase, table=True):
    #Define la clave primaria 'id' como un entero opcional autogenerado.
    id: Optional[int] = Field(default=None, primary_key=True)
    
    #Define la relacion muchos-a-muchos con 'Item', usando 'ItemCategoria' como tabla de enlace.
    items: List["Item"] = Relationship(back_populates="categorias", link_model=ItemCategoria)


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
