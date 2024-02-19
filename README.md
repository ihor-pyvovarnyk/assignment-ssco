# Assignment

Create virtualenv and activate it:
```bash
make venv  
make activate
```

Initialize local database:
```bash
make initdb
```

Run local server
```bash
make run
```

Import files:
```bash
python manage.py import_file -f $PATH_TO_FILE_1 $PATH_TO_FILE_2 ...
```