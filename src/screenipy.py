#!/usr/bin/python3

# Pyinstaller compile Windows: pyinstaller --onefile --icon=src\icon.ico src\screenipy.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=src/icon.ico src/screenipy.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress

# Keep module imports prior to classes
import os
import sys
import multiprocessing
import argparse

import classes.ConfigManager as ConfigManager
import classes.Utility as Utility
from classes.ColorText import colorText
from globals import main, getProxyServer

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument('-t', '--testbuild', action='store_true', help='Run in test-build mode', required=False)
argParser.add_argument('-d', '--download', action='store_true', help='Only Download Stock data in .pkl file', required=False)
argParser.add_argument('-o', '--options', action='store_true', help='Pass selected options in the <MainMenu>:<SubMenu>:<SubMenu>... format. For example, 12:6:3', required=False)
argParser.add_argument('-v', action='store_true')        # Dummy Arg for pytest -v
args = argParser.parse_args()

configManager = ConfigManager.tools()

if __name__ == "__main__":
    if sys.platform.startswith('darwin'):
        multiprocessing.set_start_method('forkserver')

    Utility.tools.clearScreen()
    if not configManager.checkConfigFile():
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    if args.testbuild:
        print(colorText.BOLD + colorText.FAIL +"[+] Started in TestBuild mode!" + colorText.END)
        main(testBuild=True)
    elif args.download:
        print(colorText.BOLD + colorText.FAIL +"[+] Download ONLY mode! Stocks will not be screened!" + colorText.END)
        main(downloadOnly=True)
    else:
        try:
            while True:
                main()
        except Exception as e:
            raise e
            # if isDevVersion == OTAUpdater.developmentVersion:
            #     raise(e)
            # input(colorText.BOLD + colorText.FAIL +
            #     "[+] Press any key to Exit!" + colorText.END)
            # sys.exit(0)
