/* Nombre: nodesService.js
     Autor principal: Cristian, Pablo Martin Fernandez */
/**
 * @module Nodes Service
 * @name Nodes Service
 * @description  Servicio relacionado con
 * obtencion de listado de dispositivos conectados al sistema.
 * Define CoAPNodes.
 */
var app = angular.module('coap_webServices');
/**
 * @module CoAPNodes
 * @name CoAPNodes
 * @description Servicio que trata las peticiones
 * relacionadas con la obtencion del listado de dispositivos conectados al sistema.
 * Tiene método GET.
 */
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