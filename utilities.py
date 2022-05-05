from dataclasses import dataclass
import socket

class ArgumentsParsingException(Exception):
    pass

class wrongResponseReceiverException(Exception):
    pass

@dataclass
class HeaderTCP:
    """Data Class usada para representar un Header TCP.

    Attributes:
    -----------

    syn (bool): Mensaje de sincronización.
    ack (bool): Mensaje de confirmación.
    fin (bool): Mensaje de termino de comunicación.
    seq (int): Número de secuencia
    """
    syn: bool
    ack: bool
    fin: bool
    seq: int

# Función reciclada de la primera actividad del semestre
def receive_full_mesage(connection_socket, buff_size: int, end_of_message: str) -> str:
    from socketTCP import SocketTCP
    # esta función se encarga de recibir el mensaje completo desde el cliente
    # en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
    # llegue el resto

    # recibimos la primera parte del mensaje
    buffer = connection_socket.recv(buff_size)
    full_message = buffer.decode()

    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(full_message, end_of_message)

    # si el mensaje llegó completo (o sea que contiene la secuencia de fin de mensaje) removemos la secuencia de fin de mensaje
    if is_end_of_message:
        full_message = full_message[0:(len(full_message) - len(end_of_message))]

    # si el mensaje no está completo (no contiene la secuencia de fin de mensaje)
    else:
        # entramos a un while para recibir el resto y seguimos esperando información
        # mientras el buffer no contenga secuencia de fin de mensaje
        while not is_end_of_message:
            # recibimos un nuevo trozo del mensaje
            buffer = connection_socket.recv(buff_size)
            # y lo añadimos al mensaje "completo"
            full_message += buffer.decode()

            # verificamos si es la última parte del mensaje
            is_end_of_message = contains_end_of_message(full_message, end_of_message)
            if is_end_of_message:
                # removemos la secuencia de fin de mensaje
                full_message = full_message[0:(len(full_message) - len(end_of_message))]

    # finalmente retornamos el mensaje
    return full_message

def contains_end_of_message(message: str, end_sequence: str) -> bool:
    if end_sequence == message[(len(message) - len(end_sequence)):len(message)]:
        return True
    else:
        return False
