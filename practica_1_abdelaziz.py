from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array

from time import sleep
from random import random, randint

N = 2
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
    lista_filtrada = [x for x in lista if x != -1]
    if lista_filtrada:
        return min(lista_filtrada)
    return -1


def producir(valor, semaforo_general, semaforo, index, comparacion, finalizado):
    """
    Función que produce valores aleatorios y los almacena en una variable compartida,
    usando semáforos para la sincronización.
    """
    for _ in range(N):
        # Comprobamos si ya es posible producir el siguiente valor
        semaforo.acquire()
        
        # Producción del siguiente valor
        print(f"Producer {current_process().name} produciendo")
        valor.value += randint(5, 100)
        delay()

        # Almacenamos el valor
        comparacion[index.value] = valor.value
        index.value += 1
        semaforo_general.acquire()
        print(f"Producer {current_process().name} almacenado {valor.value}")
    
    # El productor ya ha terminado de producir, ajustamos las variables compartidas
    print(f"Producer {current_process().name} finalizado")
    semaforo.acquire()
    finalizado.acquire()
    valor.value = -1
    comparacion[index.value] = -1
    semaforo_general.acquire()

        
def consumir(almacen_final, semaforo_general, semaforos, index, comparacion, finalizado):
    """
    Función que simula el consumidor, extrae los valores generados por los productores y 
    almacena el mínimo. 
    """
    # Inicializamos el índice del almacén donde se colocará el mínimo
    almacen_index = 0
    
    while True:
        # Esperar a que los productores haya producido al menos un valor
        if semaforo_general.get_value() == 0:
            
            # Comprobamos si se han completado todos los procesos
            if finalizado.get_value() == 0:
                break
            
            # Escoger el mínimo de los valores producidos por los productores
            minimo = min_list(comparacion[:])
            delay()
            print("El mínimo de la lista comparacion es:" , minimo)

            # Obtener el índice del mínimo
            index.value = comparacion[:].index(minimo)
            
            # Insertar el mínimo en el array final
            almacen_final[almacen_index] = minimo

            # Actualizar el índice del array final
            almacen_index += 1
            
            # Liberar el semáforo correspondiente al productor del mínimo
            semaforos[index.value].release()
            print("Comparación actual:", comparacion[:])
            print("Almacen por el momento", almacen_final[:])
            
            semaforo_general.release()
            
        else:
            delay()


def main():
    # Variables compartidas:

    # Valores iniciales de cada productor
    valores_iniciales = [Value('i', -2) for _ in range(NPROD)]

    # Almacén final para ser ordenado de menor a mayor
    almacen_final = Array('i', N * NPROD)

    # Array para comparar los mínimos de cada proceso
    comparacion = Array('i', NPROD)

    # Índice auxiliar para el array comparación
    index = Value('i', 0)
    
    # Inicializamos los arrays
    for i in range(NPROD):
        comparacion[i] = -2
        
    for i in range(N * NPROD):
        almacen_final[i] = -2
    
    # Semáforos de control de los procesos y consumidor
    semaforo_general = BoundedSemaphore(NPROD)
    semaforos = [Lock() for _ in range(NPROD)]
    finalizado = BoundedSemaphore(NPROD)
    
    # Listado de procesos
    lista_procesos = [Process(target=producir,
                              name=f'p_{i}',
                              args=(valores_iniciales[i],
                                    semaforo_general,
                                    semaforos[i],
                                    index,
                                    comparacion,
                                    finalizado))
                     for i in range(NPROD)]
    
    # Consumidor
    consumidor = Process(target=consumir, args=(almacen_final,
                                                semaforo_general,
                                                semaforos,
                                                index,
                                                comparacion,
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