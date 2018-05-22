"""
main.py

Cristian Martin Fernandez

Clase principal de la pasarela. Inicializa un servidor HTTP y recibe y envia datos a traves de ZigBee.
"""

import json
import sys
import threading
import time
from wsgiref.simple_server import make_server
from time import gmtime, strftime
import binascii

import serial
from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.http import method_not_allowed
from wheezy.routing import url
from wheezy.web.middleware import bootstrap_defaults
from wheezy.web.middleware import path_routing_middleware_factory
from wheezy.web.handlers.base import BaseHandler
from wheezy.html.ext.template import WidgetExtension
from wheezy.html.utils import html_escape
from wheezy.template.engine import Engine
from wheezy.template.ext.core import CoreExtension
from wheezy.template.loader import FileLoader
from wheezy.web.templates import WheezyTemplate
from wheezy.web.handlers import file_handler

from xbee import ZigBee
global counter

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2

# Comprobamos los argumentos de entrada recibidos
if len(sys.argv)<3:
    print ('USB and baudrate should be indicated. Please run: $ python main.py [COM_PORT] [baudrate]:. E.G.: python main.py com8 19200')
    sys.exit()
else:
    port=sys.argv[1] # Obtenemos el puerto por argumento
    baudrate=sys.argv[2] # Obtenemos el baudrare por argumento

try:
    ser = serial.Serial(port, int(baudrate))
except ImportError:
    print ('Configuration not valid. Revise port and baudrate.')
    sys.exit()


# Diccionario que guarda la informacion de los servidores CoAP y sus recursos
dictionary = {}


def sendToZigBee(addr_long, addr, bytes):
    xbee.send('tx', dest_addr_long=addr_long, dest_addr=addr, data=bytes, len=len(bytes)) #frame_id=b'\x00'
        

class Home(BaseHandler):
    def get(self):
        return self.render_response(
            'pages/home.html')

# Metodo principal de la clase CoAP, encargado de recibir  paquetes de los Servidores CoAP
def receiver(packet):
    global counter
    try:
        print(strftime("%Y/%m/%d %H:%M:%S", gmtime()) + " Packet:" + str(packet) + "\n")

        if packet['id'] == 'rx':  # Packet from Server CoAP
            payload = packet['rf_data']
            addr_long = packet['source_addr_long']
            addr = packet['source_addr']
            encontrado=False
            
            # Comprobamos si hemos recibido una peticion del nodo anteriormente
            for id in dictionary:
                if dictionary[id]['addr_long']==addr_long:
                    encontrado=True
                    id_encontrado=id
                    break                  
            
            # En caso de no encontrar una peticion previa, inicializamos
            if not encontrado:
                aux={}
                data=[]
                aux['addr']=addr
                aux['addr_long']=addr_long
                id_encontrado=counter
                counter=counter+1
            else:
                aux=dictionary[id_encontrado]
                data=aux['data']
                
            # Comprobamos que no sobrepasa el tamano maximo de data
            if len(data)==20:
                 del data[0] # Eliminamos el primer elemento
             
            data.append({'time':strftime("%Y/%m/%d %H:%M:%S", gmtime()), 'data': payload.decode("ascii")})
            aux['data']=data
            dictionary[id_encontrado]=aux
        elif packet['id'] == 'tx_status':  # Packet ACK
            pass
    except Exception as e:
        print ("ERROR in ZigBee receiver "+str(e))

#Recibe una peticion HTTP para obtener los nodos conectados
def nodes(request):
    list=[]
    dic={}
    for id in dictionary:
        addr=str(binascii.hexlify(dictionary[id]['addr']))[2:-1]
        addr=addr[0:8] +' '+addr[8:]
        addr_long=str(binascii.hexlify(dictionary[id]['addr_long']))[2:-1]
        addr_long=addr_long[0:8] +' '+addr_long[8:]
        aux={'id': id, 'addr':addr , 'addr_long':addr_long}
        list.append(aux)
    dic['nodes']=list
    response = HTTPResponse()
    response.write(json.dumps(dic))
    return response

# Recibe una peticion HTTP para obtener los mensajes recibidos de un nodo    
def data(request):
    id= int(request.get_param('id'))
    data=dictionary[id]['data']
    response = HTTPResponse()
    response.write(json.dumps(data))
    return response

# Recibe una peticion HTTP para enviar un mensaje a ZigBee    
def datatoZigBee(request):
    response = HTTPResponse()
    try:
        id= int(request.get_param('id'))
        data=request.get_param('data').encode("ascii")
        addr=dictionary[id]['addr']
        addr_long=dictionary[id]['addr_long']
        sendToZigBee(addr_long, addr, data)
    except Exception as e:
        print ("Error enviando datos "+ str(e))
        response.status_code = 401
    return response
    
# URL mapping del Proxy CoAP
all_urls = [
    url('', Home, name="default"),
    url(r'^nodes', nodes, name='nodes'),
    url(r'^data', data, name='data'),
    url(r'^zigbee', datatoZigBee, name='zigbee'),
    url('static/{path:any}',
        file_handler(root='static/'),
        name='static')

]
# Configuracion del servidor HTTP

options = {}
    # Template Engine
searchpath = ['templates']
engine = Engine(
    loader=FileLoader(searchpath),
    extensions=[
    CoreExtension(),
    WidgetExtension(),
])
engine.global_vars.update({
    'h': html_escape
})
options.update({
    'render_template': WheezyTemplate(engine)
})

main = WSGIApplication(
    middleware=[
        bootstrap_defaults(url_mapping=all_urls),
        path_routing_middleware_factory
    ],
    options=options
)
# Funcion principal
if __name__ == '__main__':
    global counter
    counter=0
    
    # Comunicacion soportada en el Smart Gateway: Zigbee
    xbee = ZigBee(ser, escaped=True, callback=receiver)

    # Esperamos a que se inicie la comunicacion
    time.sleep(2)

    try:
        # Inicializamos el servidor
        make_server('', 80, main).serve_forever()
        print('Server started. Visit http://localhost/')
    except KeyboardInterrupt:
        xbee.halt()
        ser.close()
    print('\nBye!')
