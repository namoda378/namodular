# Namoutils/ex6 - Namodular

Namodular is a python script that started as a sublime text 3 plugin. It's main purpose is to help the code reflect project folder structures  

## Updates

### 190212
- low reusablity issue of forin cmd lines and printable formats 
	- need to make root based path manipulation easier 
- forin command blocks with r tag should be updated when any of offsprings are changed 
	- set **-r** tag as default, updated when any of the offspring structure changes
### 190225
- support for other line comment syntax added, default as lua comment syntax. Should use other language, user should configure what string starts a line comment in config file under _namodular directory
