# Overview
This is the CSUN team builder application, created by Mike Fuson. It is used to randomzize teams for our Ultimate Frisbee leagues.

## Needed Python Modules
The following modules are needed to build the application. These are not needed if you are just running the application.

- pandas
- PyInstaller

Additionally, python-tk is needed for GUI implementations.

## Windows Install Command
python -m PyInstaller --noconsole --onefile --icon=frisbee-24.ico --add-data "frisbee-24.ico;." --name TeamBuilder  main.py

## MacOS Install Command
python -m PyInstaller --noconsole --onefile --icon=frisbee-24.icns --add-data "frisbee-24.icns:." --name TeamBuilder  main.py