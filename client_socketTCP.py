import sys
from socketTCP import SocketTCP
from utilities import *

if __name__ == "__main__":

  # Primero que nada se instancia un socket tcp,
  # se define un tamaño de buffer y una secuencia de fin de mensaje
  socketTCP = SocketTCP()
  end_of_message: str = "\r\n\r\n"

  try:

    if len(sys.argv) == 4:
      args: list = sys.argv[1:]
      addr: str = args[0]
      port: int = int(args[1])
      file_name: str = args[2]
    
    else:
      raise ArgumentsParsingException('Error parsing arguments, script should be run as: \n \
      python3 client.py [address] [port] [file_name].txt')

  except ArgumentsParsingException as err:
    print(err)
  
  else:

    try:
      # Leemos el contenido del archivo (el cual debe estar dentro del directorio
      # donde se encuentra este archivo) y enviamos dicho contenido al servidor
      f = open(file_name, "r")
      file_content: str = f.read()
      f.close()

      socketTCP.settimeout(0.8)
      print('set')

      socketTCP.connect((addr, port))
      print('connected')
      socketTCP.send(file_content + end_of_message)
      print(f"Sent content of file {file_name} to server running on ({addr}, {port})")

      # Recibimos el cierre de conexión
      socketTCP.recv(1024)

    # Si surge algún error lo reportamos
    except:
      print(f"Error while trying to read file {file_name}")