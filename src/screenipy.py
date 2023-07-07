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
from time import sleep

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument('-t', '--testbuild', action='store_true', help='Run in test-build mode', required=False)
argParser.add_argument('-p', '--prodbuild', action='store_true', help='Run in production-build mode', required=False)
argParser.add_argument('-d', '--download', action='store_true', help='Only Download Stock data in .pkl file', required=False)
argParser.add_argument('-o', '--options', help='Pass selected options in the <MainMenu>:<SubMenu>:<SubMenu>... format. For example, 12:6:3', required=False)
argParser.add_argument('-a', '--answerdefault', help='Pass answer to default yestions. Example Y, N', required=False)
argParser.add_argument('-c', '--croninterval', help='Pass interval in seconds to wait before the program is run again with same parameters', required=False)
argParser.add_argument('-v', action='store_true')        # Dummy Arg for pytest -v
args = argParser.parse_args()

configManager = ConfigManager.tools()

if __name__ == "__main__":
    if sys.platform.startswith('darwin'):
        multiprocessing.set_start_method('fork')

    Utility.tools.clearScreen()
    if not configManager.checkConfigFile():
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    if args.testbuild:
        print(colorText.BOLD + colorText.FAIL +"[+] Started in TestBuild mode!" + colorText.END)
        main(testBuild=True, prodbuild=args.prodbuild, startupoptions=args.options, defaultConsoleAnswer=args.answerdefault)
    elif args.download:
        print(colorText.BOLD + colorText.FAIL +"[+] Download ONLY mode! Stocks will not be screened!" + colorText.END)
        main(downloadOnly=True, prodbuild=args.prodbuild, startupoptions=args.options, defaultConsoleAnswer=args.answerdefault)
    else:
        try:
            while True:
                # main(prodbuild=args.prodbuild, startupoptions=args.options, defaultConsoleAnswer=args.answerdefault)
                if args.croninterval is not None and str(args.croninterval).isnumeric():
                    sleepUntilNextExecution = not Utility.tools.isTradingTime()
                    while sleepUntilNextExecution:
                        print(colorText.BOLD + colorText.FAIL + ("SecondsAfterClosingTime[%d] SecondsBeforeMarketOpen [%d]. Next run at [%s]" % (
                            int(Utility.tools.secondsAfterCloseTime()), int(Utility.tools.secondsBeforeOpenTime()),str(Utility.tools.nextRunAtDateTime(bufferSeconds=3600, cronWaitSeconds=int(args.croninterval))))) + colorText.END)
                        if (Utility.tools.secondsAfterCloseTime() >= 3600) and (Utility.tools.secondsAfterCloseTime() <= (3600 + 1.5 * int(args.croninterval))):
                            sleepUntilNextExecution = False
                        if (Utility.tools.secondsBeforeOpenTime() <= -3600) and (Utility.tools.secondsBeforeOpenTime() >= (-3600 - 1.5 * int(args.croninterval))):
                            sleepUntilNextExecution = False
                        sleep(int(args.croninterval))
                    print(colorText.BOLD + colorText.GREEN +
                      "=> Going to fetch again!" + colorText.END, end='\r', flush=True)
                    sleep(5)
                main(prodbuild=args.prodbuild, startupoptions=args.options, defaultConsoleAnswer=args.answerdefault)
        except Exception as e:
            raise e
            # if isDevVersion == OTAUpdater.developmentVersion:
            #     raise(e)
            # input(colorText.BOLD + colorText.FAIL +
            #     "[+] Press any key to Exit!" + colorText.END)
            # sys.exit(0)
