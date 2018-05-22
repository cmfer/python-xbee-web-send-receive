/* Nombre: nodesController.js
     Autor principal: Cristian Martin Fernandez */

'use strict';

angular.module('coap_webControllers').controller(
 'NodesController', ['$rootScope','$scope','$location','$interval','Nodes', 'Data',

/**
 * @module Nodes Controller
 * @description Controlador que interactua con el servidor para obtener los datos de los nodos conectado y poder enviarle informacion.
 *
 */
function ($rootScope,$scope,$location, $interval, Nodes, Data){
    
    // Obtiene los nodos al inicio
    Nodes.get(function(response){
      $scope.nodes = response.nodes;
    }, 
    function(response){
      console.info('Error getting coap nodes list');
    });
    $interval(function() {
            // Obtiene los nodos al inicio
           Nodes.get(function(response){
              $scope.nodes = response.nodes;
            }, 
            function(response){
              console.info('Error getting coap nodes list');
            });
    }, 5000);
    
   /**
    * @description view  Muestra la ventana para visualizar los datos de un nodo.
    */
    $scope.view=function(node){
        $scope.request_correct=null;
        $scope.request_bad=null;
        $scope.node=node
        jQuery.noConflict();
            (function ($) {
               $('#showDialogView').modal('show');
            })(jQuery);
        Data.get(node.id).query(function(response){
               $scope.data=response;
        },function(response){

        });
        
        $scope.client=$interval(function() {
           Data.get(node.id).query(function(response){
               $scope.data=response;
        },function(response){

        });
    }, 5000);
  }
  
   /**
    * @description stopClient Para la monitorizacion de datos de un nodo.
    */
  $scope.stopClient=function(){
    if ($scope.client!=null){
        $interval.cancel($scope.client);
    }
  }
  
  /**
    * @description showSendDataForm Muestra la ventana para enviar datos a un nodo.
    */
    $scope.showSendDataForm=function(node){
        $scope.node=node;
        $scope.value="";
        $scope.request_correct=null;
        $scope.request_bad=null;
        jQuery.noConflict();
            (function ($) {
               $('#showDialogSend').modal('show');
            })(jQuery);
    }
    
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


