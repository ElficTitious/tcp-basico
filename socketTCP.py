from __future__ import annotations
from ast import Bytes
from pickle import bytes_types
import time
from utilities import HeaderTCP, wrongResponseReceiverException
from random import randint
import socket


class SocketTCP:

  def __init__(self):
    self.__socket: socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.__buff_size: int = 4096
    self.__bytes_left_to_recv: int = 0

  @staticmethod
  def partition_msg(num_bytes: int, msg: str) -> list[str]:
    """Método estático usado para particionar un mensaje msg
    en substrings de una cantidad de bytes máxima igual a num_bytes.

    Parameters:
    -----------
    num_bytes (int): Número de bytes bajo el cual particionar.
    msg (str): Mensaje a particionar.

    Returns:
    --------
    (list[str]): Lista de mensajes de cantidad de bytes máxima igual
                 a num_bytes.
    """
    sub_msgs = []
    curr_submsg = ""
    i = 0
    # Mientras queden caracteres
    while i < len(msg):

      # Si al agregar el caracter actual al substring actual, seguimos
      # teniendo menos de num_bytes, agregamos el caracter
      if len(curr_submsg.encode()) + len(msg[i].encode()) <= num_bytes:
        curr_submsg += msg[i]
        i += 1

      # De lo contrario agregamos el substring a la lista de substrings,
      # y reseteamos el substring actual.
      else:
        sub_msgs.append(curr_submsg)
        curr_submsg = ""

    # Agregamos el ultimo substring
    sub_msgs.append(curr_submsg)
    
    return sub_msgs

  @staticmethod
  def get_data(tcp_msg: str) -> str:
    """Método estático usado para rescatar la data de un mensaje TCP,
    quitando de el la sección de headers.

    Parameters:
    -----------
    tcp_msg (str): Mensaje TCP de la forma [SYN]|||[ACK]|||[FIN]|||[SEQ]|||[DATOS].

    Returns:
    --------
    (str): Sección de datos del mensaje TCP.
    """
    data = tcp_msg.split("|||")[-1]
    return data

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
    fst_msg = self.generate_header(fst_msg)
    self.__socket.sendto(fst_msg.encode(), address)

    # Recibimos y parseamos la respuesta, y vemos si el servidor aceptó la conexión
    server_response, transmitter_addr = self.__socket.recvfrom(self.__buff_size)
    server_response = self.parse_header(server_response.decode())

    if server_response == HeaderTCP(True, True, False, seq + 1):

      # Si el mensaje correspondía a un SYN+ACK, respondemos ACK a
      # la dirección correspondiente
      snd_msg = HeaderTCP(syn=False, ack=True, fin=False, seq=seq+2)

      # fijamos el numero de secuencia
      self.seq = snd_msg.seq

      snd_msg = self.generate_header(snd_msg)

      # Asignamos la dirección asociada al socket y respondemos
      self.conn_sock_addr = transmitter_addr

      self.__socket.sendto(snd_msg.encode(), transmitter_addr)
    
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

    # Creamos un nuevo socket binded a ('localhost', puerto+1) o al primer
    # puerto disponible
    i = 1
    while True:
      try:
        new_socketTCP = SocketTCP()
        new_socketTCP.bind((self.address[0], self.address[1] + i))
      except:
        i += 1
      else:
        break

    # Si el mensaje recibido es de tipo SYN, respondemos SYN + ACK, seq=x+1
    # desde el nuevo socket
    if fst_msg.syn and not fst_msg.ack and not fst_msg.fin:
      
      server_response = HeaderTCP(True, True, False, fst_msg.seq + 1)
      server_response = self.generate_header(server_response)
      new_socketTCP.__socket.sendto(server_response.encode(), address)

    # Recibimos el segundo mensaje y lo parseamos
    snd_msg, address = new_socketTCP.__socket.recvfrom(self.__buff_size)
    snd_msg = self.parse_header(snd_msg.decode())

    # Si el mensaje es ACK, seq=x+2, aceptamos la conexión y retornamos
    # un nuevo objeto de tipo SocketTCP mas la conexión donde se encuentra
    # escuchando dicho objeto.
    if snd_msg == HeaderTCP(False, True, False, fst_msg.seq+2):

      # Fijamos el número de secuencia y la dirección de conexión
      new_socketTCP.seq = snd_msg.seq
      new_socketTCP.conn_sock_addr = address
      
      return new_socketTCP, new_socketTCP.address

  def settimeout(self, timeout_in_seconds: float) -> None:
    """Método encargado de setear un timeout al socket. Usa la función
    settimeout de sockets para setear el timeout del socket udp
    subyacente.

    Parameters:
    -----------
    timeout_in_seconds (float): Tiempo de timeout a fijar en el socket
                                en segundos.
    """
    # seteamos el timeout al socket udp subyacente
    self.__socket.settimeout(timeout_in_seconds)

  def send(self, msg: str) -> None:
    """Método encargado de enviar un mensaje a un socket; implementa el
    lado del emisor de Stop & Wait.

    Parameters:
    -----------
    msg (str): Mensaje a enviar al socket desde donde se llama el método.
    """
    # Comenzamos particionando el mensaje a enviar en substrings de máximo
    # 64 bytes.
    msgs_to_send = self.partition_msg(64, msg)

    # Como lo primero a comunicar es el largo total en bytes del mensaje, 
    # agregamos dicha información a la lista de mensajes por enviar.
    msgs_to_send.insert(0, len(msg.encode()))

    # Se comienza el Stop & Wait
    i = 0
    bytes_sent = 0
    while i < len(msgs_to_send):

      try:
        # Construimos el header
        tcp_msg_to_send = self.generate_header(
          HeaderTCP(
            False, False, False, self.seq
          )
        )

        # Agregamos los datos
        tcp_msg_to_send += str(msgs_to_send[i])

        # Actualizamos el numero de secuencia
        self.seq += len(str(msgs_to_send[i]).encode())

        # Enviamos el mensaje
        self.__socket.sendto(tcp_msg_to_send.encode(), self.conn_sock_addr)

        # Recibimos y parseamos la respuesta
        recvd_msg, _ = self.__socket.recvfrom(self.__buff_size)
        recvd_msg_header = self.parse_header(recvd_msg.decode())

        # Si la respuesta recibida no tiene un header 0|||1|||0|||seq+bytes_sent|||,
        # arrojamos un error generico.
        if recvd_msg_header != HeaderTCP(False, True, False, self.seq):
          raise Exception()

      # Si se arroja un error disminuimos los bytes enviados al valor anterior y
      # no actualizamos el substring a enviar.
      except:
        self.seq -= len(str(msgs_to_send[i]).encode())

      # De lo contrario, si se recibió la respuesta esperada, actualizamos el indice 
      # del substring a enviar a continuación.
      else:
        i += 1

  def recv(self, buff_size: int) -> Bytes:
    """Método encargado de recibir un mensaje dado un tamaño de buffer
    igual a buff_size. Maneja el lado del receptor de Stop & Wait.

    Parameters:
    -----------
    buff_size (int): Tamaño de buffer donde recibir el mensaje.

    Returns:
    --------
    (Bytes): Mensaje recibido en el buffer de tamaño buff_size.
    """

    # En un inicio no hemos recibido ningún byte
    bytes_recvd = 0

    # Recibimos un mensaje
    last_recvd_msg, transmitter_address = self.__socket.recvfrom(self.__buff_size)

    # Revisamos si se está intentando cerrar conexión
    if self.parse_header(last_recvd_msg.decode()) == HeaderTCP(False, False, True, self.seq):

      # Enviamos FIN+ACK
      fin_ack_msg = self.generate_header(
        HeaderTCP(
          False, True, True,
          self.seq+1
        )
      )
      self.__socket.sendto(fin_ack_msg.encode(), transmitter_address)

      # Recibimos y parseamos la respuesta, y vemos si corresponde a un ACK
      response, _ = self.__socket.recvfrom(self.__buff_size)
      response = self.parse_header(response.decode())
      if response == HeaderTCP(False, True, False, self.seq+2):

        # Si correspondía a ACK cerramos la conexión (retornamos para mantener
        # firma del método y para no bloquear ejecución)
        self.__socket.close()
        return "".encode()

    # Si self.__bytes_left_to_recv es igual a 0, significa que no hemos
    # comenzado a recibir el mensaje siendo enviado, y por ende debemos
    # recibir primero su largo.
    if self.__bytes_left_to_recv == 0:

      # Intentamos hacer ACK mientras no tengamos certeza que el emisor
      # recibió una respuesta.
      recvd_msg = False
      while not recvd_msg:
        try:
          
          # Obtenemos la data que debe contener el largo
          last_msg_data = self.get_data(last_recvd_msg.decode())

          # Actualizamos los bytes recibidos y el número de secuencia
          bytes_recvd += len(last_msg_data.encode())
          self.seq += len(last_msg_data.encode())

          # Construimos el header de la respuesta
          tcp_msg_to_send = self.generate_header(
            HeaderTCP(
              False, True, False, 
              self.seq
            )
          )

          # Enviamos la respuesta
          self.__socket.sendto(tcp_msg_to_send.encode(), transmitter_address)

          # Recibimos y parseamos la respuesta
          last_recvd_msg, transmitter_address = self.__socket.recvfrom(self.__buff_size)
          last_recvd_msg_header = self.parse_header(last_recvd_msg.decode())

          # Si el header de la respuesta no corresponde a 
          # 0|||0|||0|||seq+bytes_recvd|||, levantamos un error
          if last_recvd_msg_header != HeaderTCP(False, False, False, self.seq):
            raise wrongResponseReceiverException()

        # Si recibimos una respuesta erronea disminuimos los bytes 
        # recibidos al valor anterior, y lo mismo respecto al numero de secuencia
        except wrongResponseReceiverException:
          bytes_recvd -= len(last_msg_data.encode())
          self.seq -= len(last_msg_data.encode())

        # De lo contrario, si se recibió la respuesta esperada, asignamos
        # self.__bytes_left_to_recv a int(msg_data), que es el largo en bytes
        # del mensaje a recibir, y cambiamos recvd_msg a True.
        else:
          self.__bytes_left_to_recv = int(last_msg_data)
          recvd_msg = True

    # Definimos mensaje recibido
    recvd_total_msg = ""

    # Definimos el largo en bytes del largo del mensaje
    bytes_msg_len = bytes_recvd

    # Acá, o recibimos en esta llamada el largo del mensaje a recibir, o
    # lo recibimos en una llamada anterior, en ambos casos seguimos recibiendo
    # mientras no hayamos recibido buff_size bytes o self.__bytes_left_to_recv == 0.
    while True:

      try:
          
        # obtenemos la data del ultimo mensaje
        last_msg_data = self.get_data(last_recvd_msg.decode())

        # Actualizamos los bytes recibidos, por recibir y el número de secuencia
        bytes_recvd += len(last_msg_data.encode())
        self.seq += len(last_msg_data.encode())
        self.__bytes_left_to_recv -= len(last_msg_data.encode())

        # Construimos el header de la respuesta
        tcp_msg_to_send = self.generate_header(
          HeaderTCP(
            False, True, False, 
            self.seq
          )
        )

        # Enviamos la respuesta
        self.__socket.sendto(tcp_msg_to_send.encode(), transmitter_address)

        if bytes_recvd > buff_size + bytes_msg_len:
          bytes_recvd -= len(last_msg_data.encode())
          return recvd_total_msg.encode()
        

        elif self.__bytes_left_to_recv == 0 or bytes_recvd == buff_size + bytes_msg_len:
          recvd_total_msg += last_msg_data
          return recvd_total_msg.encode()

        # Recibimos y parseamos lo que nos responden
        last_recvd_msg, transmitter_address = self.__socket.recvfrom(self.__buff_size)
        last_recvd_msg_header = self.parse_header(last_recvd_msg.decode())

        # Si el header de la respuesta no corresponde a 
        # 0|||0|||0|||seq+bytes_recvd|||, levantamos un error generico
        if last_recvd_msg_header != HeaderTCP(False, False, False, self.seq):
          raise wrongResponseReceiverException()
      
      # Si recibimos una respuesta erronea volvemos a los valores anteriores de
      # bytes_recv, self.__bytes_left_to_recv y self.seq 
      except wrongResponseReceiverException:
        bytes_recvd -= len(last_msg_data.encode())
        self.seq -= len(last_msg_data.encode())
        self.__bytes_left_to_recv += len(last_msg_data.encode())

      # De lo contrario, si se recibió la respuesta esperada, agregamos la
      # sección recibida al mensaje total.
      else:
        recvd_total_msg += last_msg_data

  def close(self) -> None:
    """Método encargado de implementar el cierre de conexión desde el
    lado del Host A.
    """

    # Construimos el FIN
    fin_msg_to_send = self.generate_header(
      HeaderTCP(
        False, False, True, 
        self.seq
      )
    )
    self.__socket.sendto(fin_msg_to_send.encode(), self.conn_sock_addr)

    # Recibimos y parseamos la respuesta, y vemos si corresponde a un FIN+ACK
    response, _ = self.__socket.recvfrom(self.__buff_size)
    response = self.parse_header(response.decode())

    if response == HeaderTCP(False, True, True, self.seq + 1):
      # Si correspondía a un FIN+ACK, respondemos ACK
      ack_msg_to_send = self.generate_header(
        HeaderTCP(
          False, True, False, 
          self.seq+2)
      )
      self.__socket.sendto(ack_msg_to_send.encode(), self.conn_sock_addr)

      # Cerramos conexión
      self.__socket.close()




