from __future__ import annotations
from utilities import HeaderTCP
from random import randint
import socket


class SocketTCP:

  def __init__(self):
    self.__socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.__buff_size: int = 4096

  @staticmethod
  def parse_header(header: str) -> HeaderTCP:
    """Método estático usado para parsear un header TCP
    como string, a la estructura de datos HeaderTCP.

    Parameters:
    -----------

    header (str): Header TCP a parsear.

    Returns:
    --------

    (HeaderTCP): Versión parseada del header TCP pasado como
                 parámetro.
    """

    # Separamos por la secuencia "|||" y nos deshacemos del ultimo
    # elemento.
    header_list = header.split("|||")[:-1]

    # Definimos un lambda para convertir 0 en False y en 
    # True cualquier otra cosa
    false_if0_else_true = lambda s: False if s == '0' else True

    # Asignamos los campos a usar para la estructura
    syn = false_if0_else_true(header_list[0])
    ack = false_if0_else_true(header_list[1])
    fin = false_if0_else_true(header_list[2])
    seq = int(header_list[3])

    # construimos y retornamos la estructura
    return HeaderTCP(syn, ack, fin, seq)


  @staticmethod
  def generate_header(header: HeaderTCP) -> str:
    """Método estático usado para convertir un header TCP
    representado como una instancia de HeaderTCP a su
    representación como string.

    Parameters:
    -----------

    header (HeaderTCP): Header TCP representado como una instancia
                        de la data class HeaderTCP.

    Returns:
    --------

    (str): Representación como string del header TCP pasado como
           parámetro.
    """

    # Definimos una lambda para mapear el True a 1 y el False a 0
    ifb_1_else_0 = lambda b: 1 if b else 0

    # Generamos los campos a guardar en el header
    syn = ifb_1_else_0(header.syn)
    ack = ifb_1_else_0(header.ack)
    fin = ifb_1_else_0(header.fin)
    seq = header.seq

    # Generamos el header y lo retornamos
    return f"{syn}|||{ack}|||{fin}|||{seq}|||"

  def bind(self, address: tuple[str, int]) -> None:
    """Método encargado de *escuchar* en una dirección dada.
    Asigna el atributo address de la intancia a la dirección dada, y
    asocia el socket udp subyacente a dicha dirección.

    Parameters:
    -----------
    address (tuple[str, int]): Par IP - puerto al cual asociar el socket.
    """
    self.__socket.bind(address)
    self.address = address

  def connect(self, address: tuple[str, int]) -> None:
    """Método encargado de inciar la conexión desde esta instancia a otro
    SocketTCP que se encuentra escuchando en la dirección address. Implemente
    el lado del cliente del 3-way handshake.

    Parameters:
    -----------
    address (tuple[str, int]): Dirección en la cual se encuentra escuchando el
                               SocketTCP al cual se quiere conectar.
    """
    # Generamos un numero de secuencia aleatorio entre 0 y 100
    seq = randint(0, 100)

    # Enviamos un Header TCP con el campo syn y el codigo de secuencia generado
    fst_msg = HeaderTCP(syn=True, ack=False, fin=False, seq=seq)
    print('Enviando ', fst_msg)
    fst_msg = self.generate_header(fst_msg)
    self.__socket.sendto(fst_msg.encode(), address)

    # Recibimos y parseamos la respuesta, y vemos si el servidor aceptó la conexión
    server_response, _ = self.__socket.recvfrom(self.__buff_size)
    server_response = self.parse_header(server_response.decode())
    print('Recibido ', server_response)

    if server_response == HeaderTCP(True, True, False, seq + 1):
      snd_msg = HeaderTCP(syn=False, ack=True, fin=False, seq=seq+2)
      print('Enviando', snd_msg)
      snd_msg = self.generate_header(snd_msg)
      self.__socket.sendto(snd_msg.encode(), address)
    
  def accept(self) -> tuple[SocketTCP, tuple[str, int]]:
    """Método encargado de implementar el lado del servidor del 3-way
    handshake. Si el handshake termina de forma exitosa, se retorna
    un nuevo objeto del tipo SocketTCP y la dirección donde se encuentra
    escuchando dicho objeto.

    Returns:
    --------
    (tuple[SocketTCP, tuple[str, int]]): Par SocketTCP, dirección donde a la
                                         cual está asociado dicho objeto.
    """

    # Recibimos el primer mensaje y lo parseamos
    fst_msg, address = self.__socket.recvfrom(self.__buff_size)
    fst_msg = self.parse_header(fst_msg.decode())
    print('Recibido ', fst_msg)

    # Si el mensaje recibido es de tipo SYN, respondemos SYN + ACK, seq=x+1
    if fst_msg.syn and not fst_msg.ack and not fst_msg.fin:
      server_response = HeaderTCP(True, True, False, fst_msg.seq + 1)
      print('Enviando ', server_response)
      server_response = self.generate_header(server_response)
      self.__socket.sendto(server_response.encode(), address)

    # Recibimos el segundo mensaje y lo parseamos
    snd_msg, address = self.__socket.recvfrom(self.__buff_size)
    snd_msg = self.parse_header(snd_msg.decode())
    print('Recibido ', snd_msg)


    # Si el mensaje es ACK, seq=x+2, aceptamos la conexión y retornamos
    # un nuevo objeto de tipo SocketTCP mas la conexión donde se encuentra
    # escuchando dicho objeto.
    if snd_msg == HeaderTCP(False, True, False, fst_msg.seq+2):
      print('Conexión aceptada')
      return self, self.address

    


