#Practica 1: Algoritmo genetico
#Beltran Saucedo Axel Alejandro
#Ceron Samperio Lizeth Montserrat
#Higuera Pineda Angel Abraham
#Lorenzo Silva Abad Rey

#Librerias a utilizar 
#Random sirve para utilizar funciones aleatorias
import random
#Nos permite crear interfaces en Python
from abc import ABC, abstractmethod

#Interface utilizada para el cambio de metodo de seleccion
class MetodoSeleccion(ABC):
    @abstractmethod
    def seleccionar(self, poblacion):
        pass

#Seleccion por ruleta
class SeleccionRuleta(MetodoSeleccion):
    def seleccionar(self, poblacion):
        #Calcula la suma total de las aptitudes de la poblacion
        #Si todo el mundo tiene 0, elige uno al azar 
        total_aptitud = sum(ind.aptitud for ind in poblacion.sujetos)
        if total_aptitud == 0:
            return random.choice(poblacion.sujetos)
        #Es momento de girar la ruleta
        punto = random.uniform(0, total_aptitud)
        acumulado = 0
        for ind in poblacion.sujetos:
            acumulado += ind.aptitud
            if acumulado >= punto:
                return ind

#Seleccion por torneo
#Torneo es el metodo de seleccion más rapido de hacer, se recomienda utilizar el metodo de ruleta
class SeleccionTorneo(MetodoSeleccion):
    def __init__(self, k=3):
        #En caso de generar un error la seleccion, se pasara a utilizar ruleta
        self.k = k
        self.fallback = SeleccionRuleta()  #Ruleta como respaldo

    def seleccionar(self, poblacion):
        #Elige k indivudos al azar y se queda con el mejor
        participantes = random.sample(poblacion.sujetos, min(self.k, len(poblacion.sujetos)))
        if all(ind.aptitud == 0 for ind in participantes):
            #Si todos son inválidos, usamos ruleta
            return self.fallback.seleccionar(poblacion)
        return max(participantes, key=lambda ind: ind.aptitud)

#Clase sujeto
#Son las posibles soluciones al problema de la mochila
class Sujetos:
    def __init__(self, num_objetos):
        #Lista de 0 y 1 
        self.genes = [random.randint(0, 1) for _ in range(num_objetos)]
        #Valor total de la combinacion
        self.aptitud = 0

    #Recorre los genes, si un gen vale 1, sumamos el peso y su valor
    def calcular_aptitud(self, pesos, valores, capacidad):
        peso_total = 0
        valor_total = 0
        for i in range(len(self.genes)):
            if self.genes[i] == 1:
                peso_total += pesos[i]
                valor_total += valores[i]
        #Si pasa la capacidad es inválido la aptitud es 0
        #Si cabe su aptitud es el valor total de los objetos dentro.
        if peso_total > capacidad:
            self.aptitud = 0
        else:
            self.aptitud = valor_total
        return self.aptitud

#Clase de la poblacion 
class Poblacion:
    def __init__(self, num_individuos, num_objetos):
        #Crea una lista con los genes aleatorios
        self.sujetos = [Sujetos(num_objetos) for _ in range(num_individuos)]
    #Evalua la aptitud de cada individuo con respecto al problema de la mochila.
    def evaluar(self, pesos, valores, capacidad):
        for ind in self.sujetos:
            ind.calcular_aptitud(pesos, valores, capacidad)

#Operaciones del algoritmo genetico 
#Se controla todo el proceso de seleccion, crice, mutuacion y generaciones
class AlgoritmoGenetico:
    def __init__(self, pesos, valores, capacidad, estrategia_seleccion,
                 num_individuos=20, generaciones=50, prob_mutacion=0.01):
        #Recibe los pesos, valores y capacidad del problema
        #Numero de generaciones y sus propbabilidades de mutar
        self.pesos = pesos
        self.valores = valores
        self.capacidad = capacidad
        self.num_objetos = len(pesos)
        self.prob_mutacion = prob_mutacion
        self.generaciones = generaciones
        self.num_individuos = num_individuos
        self.estrategia = estrategia_seleccion
        self.poblacion = Poblacion(num_individuos, self.num_objetos)
        self.poblacion.evaluar(self.pesos, self.valores, self.capacidad)

    #La funcion de cruza utiliza el metodo de cruce por un solo punto
    #No es el mejor para utilizar, ya que debemos tener cuidado de no sobrepasar el limite de la lista
    #Lo que hace es:
    #Se elige un punto de cruce al azar, y se intercambian los genes de los 2 individuos 
    def crossover(self, padre1, padre2):
        if self.num_objetos < 2:
            hijo = Sujetos(self.num_objetos)
            hijo.genes = padre1.genes.copy()
            return hijo, hijo
        #Se realiza la eleccion del punto de cruce
        punto = random.randint(1, self.num_objetos - 1)
        hijo1 = Sujetos(self.num_objetos)
        hijo2 = Sujetos(self.num_objetos)
        hijo1.genes = padre1.genes[:punto] + padre2.genes[punto:]
        hijo2.genes = padre2.genes[:punto] + padre1.genes[punto:]
        return hijo1, hijo2

    #Usamo el metodo de mutacion por inversion (flip) de bits
    #Cada gen tiene probabilidad de cambiar a 0 - 1 o 1 - 0
    def mutacion(self, individuo):
        for i in range(len(individuo.genes)):
            if random.random() < self.prob_mutacion:
                individuo.genes[i] = 1 - individuo.genes[i]

    #Podemos usar para hacer la mutacion de un hijo
    #rm = rand_uniform(0.1) o 0.08          Para saber si vas a mutar a ese hijo
    #   if rm < pm                           //Si si, lo mutamos
    #   indi = rando_int(1, tamaño_cormosoma)
    #   modificar_indice 


    def ejecutar(self):
        #Se guarda el mejor individuo encontrado en todas las generaciones
        #Se encuentra vacio al inicio
        mejor_global = None
        #Bucle de generaciones
        for gen in range(1, self.generaciones + 1):
            #Crea una nueva poblacion con los nuevos sujetos (de las generaciones)
            #Se terminara el proceso cuando se tengan el mismo numero de sujetos que la antigua poblacion
            nueva_poblacion = []
            while len(nueva_poblacion) < self.num_individuos:
                #Se seleccionan a dos padres de la poblacion actual
                padre1 = self.estrategia.seleccionar(self.poblacion)
                padre2 = self.estrategia.seleccionar(self.poblacion)
                #LOs padres se cruzan y nacen dos hijos
                hijo1, hijo2 = self.crossover(padre1, padre2)
                #Cada hijo tiene una propbailidad de cambiar sus genes
                self.mutacion(hijo1)
                self.mutacion(hijo2)
                #Guarda a los hijos en la nueva poblacion
                #Si ya se alcanzo el maximo, ya no se agrega el hijo 2 y muere
                nueva_poblacion.append(hijo1)
                if len(nueva_poblacion) < self.num_individuos:
                    nueva_poblacion.append(hijo2)
            #Se remplaza a la poblacion vieja
            self.poblacion.sujetos = nueva_poblacion
            #Se calcula la nueva aptitud de todos los individuos 
            self.poblacion.evaluar(self.pesos, self.valores, self.capacidad)
            #Guarda al mejor individuo de la poblacion
            mejor = max(self.poblacion.sujetos, key=lambda ind: ind.aptitud)
            #Verifica si el mejor resultado es remplazado por otro mejor
            #Si noe existe aun ese mejor, pues se guarda
            if mejor_global is None or mejor.aptitud > mejor_global.aptitud:
                mejor_global = mejor
            #Se imprime el mejor gen
            print(f"Generación {gen}: Mejor aptitud = {mejor.aptitud}")
        return mejor_global


#Main
if __name__ == "__main__":
    #Mensaje inicial
    print("==== Practica 1: Problema de la mochila con algoritmo genetico ====")
    print("Opciones de entrada de datos:")
    print("1) Ingresar datos manualmente")
    print("2) Usar datos de ejemplo")

    opcion_datos = input("Elige una opcion: ").strip()
    #Si se selecciona la entra manual, preguntara cuntos objetos seran y la capacidad maxima
    if opcion_datos == "1":
        num_objetos = int(input("Numero de objetos: "))
        pesos = []
        valores = []
        #Para almacenar esos bojetos usamos un for
        for i in range(num_objetos):
            peso = int(input(f"Objeto {i+1}: Peso = "))
            valor = int(input(f"Objeto {i+1}: Valor = "))
            pesos.append(peso)
            valores.append(valor)
        capacidad = int(input("Capacidad de la mochila: "))
    else:
        #Si se lecciona datos de ejemplo, se trabajaran con los siguientes
        pesos = [2, 3, 4, 5]
        valores = [3, 4, 5, 8]
        capacidad = 8
        num_objetos = len(pesos)

        #Mostrar los objetos en pantalla
        print("\n=== Datos de ejemplo ===")
        for i in range(num_objetos):
            print(f"Objeto {i+1}: Peso = {pesos[i]}, Valor = {valores[i]}")
        print(f"Capacidad de la mochila = {capacidad}\n")

    #Iniciamos trabajando con torneo
    #Compara 3 individuos cada vez
    print("Analisis por torneo (despues se hara por ruleta):")
    estrategia_torneo = SeleccionTorneo(k=3)
    #Indica cuentos son los candidatos y cuantas veces se repetira para las generaciones 
    #Ademas se indica cuanta es la probabilidad de mutar (se recomienda que sea entre 0 y 1)
    ag_torneo = AlgoritmoGenetico(pesos, valores, capacidad, estrategia_torneo,
                                  num_individuos=10, generaciones=30, prob_mutacion=0.5)
    mejor_torneo = ag_torneo.ejecutar()

    #Segundo analisis con ruleta
    print("\nAnalisis por Ruleta:")
    estrategia_ruleta = SeleccionRuleta()
    #Indica cuentos son los candidatos y cuantas veces se repetira para las generaciones 
    #Ademas se indica cuanta es la probabilidad de mutar (se recomienda que sea entre 0 y 1)
    ag_ruleta = AlgoritmoGenetico(pesos, valores, capacidad, estrategia_ruleta,
                                  num_individuos=10, generaciones=30, prob_mutacion=0)
    mejor_ruleta = ag_ruleta.ejecutar()

    #Comparamos resultados
    print("\n=== Resultados finales ===")
    print("Mejor con Torneo:", mejor_torneo.genes, "Aptitud:", mejor_torneo.aptitud)
    print("Mejor con Ruleta:", mejor_ruleta.genes, "Aptitud:", mejor_ruleta.aptitud)

    if mejor_torneo.aptitud >= mejor_ruleta.aptitud:
        print("\n>>> El mejor resultado global lo dio: Torneo")
    else:
        print("\n>>> El mejor resultado global lo dio: Ruleta")
