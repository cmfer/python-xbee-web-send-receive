/* Nombre: nodesService.js
     Autor principal: Cristian, Pablo Martin Fernandez */
/**
 * @module Nodes Service
 * @name Nodes Service
 * @description  Servicio relacionado con
 * obtencion de listado de dispositivos conectados al sistema.
 * 
 */
var app = angular.module('coap_webServices');


app.factory('Nodes', ['$resource',
  function($resource){
    return $resource('/nodes', {}, {
    	get : {method:'GET', isArray:false}
    });
  }
]);

app.factory('Data', ['$resource', function($resource){
  return {
        get: function(param){ return $resource('/data', {id: param}, {
            query : {method:'GET', isArray:true}
            });
        },
		id: function(id){ return $resource('/id', {}, {
            get : {method:'GET', isArray:false}
            });
        },
        zigbee: function(id, data){ return $resource('/zigbee', {id: id, data: data}, {
            query : {method:'GET', isArray:true}
            });
        }
    }
  }
]);

app.factory('WS', ['$websocket', function($websocket){
      // Open a WebSocket connection
      var dataStream = $websocket('ws://localhost/uma');

      var collection = [];
      var nodes= [];
      var data=[];
      dataStream.onMessage(function(message) {
        var received=JSON.parse(message.data);
        if ('nodes' in received){
            nodes.length=0;
            nodes.push.apply(nodes,received.nodes);
        }else if ('data' in received) {
            data.length=0;
            data.push.apply(data,received.data);
        }
        else if ('new_message' in received){
            for (var i=0; i<nodes.length;i++ ){
                var node=nodes[i];
                if (node.id==received.new_message){
                    node.num_msg=node.num_msg+1;
                    break;
                }
             }
        }
        else if ('bombilla_on' in received){
            for (var i=0; i<nodes.length;i++ ){
                var node=nodes[i];
                if (node.id==received.id){
                    node.bombilla_on=received.bombilla_on;
                    break;
                }
             }
        }
      });

      var methods = {
        nodes :nodes,
        data: data,
        send: function(d) {
          dataStream.send(JSON.stringify(d));
        },
        close : function(){
            dataStream.close();
        }
      };

      return methods;
    }])