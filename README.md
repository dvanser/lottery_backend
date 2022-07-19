## lottery back-end

##### NOTE
For all listed below commands use your versions of python and pip

## Project setup

* Create virtual environment in project root directory:  
`sudo python3.9 -m venv venv`
* Activate virtual env(from project root dir):  
`. venv/bin/activate`
* Install dependencies(from root folder):  
`sudo pip3.9 install -r requirements.txt`
* To deactivate virtual env run:  
`deactivate`  
* Database creation(also can be used on db structure change). Inside root dir run(when venv activated):  
`python3.9`  
`from lottery import app`  
`from lottery.db import db`  
`db.init_app(app)`  
`with app.app_context():`  
`db.create_all()`  


##### NOTE
Install new dependencies only when you in virtual env. When all dependencies installed run(from project root dir):  
`pip3.9 freeze > requirements.txt`

## Run app
* Set flask app variable:  
`export FLASK_APP=lottery`
* Run app:  
`flask run`

## Localization
Flask-Babel is used for i18n and l10n support https://flask-babel.tkte.ch/

* Create babel.cfg inside root dir with following content: 
```
[python: **.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
```

* First you need to mark all the strings you want to translate in your application with ```gettext()```

* To extract all strings execute:
```
pybabel extract -F babel.cfg -o messages.pot .
```

* To create translation execute(in this case for en language):
```
pybabel init -i messages.pot -d translations -l en
```

* Edit generated file by adding translation, file is located at: 
```
translations/{$language}/LC_MESSAGES/messages.po
```

* To compile the translations for use execute: 
```
pybabel compile -d translations
```

* In case translation changed, extract strings, execute this command, updated translations (remove "fuzzy" in case it is present), compile (in case labels not changed just execute compile):
```
pybabel update -i messages.pot -d translations
```

