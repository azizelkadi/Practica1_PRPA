from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array

from time import sleep
import random

N = 2
NPROD = 4


def delay(factor=0.3):
    """
    Función para introducir un retraso aleatorio en la ejecución del programa.
    """
    sleep(random.random() * factor)


def min_list(lista):
    """
    Retorna el valor mínimo de una lista de enteros ignorando los valores -1.
    """
    lista_filtrada = [x for x in lista if x != -1]
    if lista_filtrada:
        return min(lista_filtrada)
    return None


def producir(value, semaforo_general, semaphore, index, comparacion, terminate):
    """
    Función que produce valores aleatorios y los almacena en una variable compartida,
    usando semáforos para la sincronización.
    """
    for _ in range(N):
        # TODO: comentario
        semaphore.acquire()
                
        # TODO: comentario
        print(f"Producer {current_process().name} produciendo")
        
        # TODO: comentario
        value.value += random.randint(2, 10)
        delay()
        comparacion[index.value] = value.value
        index.value += 1
        semaforo_general.acquire()
        
        # TODO: comentario
        print(f"Producer {current_process().name} almacenado {value.value}")
    
    # TODO: comentario
    print(f"Producer {current_process().name} finalizado")
    semaphore.acquire()
    terminate.acquire()
    value.value = -1
    comparacion[index.value] = -1
    semaforo_general.acquire()

        
def consumir(almacen_final, semaforo_general, semaphores, comparacion, index, terminate):
    # TODO: comentario
    almacen_index = 0
    
    while True:
        # Esperar a que un productor haya producido un valor
        if semaforo_general.get_value() == 0:
            
            # TODO: comentario
            if terminate.get_value() == 0:
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
            semaphores[index.value].release()
            print("Comparación actual:", comparacion[:])
            print("Almacen por el momento", almacen_final[:])
            
            semaforo_general.release()
            
        else:
            delay()
        
def main():
    # TODO: comentar todo
    almacen_final = Array('i', N * NPROD)
    semaforo_general = BoundedSemaphore(NPROD)
    comparacion = Array('i', NPROD)    
    index = Value('i', 0)
    
    for i in range(NPROD):
        comparacion[i] = -2
        
    for i in range(N * NPROD):
        almacen_final[i] = -2
        
    valores_iniciales = [Value('i', -2) for _ in range(NPROD)]
    semaforos = [Lock() for _ in range(NPROD)]
    terminate = BoundedSemaphore(NPROD)
    
    lista_procesos = [Process(target=producir,
                              name=f'p_{i}',
                              args=(valores_iniciales[i],
                                  semaforo_general,
                                  semaforos[i],
                                  index,
                                  comparacion,
                                  terminate))
                     for i in range(NPROD)]
    
    consumidor = Process(target=consumir, args=(almacen_final,
                                                semaforo_general,
                                                semaforos,
                                                comparacion,
                                                index,
                                                terminate))
    
    for p in lista_procesos:
        p.start()
    consumidor.start()
    
    for p in lista_procesos:
        p.join()
    consumidor.join()
    
    print("Almacén final", almacen_final[:])
    
if __name__ == "__main__":
    main()