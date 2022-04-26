# ozon_parser
__Async parser of reviews for OZON.ru__

The entire result is saved in the csv table, which is located in the __csv_result__ folder.

If the option to save images from reviews is enabled in the configuration, they are saved in the __images__ folder.

Each product and review has its own unique identifier, with which the necessary photos are attached to them.

--------------------------------------

In the __config.json__ you can change the config:

+ Image loading mode (0/1)
+ Request delay (type: int/float)
+ Proxy (login:pass@ip:port)

To start, use __main.py__. 
Don't forget to install the necessary libraries from the file __requirements.txt__ .
