#!/usr/bin/python3

# Keep module imports prior to classes
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys

import classes.Fetcher as Fetcher
import classes.ConfigManager as ConfigManager
from classes.OtaUpdater import OTAUpdater
from classes.Changelog import VERSION
import classes.Screener as Screener
import classes.Utility as Utility
from classes.ColorText import colorText
from classes.CandlePatterns import CandlePatterns
from classes.ParallelProcessing import StockConsumer
from classes.Changelog import VERSION
from alive_progress import alive_bar
import urllib
import numpy as np
import pandas as pd
from datetime import datetime
from time import sleep
from tabulate import tabulate
import multiprocessing
multiprocessing.freeze_support()

# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"

# Constants
np.seterr(divide='ignore', invalid='ignore')

# Global Variabls
screenCounter = None
screenResultsCounter = None
stockDict = None
keyboardInterruptEvent = None
loadedStockData = False
loadCount = 0
maLength = None
newlyListedOnly = False

configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
screener = Screener.tools(configManager)
candlePatterns = CandlePatterns()

def initExecution():
    Utility.tools.clearScreen()
    print(colorText.BOLD + colorText.WARN +
          '[+] Select a menu option:' + colorText.END)
    toggleText = 'T > Toggle between long-term (Default)' + colorText.WARN + ' [Current]'+ colorText.END + ' and Intraday user configuration\n' if not configManager.isIntradayConfig() else 'T > Toggle between long-term (Default) and Intraday' + colorText.WARN + ' [Current]' +  colorText.END + ' user configuration'
    print(colorText.BOLD + '''
     X > Scanners
     S > Strategies
     B > Backtests

     ''' + toggleText + '''
     E > Edit user configuration
     Y > View your user configuration

     U > Check for software update
     H > Help / About Developer
     Z > Exit (Ctrl + C)

    Enter your choice >  (default is ''' + colorText.WARN + 'X > Scanners) ''' + colorText.END
          )
    try:
        menuOption = input(
            colorText.BOLD + colorText.FAIL + '[+] Select option: ')
        print(colorText.END, end='')
        if menuOption == '':
            menuOption = 'X'
        if not menuOption.isnumeric():
            menuOption = menuOption.upper()
            if menuOption == 'Z':
                input(colorText.BOLD + colorText.FAIL +
                    "[+] Press any key to Exit!" + colorText.END)
                sys.exit(0)
            elif menuOption in 'BHUTSEXY':
                Utility.tools.clearScreen()
                return menuOption
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        showOptionErrorMessage()
        return initExecution()
    showOptionErrorMessage()
    return initExecution()

def showOptionErrorMessage():
    print(colorText.BOLD + colorText.FAIL +
              '\n[+] Please enter a valid option & try Again!' + colorText.END)
    sleep(2)
    Utility.tools.clearScreen()

def toggleUserConfig():
    configManager.toggleConfig()
    print(colorText.BOLD + colorText.GREEN +
    '\nConfiguration toggled to duration: ' + str(configManager.duration) + ' and period: ' + str(configManager.period) + colorText.END)
    sleep(3)

# Manage Execution flow
def initScannerExecution():
    global newlyListedOnly
    Utility.tools.clearScreen()
    print(colorText.BOLD + colorText.WARN +
          '[+] Select an Index for Screening:' + colorText.END)
    print(colorText.BOLD + '''
     W > Screen stocks from my own Watchlist
     N > Nifty Prediction using Artifical Intelligence (Use for Gap-Up/Gap-Down/BTST/STBT)
     E > Live Index Scan : 5 EMA for Intraday

     0 > Screen stocks by the stock names (NSE Stock Code)
     1 > Nifty 50               2 > Nifty Next 50           3 > Nifty 100
     4 > Nifty 200              5 > Nifty 500               6 > Nifty Smallcap 50
     7 > Nifty Smallcap 100     8 > Nifty Smallcap 250      9 > Nifty Midcap 50
    10 > Nifty Midcap 100      11 > Nifty Midcap 150       13 > Newly Listed (IPOs in last 2 Year)
    14 > F&O Stocks Only 

     M > Back to the Top/Main menu

    Enter > ''' + colorText.WARN + 'All Stocks (default) ''' + colorText.END
          )
    try:
        tickerOption = input(
            colorText.BOLD + colorText.FAIL + '[+] Select option: ')
        print(colorText.END, end='')
        if tickerOption == '':
            tickerOption = 12
        # elif tickerOption == 'W' or tickerOption == 'w' or tickerOption == 'N' or tickerOption == 'n' or tickerOption == 'E' or tickerOption == 'e':
        elif not tickerOption.isnumeric():
            tickerOption = tickerOption.upper()
            if tickerOption in 'MEN':
                return tickerOption, 0
        else:
            tickerOption = int(tickerOption)
            if(tickerOption < 0 or tickerOption > 14):
                raise ValueError
            elif tickerOption == 13:
                newlyListedOnly = True
                tickerOption = 12
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        print(colorText.BOLD + colorText.FAIL +
              '\n[+] Please enter a valid numeric option & Try Again!' + colorText.END)
        sleep(2)
        Utility.tools.clearScreen()
        return initScannerExecution()

    if tickerOption and tickerOption != 'W':
        Utility.tools.clearScreen()
        print(colorText.BOLD + colorText.WARN +
            '[+] Select a Criterion for Stock Screening: ' + colorText.END)
        print(colorText.BOLD + '''
    0 > Full Screening (Shows Technical Parameters without any criterion)
    1 > Probable Breakouts              2 > Recent Breakouts & Volumes
    3 > Consolidating stocks            4 > Lowest Volume in last 'N'-days (Early Breakout Detection)
    5 > RSI screening                   6 > Reversal Signals
    7 > Stocks making Chart Patterns    8 > CCI outside of the given range
    9 > Volume gainers                 10 > Closing at least 2% up since last 3 days
   11 > Short term bullish stocks      12 > 15 Minute Price & Volume breakout
   13 > Bullish RSI & MACD Intraday    14 > NR4 Day
   15 > 52 week low breakout           16 > 10 days low breakout
   17 > 52 week high breakout          18 > Bullish Aroon Crossover
   19 > MACD Historgram x below 0      20 > RSI entering bullish territory
   21 > Bearish CCI crossover          22 > RSI crosses above 30 and price higher than psar
   23 > Intraday Momentum Build-up     24 > Extremely bullish daily close
   25 > Rising RSI                     26 > Dividend Yield

   42 > Show Last Screened Results

    M > Back to the Top/Main menu
    Z > Exit''' + colorText.END
            )
    try:
        if tickerOption and tickerOption != 'W':
            executeOption = input(
                colorText.BOLD + colorText.FAIL + '[+] Select option: ')
            print(colorText.END, end='')
            if executeOption == '':
                executeOption = 0
            if not executeOption.isnumeric():
                executeOption = executeOption.upper()
            else:
                executeOption = int(executeOption)
                if(executeOption < 0 or executeOption > 44):
                    raise ValueError
        else:
            executeOption = 0
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        print(colorText.BOLD + colorText.FAIL +
              '\n[+] Please enter a valid numeric option & Try Again!' + colorText.END)
        sleep(2)
        Utility.tools.clearScreen()
        return initScannerExecution()
    return tickerOption, executeOption

# Main function
def main(testing=False, testBuild=False, downloadOnly=False):
    global screenCounter, screenResultsCounter, stockDict, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly
    screenCounter = multiprocessing.Value('i', 1)
    screenResultsCounter = multiprocessing.Value('i', 0)
    keyboardInterruptEvent = multiprocessing.Manager().Event()

    if stockDict is None:
        stockDict = multiprocessing.Manager().dict()
        loadCount = 0

    minRSI = 0
    maxRSI = 100
    insideBarToLookback = 7
    respChartPattern = 1
    daysForLowestVolume = 30
    reversalOption = None

    screenResults = pd.DataFrame(columns=[
                                 'Stock', 'Consolidating', 'Breaking-Out', 'LTP', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern', 'CCI'])
    saveResults = pd.DataFrame(columns=[
                               'Stock', 'Consolidating', 'Breaking-Out', 'LTP', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern', 'CCI'])

    
    if testBuild:
        tickerOption, executeOption = 1, 0
    elif downloadOnly:
        tickerOption, executeOption = 12, 2
    else:
        try:
            menuOption = initExecution()
            if menuOption == 'H':
                Utility.tools.showDevInfo()
                main()
            elif menuOption == 'U':
                OTAUpdater.checkForUpdate(getProxyServer(), VERSION)
                main()
            elif menuOption == 'T':
                toggleUserConfig()
                main()
            elif menuOption == 'E':
                configManager.setConfig(ConfigManager.parser)
                main()
            elif menuOption == 'X':
                tickerOption, executeOption = initScannerExecution()
            elif menuOption == 'Y':
                configManager.showConfigFile()
                main()
            else:
                print('Work in progress! Try selecting a different option.')
                sleep(3)
                main()
        except KeyboardInterrupt:
            input(colorText.BOLD + colorText.FAIL +
                "[+] Press any key to Exit!" + colorText.END)
            sys.exit(0)
    volumeRatio = configManager.volumeRatio
    if executeOption == 4:
        try:
            daysForLowestVolume = int(input(colorText.BOLD + colorText.WARN +
                                            '\n[+] The Volume should be lowest since last how many candles? '))
        except ValueError:
            print(colorText.END)
            print(colorText.BOLD + colorText.FAIL +
                  '[+] Error: Non-numeric value entered! Screening aborted.' + colorText.END)
            input('')
            main()
        print(colorText.END)
    if executeOption == 5:
        minRSI, maxRSI = Utility.tools.promptRSIValues()
        if (not minRSI and not maxRSI):
            print(colorText.BOLD + colorText.FAIL +
                  '\n[+] Error: Invalid values for RSI! Values should be in range of 0 to 100. Screening aborted.' + colorText.END)
            input('')
            main()
    if executeOption == 6:
        reversalOption, maLength = Utility.tools.promptReversalScreening()
        if reversalOption is None or reversalOption == 0:
            main()
    if executeOption == 7:
        respChartPattern, insideBarToLookback = Utility.tools.promptChartPatterns()
        if insideBarToLookback is None:
            main()
    if executeOption == 8:
        minRSI, maxRSI = Utility.tools.promptCCIValues()
        if (not minRSI and not maxRSI):
            print(colorText.BOLD + colorText.FAIL +
                  '\n[+] Error: Invalid values for CCI! Values should be in range of -300 to 500. Screening aborted.' + colorText.END)
            input('')
            main()
    if executeOption == 9:
        volumeRatio = Utility.tools.promptVolumeMultiplier()
        if (volumeRatio <= 0):
            print(colorText.BOLD + colorText.FAIL +
                  '\n[+] Error: Invalid values for Volume Ratio! Value should be a positive number. Screening aborted.' + colorText.END)
            input('')
            main()
        else:
            configManager.volumeRatio = float(volumeRatio)
    if executeOption == 42:
        Utility.tools.getLastScreenedResults()
        main()
    if tickerOption == 'M' or executeOption == 'M':
        main()
        return
    if executeOption == 'Z':
        input(colorText.BOLD + colorText.FAIL +
              "[+] Press any key to Exit!" + colorText.END)
        sys.exit(0)
    if executeOption >= 12 and executeOption <= 39:
        print(colorText.BOLD + colorText.FAIL + '\n[+] Error: Option 12 to 39 Not implemented yet! Press any key to continue.' + colorText.END) 
        input('')
        main()
    if (not str(tickerOption).isnumeric() and tickerOption in 'WEMNZ') or (str(tickerOption).isnumeric() and (tickerOption >= 0 and tickerOption < 15)):
        configManager.getConfig(ConfigManager.parser)
        try:
            if tickerOption == 'W':
                listStockCodes = fetcher.fetchWatchlist()
                if listStockCodes is None:
                    input(colorText.BOLD + colorText.FAIL +
                          f'[+] Create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!' + colorText.END)
                    sys.exit(0)
            elif tickerOption == 'N':
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
                prediction = screener.getNiftyPrediction(
                    data=fetcher.fetchLatestNiftyDaily(proxyServer=proxyServer), 
                    proxyServer=proxyServer
                )
                input('\nPress any key to Continue...\n')
                return
            elif tickerOption == 'M':
                main()
                return
            elif tickerOption == 'Z':
                input(colorText.BOLD + colorText.FAIL + "[+] Press any key to Exit!" + colorText.END)
                sys.exit(0)
            elif tickerOption == 'E':
                result_df = pd.DataFrame(columns=['Time','Stock/Index','Action','SL','Target','R:R'])
                last_signal = {}
                first_scan = True
                result_df = screener.monitorFiveEma(        # Dummy scan to avoid blank table on 1st scan
                        proxyServer=proxyServer,
                        fetcher=fetcher,
                        result_df=result_df,
                        last_signal=last_signal
                    )
                try:
                    while True:
                        Utility.tools.clearScreen()
                        last_result_len = len(result_df)
                        result_df = screener.monitorFiveEma(
                            proxyServer=proxyServer,
                            fetcher=fetcher,
                            result_df=result_df,
                            last_signal=last_signal
                        )
                        print(colorText.BOLD + colorText.WARN + '[+] 5-EMA : Live Intraday Scanner \t' + colorText.END + colorText.FAIL + f'Last Scanned: {datetime.now().strftime("%H:%M:%S")}\n' + colorText.END)
                        print(tabulate(result_df, headers='keys', tablefmt='psql'))
                        print('\nPress Ctrl+C to exit.')
                        if len(result_df) != last_result_len and not first_scan:
                            Utility.tools.alertSound(beeps=5)
                        sleep(60)
                        first_scan = False
                except KeyboardInterrupt:
                    input('\nPress any key to Continue...\n')
                    return
            else:
                listStockCodes = fetcher.fetchStockCodes(tickerOption, proxyServer=proxyServer)
        except urllib.error.URLError:
            print(colorText.BOLD + colorText.FAIL +
                  "\n\n[+] Oops! It looks like you don't have an Internet connectivity at the moment! Press any key to exit!" + colorText.END)
            input('')
            sys.exit(0)

        if not Utility.tools.isTradingTime() and configManager.cacheEnabled and not loadedStockData and not testing:
            Utility.tools.loadStockData(stockDict, configManager, proxyServer)
            loadedStockData = True
        loadCount = len(stockDict)

        print(colorText.BOLD + colorText.WARN +
              "[+] Starting Stock Screening.. Press Ctrl+C to stop!\n")

        items = [(executeOption, reversalOption, maLength, daysForLowestVolume, minRSI, maxRSI, respChartPattern, insideBarToLookback, len(listStockCodes),
                  configManager, fetcher, screener, candlePatterns, stock, newlyListedOnly, downloadOnly, volumeRatio, testBuild)
                 for stock in listStockCodes]

        tasks_queue = multiprocessing.JoinableQueue()
        results_queue = multiprocessing.Queue()

        totalConsumers = multiprocessing.cpu_count()
        if totalConsumers == 1:
            totalConsumers = 2      # This is required for single core machine
        if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
            totalConsumers -= 1
        consumers = [StockConsumer(tasks_queue, results_queue, screenCounter, screenResultsCounter, stockDict, proxyServer, keyboardInterruptEvent)
                     for _ in range(totalConsumers)]

        for worker in consumers:
            worker.daemon = True
            worker.start()

        if testing or testBuild:
            for item in items:
                tasks_queue.put(item)
                result = results_queue.get()
                if result is not None:
                    screenResults = screenResults.append(
                        result[0], ignore_index=True)
                    saveResults = saveResults.append(
                        result[1], ignore_index=True)
                    if testing or (testBuild and len(screenResults) > 2):
                        break
        else:
            for item in items:
                tasks_queue.put(item)
            # Append exit signal for each process indicated by None
            for _ in range(multiprocessing.cpu_count()):
                tasks_queue.put(None)
            try:
                numStocks = len(listStockCodes)
                print(colorText.END+colorText.BOLD)
                bar, spinner = Utility.tools.getProgressbarStyle()
                with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
                    while numStocks:
                        result = results_queue.get()
                        if result is not None:
                            screenResults = screenResults.append(
                                result[0], ignore_index=True)
                            saveResults = saveResults.append(
                                result[1], ignore_index=True)
                        numStocks -= 1
                        progressbar.text(colorText.BOLD + colorText.GREEN +
                                         f'Found {screenResultsCounter.value} Stocks' + colorText.END)
                        progressbar()
            except KeyboardInterrupt:
                try:
                    keyboardInterruptEvent.set()
                except KeyboardInterrupt:
                    pass
                print(colorText.BOLD + colorText.FAIL +
                      "\n[+] Terminating Script, Please wait..." + colorText.END)
                for worker in consumers:
                    worker.terminate()

        print(colorText.END)
        # Exit all processes. Without this, it threw error in next screening session
        for worker in consumers:
            try:
                worker.terminate()
            except OSError as e:
                if e.winerror == 5:
                    pass

        # Flush the queue so depending processes will end
        from queue import Empty
        while True:
            try:
                _ = tasks_queue.get(False)
            except Exception as e:
                break
        # Publish to gSheet with https://github.com/burnash/gspread 
        screenResults.sort_values(by=['Volume'], ascending=False, inplace=True)
        saveResults.sort_values(by=['Stock'], ascending=True, inplace=True)
        screenResults.set_index('Stock', inplace=True)
        saveResults.set_index('Stock', inplace=True)
        screenResults.rename(
            columns={
                'Trend': f'Trend ({configManager.daysToLookback}Periods)',
                'Breaking-Out': f'Breakout ({configManager.daysToLookback}Periods)',
                'LTP': 'LTP (% Chng)'
            },
            inplace=True
        )
        saveResults.rename(
            columns={
                'Trend': f'Trend ({configManager.daysToLookback}Periods)',
                'Breaking-Out': f'Breakout ({configManager.daysToLookback}Periods)',
            },
            inplace=True
        )
        print(tabulate(screenResults, headers='keys', tablefmt='psql'))

        print(colorText.BOLD + colorText.GREEN +
                  f"[+] Found {len(screenResults)} Stocks." + colorText.END)
        if configManager.cacheEnabled and not Utility.tools.isTradingTime() and not testing:
            print(colorText.BOLD + colorText.GREEN +
                  "[+] Caching Stock Data for future use, Please Wait... " + colorText.END, end='')
            Utility.tools.saveStockData(
                stockDict, configManager, loadCount)

        Utility.tools.setLastScreenedResults(screenResults)
        if not testBuild and not downloadOnly:
            Utility.tools.promptSaveResults(saveResults)
            print(colorText.BOLD + colorText.WARN +
                "[+] Note: Trend calculation is based on number of days recent to screen as per your configuration." + colorText.END)
            print(colorText.BOLD + colorText.GREEN +
                "[+] Screening Completed! Press Enter to Continue.." + colorText.END)
            input('')
        newlyListedOnly = False

def getProxyServer():
    # Get system wide proxy for networking
    try:
        proxyServer = urllib.request.getproxies()['http']
    except KeyError:
        proxyServer = ""
    return proxyServer

proxyServer = getProxyServer()

# https://chartink.com/screener/15-min-price-volume-breakout
# https://chartink.com/screener/15min-volume-breakout
