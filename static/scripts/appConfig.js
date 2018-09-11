/* Nombre: appConfing.js
     Autor principal: Cristian Martin Fernandez */

'use strict';

var app= angular.module('coap_web',
    ['coap_webControllers',
     'coap_webServices','ngRoute','ngResource','ngWebSocket']);

// Módulo de los controladores
angular.module('coap_webControllers',['ngRoute','ngResource','coap_web','coap_webServices']);

// Módulo de los servicios (API REST)
angular.module('coap_webServices',['ngResource']);

app.config(function($interpolateProvider) {
$interpolateProvider.startSymbol('{[{');
$interpolateProvider.endSymbol('}]}');
});

/* Configuración necesaria para enviar el token CSRF en cada petición, y así evitar que 
   funcionen peticiones sin haber iniciado sesión previamente */
app.config(['$httpProvider',function($httpProvider){
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);