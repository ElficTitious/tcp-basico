from utilities import *
from socketTCP import SocketTCP

server_socket = SocketTCP()
server_socket.bind(('localhost', 5000))

server_socket.accept()

# if __name__ == "__main__":
#   print('Creating server...')

#   # Primero que nada se instancia un socket no orientado a conexión,
#   # se define un tamaño de buffer y una secuencia de fin de mensaje
#   dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#   buff_size: int = 64
#   end_of_message: str = "\r\n\r\n"

#   # Asociamos el socket a la dirección 127.0.0.1, puerto 5000
#   dgram_socket.bind(('localhost', 5000))

#   # Recibimos mensages indefinidamente, los imprimimos y los retornamos a la dirección
#   # de donde provienen
#   print('Listening for messages in (127.0.0.1, 5000)...')
#   while True:

#     # Recibimos el mensaje completo junto con su dirección de origen
#     msg, address = receive_full_mesage(dgram_socket, buff_size, end_of_message)
#     print(msg)

#     # Imprimimos el mensaje decodificado 
#     # message = buffer
#     print("\nReceived message: ")
#     print("=================\n")
#     print(msg + '\n\n')
  
