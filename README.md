# Notas de net
- Parece ser que es casi igual que el metodo por usb, mandar la lista de archivos a la switch y recibir que rom se selecciono para instalacion.
Leyendo el codigo fuente de ns-usbloader, me di cuenta que se codifican los directorios de las roms en un formato que usan las urls.
`URLEncoder.encode()` en java `urllib.parse.quote()` en python
- Se usan encabezados personalizados puta madre

# Funcionalidad de net
Se necesita de un socket servidor con los siguientes parametros `AF_INET` `SOCK_STREAM` `IPPROTO_IP`. Esto lo estoy deduciendo porque en el codigo de AwooInstaller el socket del servidor se crea con estos parametros:
```c++
static int m_serverSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
```
## Handshake
Para realizar el handshake entre dispositivos se necesita de otro socket (no se porque) INET, se conecta a la ip y puerto de la switch (2000). Este socket debe mandar un el largo de un string separado por caracteres de newlines (`\n`) en donde haya informacion del host y el archivo a mandar a la switch, y luego el string en cuestion
Ejemplo:
```
# first send (message length)
67

# second send
192.168.0.23:6033/Ori_v103.xci\n192.168.0.23:6033/SMBP_Jamboree.xci\n
```
Este socket su unico proposito es hacer este handshake, asi que se debe cerrar despues de mandar la lista

## ServeLoop

Se entra en un loop infinito en donde el socket servidor debe de aceptar la conexion de la switch, despues se reciben las solicitudes que la switch manda.

Las solicitudes se reciben en paquetes, que se deben de guardar en una lista. El primer elemento de la lista es la solicitud, puede ser una de los siguientes:
- `DROP`: Se utiliza cuando el programa termina
- `HEAD`: Se utiliza para obtener el peso del archivo seleccionado. Para manejar esta solicitud se debe mandar una [solicitud de codigo 200](#CODE_200).
- `GET`: Se utiliza para obtener el archivo seleccionado. Cuando esta solicitud se manda, debera de haber una linea en la lista de paquetes que contiene el rango que se debe de mandar. En el codigo de `ns-usbloader` se obtiene el rango de esta manera:
```java
String[] rangeStr = rangeDirective.toLowerCase().replaceAll("^range:\\s+?bytes=", "").split("-", 2)
```
- El nombre del archivo: Si `DROP` no es enviado primero, el nombre del archivo seleccionado en AwooInstaller sera mandado

Los archivos son mandados casi igual que por usb, la switch manda desde donde se desea leer el archivo y espera que se manden los datos.

## Solicitudes
Las solicitudes son cadenas de texto que se puede recibir de la switch, o mandarlo nosotros. Hay algunas variables que son globales para todas las solicitudes:
- `%EXAMPLE_SERVER%`: El nombre del servidor cliente
- `%CURRENT_DATE%`: La fecha actual de la zona GMT en formato RFC_1123

Las siguientes son las solicitudes que podemos recibir o mandar:

### CODE_200
Se utiliza cuando el servidor manda una solicitud `HEAD`.
- `FILE_SIZE`: El tamano del archivo menos uno 
- `CONTENT_LENGTH`: El tamano del archivo normal.
```
HTTP/1.0 200 OK\r\n
Server: %EXAMPLE_SERVER%\r\n
Date: %CURRENT_DATE%\r\n" 
Content-type: application/octet-stream\r\n" 
Accept-Ranges: bytes\r\n" 
Content-Range: bytes 0-%FILE_SIZE_1%/%CONTENT_LENGTH%\r\n" 
Content-Length: %CONTENT_LENGTH%\r\n" 
Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\r\n\r\n
```
### CODE_206
Se utiliza para mandar partes de la rom seleccionada.
- `%START_POSITION%`: La posicion del cursor del archivo
- `%END_POSITION%`: El final del archivo
- `%FILE_SIZE`: El tamano del archivo
- `%CONTENT_LENGTH%`: Es el final del archivo menos la posicion inicial del archivo mas 1. `%END_POSITION% - %START_POSITION% + 1`

```
HTTP/1.0 206 Partial Content\r\n
Server: %EXAMPLE_SERVER\r\n
Date: %CURRENT_DATE%\r\n
Content-type: application/octet-stream\r\n
Accept-Ranges: bytes\r\n
Content-Range: bytes %START_POSITION%-%END_POSITION%/%FILE_SIZE%\r\n
Content-Length: %CONTENT_LENGTH%\r\n
Last-Modified: Thu, 01 Jan 1970 00:00:00 GMT\r\n\r\n
```
  
### CODE_400
Se manda a la switch cuando el rango de bytes es incorrecto (E.j. si el rango no fue definido)
```
HTTP/1.0 400 invalid range\r\n
Server: %EXAMPLE_SERVER\r\n"
Date: %CURRENT_DATE%\r\n" 
Connection: close\r\n
Content-Type: text/html;charset=utf-8\r\n
Content-Length: 0\r\n\r\n
```
  
### CODE_404
Se manda a la switch cuando un archivo no existe
```
HTTP/1.0 404 Not Found\r\n
Server: %EXAMPLE_SERVER\r\n 
Date: %CURRENT_DATE%\r\n 
Connection: close\r\n
Content-Type: text/html;charset=utf-8\r\n
Content-Length: 0\r\n\r\n
```
  
### CODE_416
Se manda a la switch si el archivo es menor a 500 bytes
```
HTTP/1.0 416 Requested Range Not Satisfiable\r\n
Server: %EXAMPLE_SERVER\r\n 
Date: %CURRENT_DATE%\r\n 
Connection: close\r\n
Content-Type: text/html;charset=utf-8\r\n
Content-Length: 0\r\n\r\n
```