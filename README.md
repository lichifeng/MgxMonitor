# Mgxhub
**Mgxhub** is a Age of Empires II records processor with web apis.    
Run in docker and use /docs or /redoc to see the api documentation.   

# How to deploy
1. Copy `config-sample.ini` to local.
2. Remove unnecessary lines and change the values to your own.
3. Run the docker container with environment variable `MGXHUB_CONFIG` pointing to the file.
4. Communicate with the api.