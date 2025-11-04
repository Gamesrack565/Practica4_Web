from fastapi import APIRouter, HTTPException, Query
from Servicios.base_Datos import engine
from sqlmodel import Session
from Modelos.modelos import Envio
from Servicios.algoritmo_Genetico import AlgoritmoGenetico, SeleccionRuleta, SeleccionTorneo
router = APIRouter(prefix="/optimizar", tags=["Optimización"])


#Define el endpoint POST para ejecutar el algoritmo genetico sobre un envio.
@router.post("/optimizar/{envio_id}")
def optimizar_envio(
    envio_id: int,
    capacidad: float = Query(..., descripcion="Capacidad máxima del envio"),
    generaciones: int = Query(30, ge=1, descripcion="Número de generaciones"),
    poblacion: int = Query(10, ge=1, descripcion="Tamaño de la población"),
    prob_mutacion: float = Query(0.05, ge=0, le=1, descripcion="Probabilidad de mutacion"),
    metodo: str = Query("ruleta", pattern="^(ruleta|torneo)$", descripcion="Método de seleccion")
):
    #Maneja la sesion de BD manualmente para esta operacion.
    with Session(engine) as session:
        #Obtiene el envio por su ID usando la sesion.
        envio = session.get(Envio, envio_id)
        #Si no se encuentra el envio, lanza un error 404.
        if not envio:
            raise HTTPException(status_code=404, detail="Envio no encontrado")

        #Obtiene la lista de items directamente desde la relacion del envio.
        items = envio.items
        #Si el envio no tiene items, lanza un error 400.
        if not items:
            raise HTTPException(status_code=400, detail="Este envio no tiene items")

        #Prepara la lista de pesos para el algoritmo genetico.
        pesos = [i.peso for i in items]
        #Prepara la lista de ganancias para el algoritmo genetico.
        ganancias = [i.ganancia for i in items]

         # Selección según parámetro recibido
        if metodo == "ruleta":
            seleccion = SeleccionRuleta()
        else:
            seleccion = SeleccionTorneo()

        #Crea una instancia del AlgoritmoGenetico con los datos y el metodo de seleccion.
        ag = AlgoritmoGenetico(pesos, ganancias, capacidad, seleccion, generaciones=generaciones, num_individuos=poblacion, prob_mutacion=prob_mutacion)
        
        #Ejecuta el algoritmo, que devuelve el mejor 'Sujeto' (la mejor solucion).
        mejor_solucion = ag.ejecutar()

        #Obtiene la lista de genes (ej. [1, 0, 1]) del mejor sujeto.
        mejor_genes_lista = mejor_solucion.genes

        #Obtiene la ganancia total, que es la aptitud (fitness) del mejor sujeto.
        ganancia_total = mejor_solucion.aptitud

        #Calcula el peso total de la solucion seleccionada.
        peso_total = sum(pesos[i] for i, gen in enumerate(mejor_genes_lista) if gen == 1)

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
    
