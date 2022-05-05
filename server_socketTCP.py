from utilities import *
from socketTCP import SocketTCP

if __name__ == "__main__":
  print('Creating server...')

  # Primero que nada se instancia un socket tcp,
  # se define un tamaño de buffer y una secuencia de fin de mensaje
  socketTCP = SocketTCP()
  # Con un buff_size no multiplo de 64 tarda mas pues se pierden ACKS
  buff_size: int = 128
  end_of_message: str = "\r\n\r\n"

  # Asociamos el socket a la dirección 127.0.0.1, puerto 5000
  socketTCP.bind(('localhost', 5000))

  # Recibimos mensages indefinidamente, los imprimimos y los retornamos a la dirección
  # de donde provienen
  print('Listening for messages in (127.0.0.1, 5000)...')
  while True:

    # Aceptamos conexión
    connection, address = socketTCP.accept()
    print('====== ACCEPTED CONNECTION =======')

    # Recibimos el mensaje completo junto con su dirección de origen
    msg = receive_full_mesage(connection, buff_size, end_of_message)

    # Cerramos conexión
    connection.close()

    # Imprimimos el mensaje decodificado 
    # message = buffer
    print("\nReceived message: ")
    print("=================\n")
    print(msg + '\n\n')
    print(address)
