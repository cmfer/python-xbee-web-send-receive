/* Nombre: nodesController.js
     Autor principal: Cristian Martin Fernandez */

'use strict';

angular.module('coap_webControllers').controller(
 'NodesController', ['$rootScope','$scope','$location','$interval','Nodes', 'Data','WS',

/**
 * @module Nodes Controller
 * @description Controlador que interactua con el servidor para obtener los datos de los nodos conectado y poder enviarle informacion.
 *
 */
function ($rootScope,$scope,$location, $interval, Nodes, Data,WS){
    
     $scope.onExit = function() {
     WS.close();
    };
    $scope.nodes=WS.nodes;
    
	Data.id().get(function(response){
		$scope.id = response;
	}, function(response){});

     $scope.ws = WS;
	/**
    * @description view  Muestra la ventana para visualizar los datos de un nodo.
    */
    $scope.view=function(node){
        $scope.request_correct=null;
        $scope.request_bad=null;
        $scope.node=node;
        $scope.data=WS.data;
        jQuery.noConflict();
            (function ($) {
               $('#showDialogView').modal('show');
            })(jQuery);
        var dic={'register': true, id: node.id}
        WS.send(dic);
     
  }
  
   /**
    * @description stopClient Para la monitorizacion de datos de un nodo.
    */
	var stopClient = function(){
        var dic={'register': false, id: $scope.node.id}
        WS.send(dic);
	}
  
	$('#showDialogView').on('hidden.bs.modal', function () {
		stopClient();
	})
    
    /**
    * @description sendData Envia datos a un nodo.
    */
    $scope.sendData=function(){
        Data.zigbee($scope.node.id,$scope.value).query(function(response){
               $scope.request_correct=true;
        },function(response){
            $scope.request_bad=true;
        });
    }
}]);


