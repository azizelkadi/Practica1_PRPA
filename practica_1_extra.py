from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Lock, Semaphore
from multiprocessing import current_process
from multiprocessing import Value, Array

from time import sleep
from random import random, randint

N = 3
NPROD = 4


def delay(factor=0.3):
    """
    Función para introducir un retraso aleatorio en la ejecución del programa.
    """
    sleep(random() * factor)


def min_list(lista):
    """
    Calcula el valor mínimo de una lista de enteros ignorando los valores -1.
    """
    lista_filtrada = [x for x in lista if x > 0]
    if lista_filtrada:
        return min(lista_filtrada)
    return -1


def producir(valor, almacen_productor, empty, non_empty):
    """
    Función que produce valores aleatorios y los almacena en un almacén propio.
    Hace uso de dos semáforos Enpty y Non-Empty para controlar al consumidor y que no
    ejecute el mínimo si hay un proceso atrasado.
    """
    for i in range(N):
        # Semáforo empty
        empty.acquire()

        # Producción del siguiente valor
        print(f"Producer {current_process().name} produciendo")
        valor.value += randint(3, 10)
        delay()
        
        # Almacenamos el valor
        almacen_productor[i] = valor.value
        print(f"Producer {current_process().name} almacenado {valor.value}")

        # Liberamos semáforo non_empty
        non_empty.release()
        
    
    # Finalización
    print(f"Producer {current_process().name} finalizado")

        
def consumir(almacen_final, almacenes_productores, semaforos_empty, semaforos_non_empty, posiciones, finalizado):
    """
    Función que toma los resultados de los almacenes de los productores, extrae el mínimo y lo 
    almacena en un buffer. Hace uso de los semáforos Non-empty y Empty para controlar la 
    extracción del mínimo.
    """
    # Inicializamos el índice del almacén donde se colocará el mínimo
    almacen_index = 0
    
    # Inicializamos los semáforos de control
    for i in range(NPROD):
        semaforos_non_empty[i].acquire()
        semaforos_non_empty[i].release() 

    # Iteramos mientras no se hayan extraido todos los números
    while True:

        # Comprobamos si se han extraido todos los números
        if finalizado.get_value() == 0:
            break

        # Extraemos los elementos de los almacenes de los productores
        comparacion = [alm[i] if i < len(alm) else -1 for alm, i in zip(almacenes_productores, posiciones)]
        print("Comparación actual:", comparacion[:])
        
        # Escogemos el mínimo de los valores producidos
        minimo = min_list(comparacion)
        delay()
        print("El mínimo de la lista comparacion es:" , minimo)

        # Obtenemos el índice del mínimo
        index_minimo = comparacion.index(minimo)

        # Liberamos el semáforo Empty correspondiente
        semaforos_empty[index_minimo].release()  
        
        # Insertamos el mínimo en el almacén final
        almacen_final[almacen_index] = minimo

        # Actualizamos el índice del almacén final
        almacen_index += 1
        
        # Actualizar el índice del almacen del productor correspondiente
        posiciones[index_minimo] += 1

        # Comprobamos si ha finalizado de extraer los números de ese proceso
        if posiciones[index_minimo] == N:
            finalizado.acquire()

        # Entramos en el semáforo Non-Empty correspondiente
        semaforos_non_empty[index_minimo].acquire()  
        
        # Mostramos almacén final actual
        print("Almacén actual:", almacen_final[:])
        delay()
        
def main():
    # Variables compartidas:

    # Almacén final para ser ordenado de menor a mayor
    almacen_final = Array('i', N * NPROD)

    # Array con las posiciones actuales de los almacenes de cada productor
    posiciones = Array('i', NPROD)

    # Lista con los almacenes de cada productor
    almacenes_productores = [Array('i', N) for _ in range(NPROD)]

    # Valores iniciales de cada productor
    valores_iniciales = [Value('i', -2) for _ in range(NPROD)]

    # Inicializamos los arrays
    for i in range(NPROD):
        posiciones[i] = 0
        
    for i in range(N * NPROD):
        almacen_final[i] = -2

    # Semáforos de control de los procesos y consumidor
    semaforos_empty = [Lock() for _ in range(NPROD)]
    semaforos_non_empty = [Semaphore(0) for _ in range(NPROD)]
    finalizado = BoundedSemaphore(NPROD)

    # Listado de procesos
    lista_procesos = [Process(target=producir,
                              name=f'p_{i}',
                              args=(valores_iniciales[i],
                                    almacenes_productores[i],
                                    semaforos_empty[i],
                                    semaforos_non_empty[i]))
                     for i in range(NPROD)]
    
    # Consumidor
    consumidor = Process(target=consumir, args=(almacen_final,
                                                almacenes_productores,
                                                semaforos_empty,
                                                semaforos_non_empty,
                                                posiciones,
                                                finalizado))
    
    # Iniciamos los procesos y el consumidor
    for p in lista_procesos:
        p.start()
    consumidor.start()
    
    for p in lista_procesos:
        p.join()
    consumidor.join()
    
    # Mostramos el almacén final ya ordenado
    print("Almacén final", almacen_final[:])
    
if __name__ == "__main__":
    main()