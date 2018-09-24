"""
main.py

Cristian Martin Fernandez, Jaime Chen

Clase principal de la pasarela. Inicializa un servidor HTTP y Websockets, y recibe y envia datos a traves de ZigBee.
"""

import json
import sys
import threading
import time
from wsgiref.simple_server import make_server
from time import gmtime, strftime
import binascii
import struct

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

from geventwebsocket import WebSocketServer, WebSocketApplication, Resource

MAX_MESSAGES = 20

global counter

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2

# Comprobamos los argumentos de entrada recibidos
if len(sys.argv) not in [2,3]:
    print ('USB and baudrate should be indicated. Please run: $ python main.py COM_PORT [baudrate]:. E.G.: python main.py com8 9600')
    sys.exit()
else:
    port=sys.argv[1] # Obtenemos el puerto por argumento
    if sys.argv == 3:
        baudrate=sys.argv[2] # Obtenemos el baudrare por argumento
    else:
        baudrate = 9600

try:
    ser = serial.Serial(port, int(baudrate))
except ImportError:
    print ('Configuration not valid. Revise port and baudrate.')
    sys.exit()


# Diccionario que guarda la informacion de los nodos
global clients
dictionary = {}
clients = []
sink_info = {'max_msg': MAX_MESSAGES}

# Envia informacion a traves de ZigBee
def sendToZigBee(addr_long, addr, bytes):
    xbee.send('tx', dest_addr_long=addr_long, dest_addr=addr, data=bytes, len=len(bytes)) #frame_id=b'\x00'

# Manejador de la pagina principal
class Home(BaseHandler):
    def get(self):
        return self.render_response(
            'pages/home.html')

# Metodo principal encargado de recibir  paquetes ZigBee
def receiver(packet):
    global counter
    global sink_info
    
    try:
        print(strftime("%Y/%m/%d %H:%M:%S", gmtime()) + " Packet:" + str(packet) + "\n")

        if packet['id'] == 'rx':  # Paquete Zigbee
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
                aux['bombilla_on']=False
                id_encontrado=counter
                counter=counter+1
            else:
                aux=dictionary[id_encontrado]
                data=aux['data']
            deleted=False
            # Comprobamos que no sobrepasa el tamano maximo de data
            if len(data) == MAX_MESSAGES:
                del data[MAX_MESSAGES-1] # Eliminamos el primer elemento
                deleted=True
            try:
                # Comprobamos si recibimos un mensaje de la bombilla
                if payload.decode("ascii")=="bon":
                    aux['bombilla_on']=True
                    send_ws_data({'bombilla_on':True, 'id': id_encontrado})
                elif payload.decode("ascii")=="boff":
                    aux['bombilla_on']=False
                    send_ws_data({'bombilla_on':False, 'id': id_encontrado})
                payload = payload.decode("ascii")
            except:
                pass
            data.insert(0, {'time':strftime("%Y/%m/%d %H:%M:%S", gmtime()), 'data': payload})
            aux['data']=data
            dictionary[id_encontrado]=aux
            send_ws_data_to_id(id_encontrado,get_data(id_encontrado))
            if not encontrado:
                send_ws_data(get_nodes())
            elif not deleted:
                send_ws_data({'new_message':id_encontrado})

        elif packet['id'] == 'tx_status':  # Packet ACK
            pass
        elif packet['id'] == 'at_response':
            if packet['command'] == b'SH':
                sink_info['id_high'] = binascii.hexlify(packet['parameter']).decode("ascii")
                print('DH', sink_info['id_high'])
            elif packet['command'] == b'SL':
                sink_info['id_low'] = binascii.hexlify(packet['parameter']).decode("ascii")
                print('DL', sink_info['id_low'])
            elif packet['command'] == b'ID':
                pan_id_number = struct.unpack(">q", packet['parameter'])[0]
                sink_info['pan_id'] = format(pan_id_number, 'x')
                print('ID', sink_info['pan_id'])
            elif packet['command'] == b'OI':
                sink_info['operating_pan_id'] = binascii.hexlify(packet['parameter']).decode("ascii")
                print('OI', sink_info['operating_pan_id'])

        else:
            pass
    except Exception as e:
        print ("ERROR in ZigBee receiver "+str(e))

# Envia informacion por WS
def send_ws_data(data):
    for client in clients:
        client['ws'].send(json.dumps(data))

# Devuelve los nodos conectados a la red
def get_nodes():
    list=[]
    dic={}
    for id in dictionary:
        node_info = dictionary[id]
	#import pdb; pdb.set_trace()
        addr=str(binascii.hexlify(node_info['addr']))
        if sys.version_info >= (3,0): # Python 3
            addr=addr[2:-1]
        addr=addr[0:8] +' '+addr[8:]
        addr_long=str(binascii.hexlify(node_info['addr_long']))
        if sys.version_info >= (3,0): # Python 3
            addr_long=addr_long[2:-1]
        addr_long=addr_long[0:8] +' '+addr_long[8:]
        if 'data' in node_info:
            num_msg = len( node_info['data'])
        else:
            num_msg = 0
        aux={'id': id, 'addr':addr , 'addr_long':addr_long, 'num_msg': num_msg, 'bombilla_on':node_info['bombilla_on']}
        list.append(aux)
    dic['nodes']=list
    return dic

#Recibe una peticion HTTP para obtener los nodos conectados
def nodes(request):
    dic=get_nodes()
    response = HTTPResponse()
    response.write(json.dumps(dic))
    return response

# Envia informacion por WS a los clientes subscritos a un ID
def send_ws_data_to_id(id, data):
    for client in clients:
        if id in client['ids']:
            client['ws'].send(json.dumps(data))

# Obtiene informacion del nodo ZigBee
def get_id(request):
    global sink_info
       
    response = HTTPResponse()
    response.write(json.dumps(sink_info))
    return response


# Obtiene los datos recibidos de un ID
def get_data(id):
    dic={}
    if id in dictionary:
        dic['data']=dictionary[id]['data']
    return dic


# Recibe una peticion HTTP para obtener los mensajes recibidos de un nodo
def data(request):
    id= int(request.get_param('id'))
    data=get_data(id)
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

# URL mapping del Servidor
all_urls = [
    url('', Home, name="default"),
    url(r'^nodes', nodes, name='nodes'),
    url(r'^id', get_id, name='id'),
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


# Clase principal para la gestion de Websockets
class UMAApplication(WebSocketApplication):
    global dictionary
    def __init__(self, tuple):
        try:
            super().__init__(tuple)  # Python 3 
        except:
            super(UMAApplication,self).__init__(tuple)  # Python 2
        self.aux={}

    def on_open(self):
        self.aux['ws']=self.ws
        self.aux['ids']=[]
        clients.append(self.aux)
        self.ws.send(json.dumps(get_nodes()))

    def on_message(self, message):
        data=json.loads(message)
        if(data['register']):
            self.aux['ids'].append(data['id'])
            dic=get_data(data['id'])
            self.ws.send(json.dumps(dic))
        else:
            self.aux['ids'].remove(data['id'])

    def on_close(self, reason):
        #clients.remove(self)
        print (reason)

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

    xbee.send('at', frame_id=b'A', command=b'SH')
    xbee.send('at', frame_id=b'B', command=b'SL')
    xbee.send('at', frame_id=b'C', command=b'ID')
    xbee.send('at', frame_id=b'D', command=b'OI')
    
    # Esperamos a que se inicie la comunicacion
    time.sleep(2)

    try:
        # Inicializamos el servidor
        print('Server at http://localhost/')
        #make_server('', 80, main).serve_forever()
        WebSocketServer(
        ('0.0.0.0', 80),

        Resource({
            '^/uma': UMAApplication,
            '^/.*': main
        }),debug=False


    ).serve_forever()
    except KeyboardInterrupt:
        xbee.halt()
        ser.close()
    print('\nBye!')
