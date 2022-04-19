from dataclasses import dataclass
import socket

class ArgumentsParsingException(Exception):
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

def receive_full_mesage(connection_socket: socket, buff_size: int, end_of_message: str) -> tuple[str, tuple[str, int]]:
    # esta función se encarga de recibir el mensaje completo desde el cliente
    # en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
    # llegue el resto

    # recibimos la primera parte del mensaje
    buffer, address = connection_socket.recvfrom(buff_size)
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
            buffer, address = connection_socket.recvfrom(buff_size)
            # y lo añadimos al mensaje "completo"
            full_message += buffer.decode()

            # verificamos si es la última parte del mensaje
            is_end_of_message = contains_end_of_message(full_message, end_of_message)
            if is_end_of_message:
                # removemos la secuencia de fin de mensaje
                full_message = full_message[0:(len(full_message) - len(end_of_message))]

    # finalmente retornamos el mensaje junto con la direccion de donde proviene
    return full_message, address

def send_full_message(connection_socket: socket, address: tuple[str, int], buff_size: int, message: str):
    """Funcion que envia el mensaje `message` completo a la direccion `address` a traves del socket 
    `connection_socket`. Para esto se envian trozos de cantidad de bytes menor o igual a `buff_size`
    hasta que se completa el mensaje.

    Parameters:
    connection_socket (socket): Socket UDP a través del cual enviar el mensaje
    address (tuple[str, int]): Dirección a la cual enviar el mensaje
    buff_size (int): Tamaño del buffer de quien recibe el mensaje
    message: Mensaje a enviar (debe incluir la secuencia de fin de mensaje)
    """
    encoded_message = message.encode()
    lo_index = 0
    hi_index = buff_size if buff_size < len(encoded_message) else len(encoded_message)
    while lo_index < len(encoded_message):
        connection_socket.sendto(encoded_message[lo_index:hi_index], address)

        lo_index = hi_index
        hi_index = hi_index + buff_size if hi_index + buff_size <= len(encoded_message) else len(encoded_message)
        
        


def contains_end_of_message(message: str, end_sequence: str) -> bool:
    if end_sequence == message[(len(message) - len(end_sequence)):len(message)]:
        return True
    else:
        return False
