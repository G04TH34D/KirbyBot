
'''
    \\ \\ KIRBY BOT // //
'''

'''
    A crypto trading app that works off of indicator values to make trading decisions.This bot will commit to 1 trading 
    stragey. The stragey is to have a buy signal counter. This counter goes off everytime this condition is met:

        RSI < 35 and current_price < Lower_Bollinger_Band and Last_candle_out_of_band

        Our bots strategy is to enter a trade with a fixed percentage of USD hodlings, sell 25% at a time for profit or
        loss at set levels. 

        The stop loss levels are:
        25% of initial position size volume at 8% loss
        25% of initial position size volume at 10% loss
        25% of initial position size volume at 12.5% loss
        25% of initial position size volume at 15% loss

        The take profit levels are:
        20% of initial position size volume at 1.6% profit
        20% of initial position size volume at 2.5% profit
        20% of initial position size volume at 5% profit
        20% of initial position size volume at 7.5% profit
        20% of initial position size volume at 10% profit

        Buy condition:
        RSI < 30
        Last candle closed < Lower bollinger band level
        current price is < Lower bollinger band level

        If all of these are true the bot will increment the buy signal variable. If the buy signal variable is at 3
        it will initiate a buy. The buy signal will be reset to 0 and the bot will have entered a position.

        Sell Condition:
            the bot will use the values placed above to decide if it should sell.

        Since the bot will check every 30 seconds we will need to verify that the buy signal has not been incremented
        during the current candle. This will prevent the bot from incrementing the signal multiple times in one candle 
        frame.  


    It will keep to the stragey and hold no more than 5 positions. The bot will always trade with a fixed 
    percentage during live Testing. As a test the bot will have a limited menu and display. 

    The main function of this application is to be able to demonstrate data handling in a live application environment.

    Current project:

            - Debug and Logging - 
            Setup an extensive debugging and logging method initially before incorporating any further functions.

            - Develop loop -
            Create the framework for how the app runs. 

                -Initialize state-
                    The main loop or state runs through validation testing and state testing.
                    Positional states/arguments are chosen if not loaded from previous state
                    - Load State - 
                        Load positional information from a json file when the bot initiates. 


                -Check time-
                    Time is checked to see where state last left off and where current data is.
                    This will run to ensure 
                        -If current_time > data.state.time:
                            fetch_data
                            save 

                -Poll API-
                    Make requests in a way not to time out the requests to aquire needed data.

                    -Handle Data-
                        What data do we need?    

                        -Poll API
                            - OHLC data
                                Pandas Dataframe. Can be variable and read from file. 
                                Will have to be passed through multiple agruments 

                                OHLC Data will 

                        -Poll API        
                            - Current bid
                                Can be variable and read from file. 
                        -Poll API        
                            - Current ask
                                Can be variable and read from file.
                        -Poll API         
                            - Current price
                                Can be variable and read from file.

                        -Poll API
                            - Update OHLC data.
                                Manage OHLC data validation during live running.
                                This could be DB, memory, or state. 
                                check the OHLC, validate new closed candle and append it while popping the oldest data
                                if in memory. If DB then restructure.

                        -WebSocket-
                            Look into websocket for API outages and how to handle that data. Later planned.

            -Define Indicators-
                Take data and process it into indicators. Indicators should be a class start with functions and move
                to class of indicators that can run off of data variables that could be delivered via menu.

                - RSI -
                    *****

                - Bollinger Bands -
                    *****

                    Store indicators in a variable to use in real time. Indicators should always be generated from the 
                    most current data.


            -Verify the ability to buy/sell-
                Create functions that can buy and sell and store necessary values for profit and loss. 
                    Test buying/selling and digest messages correctly.

            -Implement trade logic-
                Verify logic is triggering correctly based off of trading strategy. 


            -Positional state handling-
                The bot will need a state json file that will contain:

                - pair
                - interval
                - trade % of usd value
                - position data 
                    - Time of opening position
                    - Buy price 
                    - Initial volume
                    - Profit/Stop loss targets.
                - winning trades
                - lossing trades
                - Current profit/loss
                - Estimated taxes owed


            -Menu System-
                The system will be designed so that when pressing enter we enter command mode.       
                Command mode will allow the user to select a function to run
                Functions:
                    - Open new position
                    - Close current position
                    - Change intervals
                    - Change trading pair
                    - Change trading percentage
                When not in command mode the bot will display a dashboard that will display trading information.

            -Dashboard-
                 Draws live data in an easy to read dashboard that displays positional data and current state    


                -Project Leg Close Out-
                
    This has been the first leg of code to try and develope the MVP for creating the first WBS of our project design.
    
    Goals - 
    
        Create logging/debug - Create multiple functions that can store log files and handling debugging. 
            - Create stored logging for itteration to save to log file when performed action is ran. 

        Create function to Initialize bot state
            - When initilized if state is there have bot load state if no response/input after 30 seconds
        
        Create function to save state 
            -
        
        Create function to load API - API keys will be stored in a text file external of application. We then load 
        the api keys and a variable to use when making API requests
            -
            
        Create API calls for data - Create a wrapper to request information from api.
            -
        
        Create position refrence ID's at time of position creation to verify position sells
            - Positions should have unique ID's that can be referenced when sells occur to verify state.
            
        Create expected values validation 
            - Create a function to check for expected values in state file after actions are performed. 
        
            

        
    


'''

import threading
import time
import logging
import glob
import json
import pandas as pd
import time
import os
from datetime import datetime
from inputimeout import inputimeout, TimeoutOccurred
import krakenex
from pykrakenapi import KrakenAPI
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
import traceback


# Create a logger setup function to be called once during the bot's initialization
def setup_logger():
    # Create or get the existing logger
    logger = logging.getLogger('CryptoBotLogger')
    logger.setLevel(logging.DEBUG)  # Set the logger to the lowest level to capture all messages

    # Clear existing handlers to avoid duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Define a custom log level for performed actions
    global PERFORMED_ACTION
    PERFORMED_ACTION = 25  # Custom level between INFO and WARNING
    logging.addLevelName(PERFORMED_ACTION, "PERFORMED_ACTION")

    # Create a file handler for writing log messages to a file
    log_filename = f"trading_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)  # Log only INFO and above to the file
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Create a console handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG) if debug_mode else console_handler.setLevel(logging.INFO)   # Log DEBUG and above to the console
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

# Globals

debug_mode = True  # Global debug mode flag
logger = setup_logger()  # Logger
stop_signal = threading.Event()  # Event to signal the trading logic to stop
last_public_api_call_time = 0
public_api_call_interval = 1  # Seconds between public API calls (adjust based on Kraken's rate limits)
last_ohlc_update_time = None
log_filename = f"trading_bot_{datetime.now().strftime('%Y-%m-%d')}.log"  # Define log_filename globally
is_handling_error = False
last_error_info = {
    'message': '',
    'timestamp': 0
}

def make_api_call(api_func, *args, **kwargs):
    """
    Wrapper function to make API calls with rate-limiting, retry logic, and logging.

    Args:
        api_func (function): The Kraken API function to call (e.g., api.query_public).
        *args: Positional arguments for the API function.
        **kwargs: Keyword arguments for the API function.

    Returns:
        dict or DataFrame: The result of the API call, or None if it fails.
    """
    global last_public_api_call_time
    max_retries = 3  # Number of retries if the rate limit is exceeded
    retry_wait_time = 5  # Wait time in seconds before retrying after hitting the rate limit

    for attempt in range(max_retries):
        try:
            # Calculate the time since the last public API call
            time_since_last_call = time.time() - last_public_api_call_time

            # If the time since the last call is less than the interval, sleep
            if time_since_last_call < public_api_call_interval:
                sleep_time = public_api_call_interval - time_since_last_call
                log_message('debug', f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)

            # Make the actual API call
            result = api_func(*args, **kwargs)

            # Update the last API call time after the successful call
            last_public_api_call_time = time.time()

            # Check for errors in the response
            if isinstance(result, dict) and 'error' in result and result['error']:
                log_message('error', f"API error: {result['error']}")
                raise Exception(f"API error: {result['error']}")

            # Handle DataFrame results directly
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    log_message('error', "API returned an empty DataFrame.")
                    raise Exception("API returned an empty DataFrame.")
                return result  # Return the DataFrame

            return result  # Return the successful result (dict or otherwise)

        except Exception as e:
            log_message('error', f"Error on API call attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                log_message('debug', f"Retrying in {retry_wait_time} seconds...")
                time.sleep(retry_wait_time)
            else:
                log_message('error', f"Max retries reached for API function {api_func.__name__}.")
                return None

# Function to log
def log_message(level, message):
    """Logs a message with a specific level directly to the logger."""
    global is_handling_error

    # Avoid recursion if already handling an error
    if is_handling_error and level == 'error':
        return

    # Determine the logging level
    level = level.lower()
    try:
        if level == 'debug':
            logger.debug(message)
            if debug_mode:  # Print debug messages if debug mode is enabled
                print(f"DEBUG: {message}")
        elif level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            is_handling_error = True  # Set the flag to indicate error handling is active
            logger.error(message, exc_info=True)
            stack_trace = traceback.format_exc()
            send_error_email(f"Error in Trading Bot", message, stack_trace)
            is_handling_error = False  # Reset the flag after handling
        elif level == 'critical':
            logger.critical(message)
        elif level == 'performed_action':
            logger.log(PERFORMED_ACTION, message)
        else:
            logger.info(message)
    except Exception as e:
        # Avoid any further logging to prevent recursion
        if not is_handling_error:
            is_handling_error = True
            print(f"Critical logging failure: {e}")
            is_handling_error = False

# Debug toggle function
def toggle_debug():
    global debug_mode
    debug_mode = not debug_mode
    print(f"Debug mode is now {'ON' if debug_mode else 'OFF'}")


# Function to send an email
def send_email(subject, message, to_email="email@email.com"):
    """Sends an email notification."""
    try:
        # Email configuration
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        sender_email = 'email@email.com'
        sender_password = 'apppassword'  # App-specific password

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the main message body
        msg.attach(MIMEText(message, 'plain'))

        # Read the contents of the log file and attach it to the email
        try:
            with open(log_filename, 'r') as log_file:
                log_contents = log_file.read()
                msg.attach(MIMEText(f"\n\n--- Log Contents ---\n{log_contents}", 'plain'))
            logger.debug(f"Log contents attached to email: {log_filename}")
        except FileNotFoundError:
            logger.warning(f"Log file not found: {log_filename}")
        except Exception as e:
            logger.error(f"Error reading log file: {e}")

        # Connect to the SMTP server and send the email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        logger.debug(f"Email sent to {to_email} with subject: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        
# Function to send an email when an error occurs
def send_error_email(subject, message, error):
    """Sends an error email notification with the stack trace included."""
    global last_error_info, is_handling_error

    current_time = time.time()
    min_interval = 600  # Minimum interval in seconds between emails for the same error (e.g., 10 minutes)

    if is_handling_error:
        return  # Avoid recursion

    try:
        is_handling_error = True  # Set the flag to indicate error handling is active

        # Generate the stack trace if `error` is an instance of `BaseException`
        if isinstance(error, BaseException):
            stack_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        else:
            stack_trace = str(error)

        full_message = f"{message}\n\nStack Trace:\n{stack_trace}"

        # Check if this error is the same as the last one and if the minimum interval has passed
        if error != last_error_info['message'] or (current_time - last_error_info['timestamp'] > min_interval):
            # Update the last error info
            last_error_info['message'] = str(error)  # Store the error message for comparison
            last_error_info['timestamp'] = current_time

            # Send the email and handle potential exceptions
            send_email(subject, full_message)
            logger.debug(f"Error email sent for error: {error}")

    except Exception as e:
        # Log the failure to send an error email without triggering another email
        print(f"Failed to send error email: {e}")
    finally:
        is_handling_error = False  # Reset the flag after handling
# Function to send an email when an action occurs
def send_action_email(subject, message):
    """Sends an action email notification."""
    send_email(subject, message)
    log_message('debug', f"Action email sent with subject: {subject}")
    log_message('info', f"Action email sent with subject: {subject}")

def read_api_keys(file_path):
    log_message('debug', f"Attempting to read API keys from {file_path}...")  # Debug statement indicating the function start
    try:
        with open(file_path, 'r') as file:
            log_message('debug', "File opened successfully, reading lines...")  # Debug after successfully opening the file
            lines = file.readlines()
            api_key = lines[0].strip()
            api_secret = lines[1].strip()

        log_message('debug', "API keys read successfully.")  # Debug after reading the API keys
        return api_key, api_secret
    except Exception as e:
        log_message('debug', f"Error loading API keys: {e}")  # Debug when an exception occurs
        log_message('error', f"Error loading API keys: {e}")
        raise

# Initialize API using keys from a file
api_key, api_secret = read_api_keys('kraken.key')
api = krakenex.API(api_key, api_secret)
k = KrakenAPI(api)

def get_validated_pair(api):
    log_message('debug', "Starting trading pair validation...")  # Debug: Function start
    while True:
        trading_pair = input \
            ("Please enter the trading pair you want to use (e.g., ADAUSD): ").strip().upper()  # Removed the '/' expectation
        log_message('debug', f"User input trading pair: {trading_pair}")  # Debug: User input

        try:
            log_message('debug', f"Querying Kraken API for trading pair: {trading_pair}")  # Debug: API query start
            # Use the krakenex.API object (api) to query public data
            ticker_info = api.query_public('Ticker', {'pair': trading_pair})

            if ticker_info.get('result'):
                validated_pair = trading_pair
                log_message('debug', f"Trading pair validated successfully: {validated_pair}")  # Debug: Successful validation
                print(f"Validated trading pair {trading_pair}.")
                logging.info(f"Validated trading pair: {validated_pair}")
                return validated_pair
            else:
                log_message('debug', f"Invalid trading pair: {trading_pair}, prompting user again.")  # Debug: Invalid pair
                print(f"Invalid trading pair {trading_pair}. Please try again.")
        except Exception as e:
            log_message('debug', f"Error validating trading pair: {e}")  # Debug: Exception handling
            print(f"Error validating trading pair: {e}")
            logging.error(f"Error validating trading pair: {e}")

def get_validated_interval():
    log_message('debug', "Starting interval validation...")  # Debug: Function start
    while True:
        try:
            interval_input = input("Please enter the interval (in minutes, e.g., 1, 5, 15): ").strip()
            log_message('debug', f"User input interval: {interval_input}")  # Debug: User input
            interval = int(interval_input)

            if interval > 0:
                log_message('debug', f"Validated interval: {interval} minutes.")  # Debug: Successful validation
                logging.info(f"Selected interval: {interval} minutes.")
                return interval
            else:
                log_message('debug', "Invalid interval: Must be a positive integer.")  # Debug: Invalid interval
                print("Interval must be a positive integer. Please try again.")
        except ValueError:
            log_message('debug', f"Invalid input detected: {interval_input}")  # Debug: Exception handling
            print("Invalid input. Please enter a positive integer.")

def save_state(pair, state):
    """Save the current trading state to a JSON file."""
    try:
        # Make a copy of the state without non-serializable objects
        state_copy = state.copy()

        # Remove OHLC data before saving the state
        if 'ohlc_data' in state_copy:
            del state_copy['ohlc_data']

        # Save the remaining state to a file
        file_name = f'trade_state_{pair.replace("/", "_")}.json'
        with open(file_name, 'w') as file:
            json.dump(state_copy, file, indent=4)

        logging.info(f"State saved successfully for {pair}.")
    except Exception as e:
        logging.error(f"Error saving state: {e}")
        log_message('debug', f"Error saving state: {e}")  # Debug: Exception handling

def save_and_verify_state(pair, state):
    """Save the state and verify if it has been saved correctly."""
    try:
        # Save the state
        save_state(pair, state)

        # Reload the saved state
        with open(f'trade_state_{pair.replace("/", "_")}.json', 'r') as file:
            loaded_state = json.load(file)

        # Normalize both states for comparison
        #normalized_state = normalize_state(state)
        #normalized_loaded_state = normalize_state(loaded_state)

        # Compare loaded state with the current state
        #if normalized_state != normalized_loaded_state:
        #    log_message('error', "Discrepancy detected between saved and in-memory state after buy.")
        #    log_message('debug', f"Expected State: {normalized_state}")
        #    log_message('debug', f"Loaded State: {normalized_loaded_state}")

    except Exception as e:
        log_message('error', f"Error during save and verify state: {e}")

def normalize_state(state):
    """Normalize the state for comparison."""
    if isinstance(state, dict):
        return {k: normalize_state(v) for k, v in sorted(state.items())}
    elif isinstance(state, list):
        return [normalize_state(v) for v in state]
    elif isinstance(state, float):
        return round(state, 8)  # Round to a reasonable precision to avoid small differences
    else:
        return state

def load_state(config):
    """
    Loads the latest saved state from a JSON file or initializes a new state if no saved state exists.
    """
    log_message('debug', "Starting load_state function...")  # Debug: Function start
    try:
        # Search for saved state files
        state_files = glob.glob('trade_state_*.json')
        if not state_files:
            log_message('debug', "No state files found.")
            raise FileNotFoundError("No state files found.")

        # Load the first state file found
        file_name = state_files[0]
        with open(file_name, 'r') as file:
            state = json.load(file)

        log_message('debug' ,f"Loaded state for {state['pair']}.")
        return state

    except FileNotFoundError:
        # No state file found, initialize a new state
        log_message('debug', "No state file found, initializing new state...")
        return None

    except Exception as e:
        # Handle exceptions
        error_message = f"Error loading state: {e}"
        log_message('debug', error_message)
        return None

def load_or_initialize_state(api):
    """
    Load or initialize the trading state for the bot.
    This handles both loading an existing state or configuring a new one.
    """
    try:
        # Check if a saved state exists
        state_files = glob.glob('trade_state_*.json')
        if state_files:
            # Prompt the user to load an existing state or create a new one
            log_message('debug', "Saved state found.")
            user_input = input \
                ("Saved state found. Press Enter to load, or type 'new' to configure a new session: ").strip().lower()

            if user_input == '':  # Load the existing state
                file_name = state_files[0]
                with open(file_name, 'r') as file:
                    state = json.load(file)

                log_message('debug', f"Loaded state for {state['pair']}.")
                return state
            elif user_input == 'new':  # Create a new state
                log_message('debug', "User opted to create new state.")
            else:
                log_message('debug', f"Invalid input: {user_input}")
                return None

        # No saved state or user opted to create new state
        log_message('debug', "No saved state found or starting new configuration.")
        print("No saved state found or starting new configuration.")

        # Get trading pair and interval
        trading_pair = get_validated_pair(api)
        interval = get_validated_interval()

        # Get trade percentage as a whole number and validate it
        while True:
            try:
                # Input a whole number for percentage, e.g., 5 for 5%
                trade_percentage_input = input \
                    ("Enter the trade percentage of USD balance per trade (e.g., 5 for 5%): ").strip()
                trade_percentage = int(trade_percentage_input) / 100.0  # Convert to float by dividing by 100

                # Ensure that the trade percentage is not more than 100%
                if trade_percentage <= 1.0:
                    break
                else:
                    print("ERROR: Trade percentage cannot exceed 100. Please enter a valid value (e.g., 5 for 5%).")

            except ValueError:
                print("ERROR: Invalid input. Please enter a whole number (e.g., 5 for 5%).")

        # Fetch the account balance
        balance = fetch_balance()

        # Initialize a new state with the bank field
        state = {
            'balance': balance,
            'positions': {},
            'trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit_or_loss': 0.0,
            'total_tax': 0.0,
            'interval': interval,
            'trade_percentage': trade_percentage,
            'pair': trading_pair,
            'buy_signal_counter': 0,
            'bank': {'volume': 0.0, 'cost': 0.0}  # Initialize the bank
        }

        # Save the new state
        save_state(trading_pair, state)
        log_message('debug', f"Initialized new state for {trading_pair}.")
        return state

    except Exception as e:
        log_message('error', f"Error initializing or loading state: {e}")
        return None

def fetch_balance():
    log_message('debug', "Fetch Balance Running...")  # Debug: Function start
    try:
        # Use the krakenex API object directly for private queries
        log_message('debug', "Querying Kraken API for balance...")  # Debug: API query start
        balance = api.query_private('Balance')
        log_message('debug', f"API Response: {balance}")  # Debug: Display raw API response

        if 'error' in balance and balance['error']:
            error_message = f"API Error: {balance['error']}"
            log_message('debug', error_message)  # Debug: API error response
            raise Exception(error_message)

        usd_balance = float(balance['result'].get('ZUSD', 0.0))  # Adjust key based on the correct currency format
        log_message('debug', f"Fetched USD balance: ${usd_balance:.2f}")  # Debug: Balance fetched successfully
        return usd_balance
    except Exception as e:
        error_message = f"Error fetching balance: {e}"
        log_message('debug', error_message)  # Debug: Exception occurred
        print(error_message)
        return None

def fetch_ohlc_data(pair, interval=1):
    """
    Fetch OHLC data from Kraken API and ensure the returned value is always a DataFrame.
    Avoid redundant polling by checking the last candle time before fetching new data.
    """
    global last_ohlc_update_time
    log_message('debug', f"fetch_ohlc_data Running for {pair} with interval {interval}...")  # Debug: Function start

    try:
        # Fetch OHLC data using the Kraken API with rate-limiting via make_api_call
        result = make_api_call(k.get_ohlc_data, pair, interval=interval)

        # Check if the result was fetched successfully
        if result is None or not isinstance(result, tuple):
            log_message('error', f"Failed to fetch OHLC data for {pair}.")
            return None

        ohlc_data, _ = result  # Kraken API returns OHLC data as DataFrame and last candle timestamp

        # Ensure the data is a DataFrame and contains necessary columns
        if not isinstance(ohlc_data, pd.DataFrame):
            log_message('debug', f"OHLC data is not a DataFrame. Found type: {type(ohlc_data)}")
            raise ValueError(f"OHLC data is not a DataFrame. Found type: {type(ohlc_data)}")

        if 'close' not in ohlc_data.columns or 'time' not in ohlc_data.columns:
            log_message('debug', "OHLC data missing necessary columns ('close' or 'time').")
            raise ValueError("OHLC data missing necessary columns ('close' or 'time').")

        # Debug statement to show the number of data points in OHLC data
        log_message('debug', f"OHLC data fetched for {pair} contains {len(ohlc_data)} data points.")

        # Sort data by time to ensure the latest candles are at the end
        ohlc_data = ohlc_data.sort_index()

        # Convert timestamp to UTC time
        ohlc_data['time'] = pd.to_datetime(ohlc_data.index, unit='s', utc=True)
        ohlc_data.reset_index(drop=True, inplace=True)

        # Check if there's a new candle since the last update
        last_time = ohlc_data['time'].iloc[-1]
        if last_ohlc_update_time is not None and last_time <= last_ohlc_update_time:
            log_message('debug', f"No new OHLC data available. Last candle time: {last_time}")
            return None  # No new data, skip updating

        # Update the last fetched candle time
        last_ohlc_update_time = last_time
        log_message('debug', f"New OHLC data fetched. Last candle time: {last_time}.")  # Debug: Latest candle time

        return ohlc_data  # Return the DataFrame with new OHLC data

    except Exception as e:
        log_message('error', f"Error fetching OHLC data: {e}")
        return pd.DataFrame \
            (columns=['time', 'open', 'high', 'low', 'close', 'volume'])  # Return empty DataFrame on error

def fetch_current_price(pair):
    """
    Fetch the current bid, ask, and last trade prices from Kraken API for the specified trading pair.

    Args:
        pair (str): The trading pair, e.g., "ADA/USD".

    Returns:
        dict: A dictionary containing 'bid', 'ask', and 'current_price' (last trade price).
    """
    try:
        log_message('debug', f"Initiating request to fetch current bid, ask, and last trade prices for {pair}.")

        # Fetch ticker information using the make_api_call wrapper for rate-limiting and retries
        ticker_info = make_api_call(api.query_public, 'Ticker', {'pair': pair.replace('/', '')})

        # Check if the result was fetched successfully
        if ticker_info is None or 'error' in ticker_info and ticker_info['error']:
            log_message('error', f"Error fetching ticker data for {pair}: {ticker_info.get('error', 'No error info')}")
            return {'bid': None, 'ask': None, 'current_price': None}

        log_message('debug', f"Received ticker data response: {ticker_info}")

        # Extract the first result from the ticker data
        result = list(ticker_info['result'].values())[0]
        log_message('debug', f"Parsed result from ticker data: {result}")

        # Extract bid, ask, and last trade prices
        bid = float(result['b'][0])  # 'b' is the bid price
        ask = float(result['a'][0])  # 'a' is the ask price
        current_price = float(result['c'][0])  # 'c' is the last trade price

        log_message('debug', f"Fetched bid price: {bid}, ask price: {ask}, last trade price: {current_price}")

        # Return the prices as a dictionary
        return {'bid': bid, 'ask': ask, 'current_price': current_price}

    except Exception as e:
        log_message('error', f"Exception occurred while fetching current prices for {pair}: {e}")
        return {'bid': None, 'ask': None, 'current_price': None}

def calculate_indicators(ohlc_data, current_price):
    """
    Calculate multiple indicators based on OHLC data and the current price.

    Args:
        ohlc_data (pd.DataFrame): OHLC data containing 'close' prices.
        current_price (float): The current market price of the asset.

    Returns:
        dict: A dictionary containing the calculated indicators (RSI, Bollinger Bands, etc.).
    """

    def calculate_rsi(data, price, period=14):
        """Calculate the RSI for the given data and current price."""
        try:
            close_values = data['close'].tolist()
            # log_message('debug', f"Close values: {close_values}, Current price: {price}")
            close_values.append(price)

            if len(close_values) < period + 1:
                log_message('warning', f"Not enough data to calculate RSI. Close values length: {len(close_values)}")
                return None

            profit_and_loss = [close_values[i + 1] - close_values[i] for i in range(len(close_values) - 1)]
            avg_gain = sum([x for x in profit_and_loss[-(period + 1):-1] if x >= 0]) / period
            avg_loss = sum([-x for x in profit_and_loss[-(period + 1):-1] if x < 0]) / period

            for value in profit_and_loss[-period:]:
                if value >= 0:
                    avg_gain = (avg_gain * (period - 1) + value) / period
                else:
                    avg_loss = (avg_loss * (period - 1) - value) / period

            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            log_message('debug', f"RSI: {rsi}")
            return rsi
        except Exception as e:
            log_message('error', f"Error calculating RSI: {e}")
            return None

    def calculate_bollinger_bands(data, window=20, no_of_std=2):
        """Calculate the Bollinger Bands for the given data."""
        try:
            log_message('debug', f"Starting Bollinger Bands calculation for window: {window} and std: {no_of_std}")

            # Ensure there are enough data points to calculate the rolling window
            if len(data) < window:
                log_message('warning', f"Not enough data points to calculate Bollinger Bands. "
                                       f"Data points available: {len(data)}, required: {window}")
                return None

            # Ensure the 'close' column exists and contains valid numeric values
            if 'close' not in data.columns:
                log_message('error', "'close' column missing in OHLC data.")
                return None

            if data['close'].isnull().any():
                log_message('warning', "'close' column contains NaN values.")
                return None

            log_message('debug', f"Data passed validation. Proceeding with Bollinger Bands calculation.")

            # Perform rolling calculations
            data['Middle Band'] = data['close'].rolling(window=window).mean()
            data['Standard Deviation'] = data['close'].rolling(window=window).std()

            # Check if the rolling calculations have enough data and don't return all NaN values
            if data['Middle Band'].isnull().all():
                log_message('warning', "Middle Band calculation returned all null values.")
                return None

            # Calculate Upper and Lower bands
            data['Upper Band'] = data['Middle Band'] + (data['Standard Deviation'] * no_of_std)
            data['Lower Band'] = data['Middle Band'] - (data['Standard Deviation'] * no_of_std)

            # Check if there are NaN values in the Upper or Lower Bands
            if data[['Upper Band', 'Lower Band']].isnull().all().any():
                log_message('warning', "Upper/Lower Band calculation returned NaN values.")
                return None

            log_message('debug',
                        f"Bollinger Bands calculated successfully. Latest Lower Band: {data['Lower Band'].iloc[-1]}")

            return data[['Middle Band', 'Upper Band', 'Lower Band']]

        except Exception as e:
            log_message('error', f"Error calculating Bollinger Bands: {e}")
            return None

    # Calculate indicators
    log_message('debug', "Starting to calculate indicators.")
    indicators = {}
    indicators['rsi'] = calculate_rsi(ohlc_data, current_price)
    indicators['bollinger_bands'] = calculate_bollinger_bands(ohlc_data)

    # Log results
    if indicators['rsi'] is not None:
        log_message('debug', f"RSI: {indicators['rsi']}")
    else:
        log_message('warning', "RSI calculation failed or returned None.")

    if indicators['bollinger_bands'] is not None:
        log_message('debug', f"Bollinger Bands: {indicators['bollinger_bands'].tail(1)}")
    else:
        log_message('error', "Bollinger Bands calculation failed or returned None.")

    return indicators

def place_buy_order(state):
    try:
        # Retrieve necessary parameters from the state
        pair = state['pair']
        trade_percentage = state['trade_percentage']
        current_price = state['current_price']
        balance = state['balance']

        # Calculate the trade balance and volume
        trade_balance = balance * trade_percentage
        trade_volume = trade_balance / current_price

        # Logging the buy order attempt
        log_message('debug', f"Attempting to place buy order for {pair} with volume {trade_volume:.4f} at price {current_price:.4f}")
        log_message('PERFORMED_ACTION', f"Attempting to place buy order for {pair} with volume {trade_volume:.4f} at price {current_price:.4f}")

        # Minimum trade volume check
        if trade_volume < 0.01:
            log_message('warning', f"Insufficient volume to place a buy order for {pair}. Required minimum: 0.01, Available: {trade_volume:.4f}")
            return None

        # Placing the buy order via the Kraken API
        order = api.query_private('AddOrder', {
            'nonce': str(int(time.time() * 1000)),
            'pair': pair.replace('/', ''),
            'type': 'buy',
            'ordertype': 'market',
            'volume': str(trade_volume)
        })

        # Check for errors in the API response
        if 'error' in order and order['error']:  # If 'error' exists and is non-empty
            log_message('error', f"Error placing buy order: {order['error']}")
            return None

        # Ensure 'result' is in the response
        if 'result' not in order:
            log_message('error', "Buy order response does not contain 'result'.")
            return None

        # Retrieve trade details from the order response
        txid = list(order['result']['txid'])[0]
        order_info = api.query_private('QueryOrders', {'txid': txid})

        # Ensure 'result' is in the order_info
        if 'result' not in order_info or txid not in order_info['result']:
            log_message('error', f"Could not retrieve trade details for txid {txid}.")
            return None

        trade_details = order_info['result'][txid]

        # Extract trade data with a check for 'closetm' existence
        trade_data = {
            'price': float(trade_details['price']),
            'vol': float(trade_details['vol_exec']),
            'cost': float(trade_details['cost']),
            'fee': float(trade_details['fee']),
            # Use current timestamp if 'closetm' is missing
            'time': float(trade_details.get('closetm', time.time()))
        }

        # Calculate profit and stop loss targets based on the buy price
        profit_targets = [round(trade_data['price'] * level, 4) for level in [1.016, 1.025, 1.05, 1.10]]
        stop_loss_targets = [round(trade_data['price'] * level, 4) for level in [0.92, 0.90, 0.88, 0.85]]

        # Generate a unique position ID
        position_number = 1
        position_id = f"position_{position_number}"
        while position_id in state['positions']:
            position_number += 1
            position_id = f"position_{position_number}"

        position = {
            'buy_price': trade_data['price'],
            'volume': trade_data['vol'],
            'initial_volume': trade_data['vol'],
            'profit_targets': profit_targets,
            'stop_loss_targets': stop_loss_targets,
            'last_sell_time': 0
        }

        # Add the new position to the state
        state['positions'][position_id] = position

        # Update the bot's general state
        state['trades'] += 1
        state['balance'] -= trade_data['cost'] + trade_data['fee']  # Deduct cost and fee from balance

        # Log and update state after the purchase
        log_message('PERFORMED_ACTION', f"Buy order placed and state updated for {pair}: {trade_data}")
        save_state(pair, state)

        # Reset the buy signal counter after successful purchase
        state['buy_signal_counter'] = 0

        # Send email notification for the buy order
        email_subject = f"Buy Order Executed for {pair}"
        email_message = (
            f"A buy order has been executed:\n\n"
            f"Trading Pair: {pair}\n"
            f"Volume: {trade_data['vol']:.4f}\n"
            f"Buy Price: {trade_data['price']:.4f}\n"
            f"Cost: {trade_data['cost']:.2f}\n"
            f"Fee: {trade_data['fee']:.2f}\n"
            f"Updated Balance: {state['balance']:.2f}\n"
        )
        send_email(email_subject, email_message)

        return trade_data

    except Exception as e:
        log_message('error', f"Error placing buy order for {pair}: {e}")
        return None

def buy_condition(pair, state, ohlc_data):
    """
    Checks buy conditions and executes a buy order if conditions are met.

    Args:
        pair (str): The trading pair.
        state (dict): The current state of the bot.
        ohlc_data (DataFrame): The OHLC data required for determining buy conditions.

    Returns:
        bool: True if a buy was executed, False otherwise.
    """
    current_price = state.get('current_price')
    rsi = state.get('current_rsi')
    lower_band = state.get('lower_band')
    balance = state.get('balance', 0)

    log_message('debug', f"Running buy_condition for {pair}.")

    # Log current values for troubleshooting
    log_message('debug', f"Current Price: {current_price}, RSI: {rsi}, Lower Band: {lower_band}, Balance: {balance}")

    try:

        # Check if the maximum number of positions has been reached
        if len(state['positions']) >= 5:
            log_message('debug', "Position limit reached. No more buys allowed.")

            return False

        # Check if the balance is above $25
        if balance < 25:
            log_message('debug', "Balance is less than $25. Skipping buy condition check.")
            return False

        # Validate current price before proceeding
        if current_price is None:
            log_message('warning', "Current price is unavailable. Skipping buy condition check.")

            return False

        if rsi is None:
            log_message('warning', "RSI value is unavailable. Skipping buy condition check.")

            return False

        if lower_band is None:
            log_message('warning', "Lower Bollinger Band is unavailable. Skipping buy condition check.")

            return False

        # Ensure OHLC data has enough entries to access the previous close
        if ohlc_data is None or len(ohlc_data) < 2:
            log_message('warning', "Not enough OHLC data to determine previous close.")

            return False

        # Extract previous and latest candle data safely
        prev_close = ohlc_data.iloc[-2]['close']
        latest_candle_time = pd.to_datetime(ohlc_data.iloc[-1]['time']) if 'time' in ohlc_data.columns else None

        # Check if latest candle time is valid
        if latest_candle_time is None:
            log_message('warning', "Latest candle time is missing; skipping condition check.")

            return False



        # Use OHLC data to determine if the previous close was below the lower band
        prev_close_below_lower_band = prev_close < lower_band
        rsi_condition = rsi < 35

        log_message('debug', f"Previous close below lower band: {prev_close_below_lower_band}")
        log_message('debug', f"RSI condition met (RSI < 35): {rsi_condition}")
        log_message('debug', f"Current price < Lower Band: {current_price < lower_band}")

        # Retrieve and validate last processed candle time from state
        last_candle_time = pd.to_datetime(state.get('last_candle_time', None))

        # Compare times
        log_message('debug',
                    f"Latest candle time: {latest_candle_time}, Last processed candle time: {last_candle_time}")

        # Check if this candle has already been processed
        if last_candle_time and last_candle_time == latest_candle_time:
            log_message('debug', "Current candle matches last processed candle. Skipping buy signal increment.")
            return False

        # Log the current buy signal before checking the conditions
        log_message('debug', f"Current Buy Signal: {state['buy_signal_counter']}")

        # Check if all buy conditions are met
        if prev_close_below_lower_band and rsi_condition and current_price < lower_band:
            log_message('debug', "All buy conditions met.")

            # Increment the buy signal counter
            log_message('debug', f"Buy signal counter before increment: {state['buy_signal_counter']}")
            state['buy_signal_counter'] += 1
            log_message('debug', f"Buy signal counter after increment: {state['buy_signal_counter']}")

            # Update the last candle time to avoid reprocessing the same candle
            state['last_candle_time'] = latest_candle_time.isoformat()  # Store as ISO formatted string for consistency
            save_state(pair, state)
            log_message('debug', "State saved after updating buy signal counter and last candle time.")
            log_message('debug', "State saved after updating buy signal counter and last candle time.")
            # Execute a buy when the buy signal counter reaches the threshold
            if state['buy_signal_counter'] >= 3:
                # Attempt to place the buy order; only place_buy_order will handle state updates
                buy_order = place_buy_order(state)
                return bool(buy_order)  # Return True if buy_order is successful, else False
            else:
                log_message('debug', f"Buy signal {state['buy_signal_counter']} detected but not enough to buy yet.")
                return False
        else:
            log_message('debug', "Buy conditions not met.")
            return False
    except Exception as e:
        log_message("error", f"Error in buy_condition: {e}")
        log_message("debug", f"Error in buy_condition: {e}")
        return False

def place_sell_order(pair, volume, current_bid, state, position_id):
    """
    Places a sell order via the API, calculates the resulting changes in memory, and finally updates the state.

    Args:
        pair (str): The trading pair being traded.
        volume (float): The volume of the asset to be sold.
        current_bid (float): The current bid price.
        state (dict): The current state of the trading bot.
        position_id (str): The ID of the position being sold.

    Returns:
        dict: The trade details if successful, otherwise the order response including any errors.
    """
    try:
        log_message('debug', f"Attempting to place sell order: Pair={pair}, Volume={volume}, Price={current_bid}")

        # Minimum trade volume check
        if volume < 0.01:
            volume = state['positions'][position_id]['volume']
            log_message(
                "warning",
                f"Adjusted volume to entire position as initial volume {volume:.4f} is below the minimum trade threshold."
            )
            log_message('debug', f"Adjusted volume for sell to: {volume:.4f}")

        # Place sell order via API
        order = api.query_private('AddOrder', {
            'nonce': str(int(time.time() * 1000)),
            'pair': pair.replace('/', ''),
            'type': 'sell',
            'ordertype': 'market',
            'volume': str(volume)
        })

        # Check for errors in the API response
        if 'error' in order and order['error']:  # If 'error' exists and is non-empty
            log_message('error', f"Error placing sell order: {order['error']}")
            return order  # Return the error response instead of None

        # Check if 'result' and 'txid' are present in the response
        if 'result' not in order or 'txid' not in order['result']:
            log_message('error', "Sell order response missing 'result' or 'txid'.")
            return order  # Return the incomplete response for debugging

        # Retrieve and log the transaction ID (txid)
        txid = order['result']['txid'][0]
        log_message('debug', f"Sell order placed successfully, received txid: {txid}")

        # Fetch the order details using the txid
        order_info = api.query_private('QueryOrders', {'txid': txid})

        # Check if the response contains valid order details
        if 'error' in order_info and order_info['error']:
            log_message('error', f"Error fetching order details: {order_info['error']}")
            return order_info  # Return the error response for debugging

        if 'result' not in order_info or txid not in order_info['result']:
            log_message('error', f"Order details for txid {txid} are missing.")
            return order_info  # Return the incomplete response for debugging

        trade_details = order_info['result'][txid]

        # Extract trade data and calculate profit/loss, subtracting the fee
        trade_data = {
            'price': float(trade_details['price']),
            'vol': float(trade_details['vol_exec']),
            'cost': float(trade_details['cost']),
            'fee': float(trade_details['fee']),
            'time': float(trade_details.get('closetm', time.time()))
        }

        # Work with a copy of the position data
        position = state['positions'][position_id].copy()
        position['volume'] -= trade_data['vol']

        # Calculate new balance and profit/loss
        new_balance = fetch_balance()  # Ensure the balance is updated after the sell
        buy_price = position['buy_price']
        raw_profit_or_loss = (trade_data['price'] - buy_price) * trade_data['vol']
        profit_or_loss = raw_profit_or_loss - trade_data['fee']  # Subtract the fee from the profit

        # Update taxes and win/loss count
        total_tax = state['total_tax']
        winning_trades = state['winning_trades']
        losing_trades = state['losing_trades']
        total_profit_or_loss = state['total_profit_or_loss']

        # Add taxes for profitable trades (0.37 of profit)
        if profit_or_loss > 0:
            tax_amount = profit_or_loss * 0.37
            total_tax += tax_amount
            winning_trades += 1
            log_message('debug', f"Taxes for this trade: {tax_amount:.2f} added to total tax.")
        else:
            losing_trades += 1

        # Update total profit/loss
        total_profit_or_loss += profit_or_loss

        # Log the trade
        log_message('PERFORMED_ACTION', f"Executed sell order for {pair}. Volume: {trade_data['vol']}, "
                                        f"Sell Price: {trade_data['price']}, Buy Price: {buy_price}, "
                                        f"Profit/Loss: {profit_or_loss:.2f} (after fees), Balance: {new_balance:.2f}")
        log_message('debug', f"Sell order placed successfully: {trade_data}")

        # Only now, update the state with the newly calculated values
        state['positions'][position_id] = position
        state['balance'] = new_balance
        state['total_tax'] = total_tax
        state['winning_trades'] = winning_trades
        state['losing_trades'] = losing_trades
        state['total_profit_or_loss'] = total_profit_or_loss

        # Save the updated state
        save_state(pair, state)
        log_message('debug', "State saved after successful sell order.")

        # Send email notification for the sell order
        send_email(f"Sell Order Executed for {pair}", (
            f"Trading Pair: {pair}\n"
            f"Volume: {trade_data['vol']:.4f}\n"
            f"Sell Price: {trade_data['price']:.4f}\n"
            f"Buy Price: {buy_price:.4f}\n"
            f"Profit/Loss (after fees): {profit_or_loss:.2f}\n"
            f"Updated Balance: {new_balance:.2f}\n"
            f"Total Taxes Owed: {total_tax:.2f}\n"
            f"Total Profit/Loss: {total_profit_or_loss:.2f}\n"
        ), "alexbar8520@gmail.com")

        return trade_data

    except Exception as e:
        log_message('error', f"Error placing sell order for {pair}: {e}")
        return {'error': str(e)}  # Return a structured error message

def sell_condition(state):
    log_message('debug', f"Running sell_condition for {state['pair']}")
    min_trade_volume = 0.01
    cooldown_period = 30  # Cooldown period in seconds
    current_time = time.time()

    if not state['positions']:
        log_message("debug", "No positions available to sell.")
        return

    positions_to_delete = []

    # Create a list of positions to iterate over to avoid modifying the state during iteration
    positions_copy = list(state['positions'].items())

    for pos_id, position in positions_copy:
        current_bid = state.get('current_bid')
        log_message('debug', f"Checking position {pos_id} with details: {position}")

        if current_bid is None:
            log_message('warning', "Current bid price is unavailable. Skipping sell condition check.")
            continue

        # Check if the position is on cooldown
        last_sell_time = position.get('last_sell_time', 0)
        cooldown_remaining = cooldown_period - (current_time - last_sell_time)
        if cooldown_remaining > 0:
            log_message('debug', f"Position {pos_id} is on cooldown for another {cooldown_remaining:.2f} seconds. Skipping sell.")
            continue

        # Check if only one profit target remains, adjust stop loss to 1.6% above buy price
        if len(position['profit_targets']) == 1:
            new_stop_loss = round(position['buy_price'] * 1.018, 4)  # Set stop loss at 1.8% above buy price
            position['stop_loss_targets'] = [new_stop_loss]
            log_message('PERFORMED_ACTION', f"Only one profit target left, updated stop loss to {new_stop_loss}.")

        # Check profit targets
        for target in position['profit_targets'][:]:
            log_message('debug', f"Checking profit target {target} for position {pos_id}")
            if current_bid >= target:
                log_message('PERFORMED_ACTION', f"Profit target met for position {pos_id}. Current bid: {current_bid}, Target: {target}")

                partial_volume = max(min(position['initial_volume'] * 0.25, position['volume']), min_trade_volume)
                log_message('PERFORMED_ACTION', f"Attempting to sell {partial_volume} from position {pos_id} at bid {current_bid}.")

                sell_order = place_sell_order(state['pair'], partial_volume, current_bid, state, pos_id)

                if sell_order:
                    position['profit_targets'].remove(target)
                    position['last_sell_time'] = current_time
                    log_message('PERFORMED_ACTION', f"Sold {partial_volume} at {current_bid} for profit. Updated position {pos_id}.")
                    save_and_verify_state(state['pair'], state)

                    if position['volume'] < min_trade_volume:
                        log_message('debug', f"Position {pos_id} volume is below minimum after sell. Marking for deletion.")
                        positions_to_delete.append(pos_id)
                else:
                    log_message('PERFORMED_ACTION', f"Failed to sell position {pos_id} at profit target {target}.")
                break

        # Check stop loss targets
        for stop_target in position['stop_loss_targets'][:]:
            log_message('debug', f"Checking stop loss target {stop_target} for position {pos_id}")
            if current_bid <= stop_target:
                log_message('PERFORMED_ACTION', f"Stop loss target met for position {pos_id}. Current bid: {current_bid}, Stop Target: {stop_target}")

                partial_volume = max(min(position['initial_volume'] * 0.25, position['volume']), min_trade_volume)
                log_message('debug', f"Attempting to sell {partial_volume} from position {pos_id} at bid {current_bid}.")

                sell_order = place_sell_order(state['pair'], partial_volume, current_bid, state, pos_id)

                if sell_order:
                    position['stop_loss_targets'].remove(stop_target)
                    position['last_sell_time'] = current_time
                    log_message('PERFORMED_ACTION', f"Sold {partial_volume} at {current_bid} for stop loss. Updated position {pos_id}.")
                    save_and_verify_state(state['pair'], state)

                    if position['volume'] < min_trade_volume:
                        log_message('debug', f"Position {pos_id} volume is below minimum after sell. Marking for deletion.")
                        positions_to_delete.append(pos_id)
                else:
                    log_message('PERFORMED_ACTION', f"Failed to sell position {pos_id} at stop loss target {stop_target}.")

                break

        # If the position volume is too small, add to bank instead of deleting
        if position['volume'] <= 1e-8:
            log_message('PERFORMED_ACTION', f"Position {pos_id} too small to sell. Adding to bank.")
            add_to_bank(state, position)
            positions_to_delete.append(pos_id)

    # Delete the positions marked for deletion after iteration is complete
    for pos_id in positions_to_delete:
        if pos_id in state['positions']:
            del state['positions'][pos_id]
            log_message('PERFORMED_ACTION', f"Position {pos_id} removed from state.")
            renumber_positions(state)  # Renumber after deletion
            log_message('PERFORMED_ACTION', "Positions Renumbered.")
            save_and_verify_state(state['pair'], state)
            log_message('debug', f"State saved after removing position {pos_id}.")

    # Check the bank state and move it into a position if the bank value exceeds $25
    bank_volume = state['bank']['volume']
    bank_cost = state['bank']['cost']
    current_bid = state.get('current_bid')

    if bank_volume > 0 and current_bid:
        bank_value = bank_volume * current_bid

        if bank_value >= 25:
            log_message('debug', f"Bank value is ${bank_value:.2f}, creating new position.")
            create_position_from_bank(state)

def add_to_bank(state, position):
    """
    Adds a small position to the bank, which will accumulate until it reaches $25 in value.
    The average buy price is updated to calculate profit/stop-loss accurately when re-entered into positions.
    """
    current_volume = state['bank']['volume']
    current_cost = state['bank']['cost']

    # Calculate the value of the new position being added
    position_value = position['buy_price'] * position['volume']

    # Calculate the new total volume and value
    new_total_volume = current_volume + position['volume']
    new_total_value = (current_cost * current_volume) + position_value

    # Calculate the new average cost
    if new_total_volume == 0:
        new_average_cost = 0
    else:
        new_average_cost = new_total_value / new_total_volume

    # Update the bank state
    state['bank']['volume'] = new_total_volume
    state['bank']['cost'] = new_average_cost

    # Debug log to track changes
    log_message('debug', f"Updated bank volume: {new_total_volume:.8f}, cost: {new_average_cost:.2f}")

    # Check if the bank is large enough to create a new position
    bank_value = new_total_volume * state['current_bid']
    if bank_value >= 25:
        log_message("debug", f"Bank value is ${bank_value:.2f}, creating new position.")
        create_position_from_bank(state)

def renumber_positions(state):
    new_positions = {}
    for index, (pos_id, position) in enumerate(state['positions'].items(), start=1):
        new_positions[f'position_{index}'] = position
    state['positions'] = new_positions

def create_position_from_bank(state):
    """
    Creates a new position from the bank once the value exceeds $25.
    """
    bank_volume = state['bank']['volume']
    bank_cost = state['bank']['cost']

    # Ensure bank volume and cost are valid before proceeding
    if bank_volume <= 0:
        log_message('error', "Attempting to create a new position with zero or negative bank volume.")
        return

    # Generate a unique position ID
    position_number = 1
    position_id = f"position_{position_number}"
    while position_id in state['positions']:
        position_number += 1
        position_id = f"position_{position_number}"

    new_position = {
        'buy_price': bank_cost,
        'volume': bank_volume,
        'initial_volume': bank_volume,
        'profit_targets': [round(bank_cost * level, 4) for level in [1.016, 1.025, 1.05, 1.10]],
        'stop_loss_targets': [round(bank_cost * level, 4) for level in [0.92, 0.90, 0.88, 0.85]],
        'last_sell_time': 0
    }

    # Add the new position to the state
    state['positions'][position_id] = new_position

    # Reset the bank
    state['bank'] = {'volume': 0.0, 'cost': 0.0}
    log_message("debug", f"Created new position from bank. Position ID: {position_id}, Volume: {bank_volume:.8f}, Buy Price: {bank_cost:.2f}")

    # Save the updated state
    save_state(state['pair'], state)

def menu():
    # Nested functions for menu actions
    def enter_position():
        log_message('debug', 'Enter position function called.')
        print("Entering a position... (placeholder)")

    def close_position():
        log_message('debug', 'Close position function called.')
        print("Closing a position... (placeholder)")

    def change_interval():
        log_message('debug', 'Change interval function called.')
        print("Changing interval... (placeholder)")

    def change_percentage():
        log_message('debug', 'Change percentage function called.')
        print("Changing percentage... (placeholder)")

    def toggle_debug_mode():
        global debug_mode
        debug_mode = not debug_mode
        log_message('debug', f"Debug mode turned {'ON' if debug_mode else 'OFF'}.")
        print(f"Debug mode is now {'ON' if debug_mode else 'OFF'}")

    def stop_bot():
        log_message('debug', 'Stop bot function called.')
        stop_signal.set()  # Signal the trading logic thread to stop
        trading_thread.join()  # Wait for the thread to finish
        log_message('debug', 'Bot has stopped.')
        exit()

    # Menu logic - activated only when the user presses Enter
    while True:
        try:
            # Wait for user to press Enter to activate menu
            input("\nPress Enter to enter command mode...")

            print("\n--- Trading Bot Menu ---")
            print("1. Enter Position")
            print("2. Close Position")
            print("3. Change Interval")
            print("4. Change Percentage")
            print("5. Toggle Debug Mode")
            print("6. Stop Bot")
            print("7. Exit Command Mode")

            choice = input("Select an option (1-7): ")

            if choice == '1':
                enter_position()
            elif choice == '2':
                close_position()
            elif choice == '3':
                change_interval()
            elif choice == '4':
                change_percentage()
            elif choice == '5':
                toggle_debug_mode()
            elif choice == '6':
                stop_bot()
                break  # Break out of the menu and stop the bot
            elif choice == '7':
                print("Exiting command mode...")
                return  # Exit command mode and return to the main loop
            else:
                print("Invalid choice. Please select a valid option.")

        except KeyboardInterrupt:
            log_message('info', "Bot manually stopped.")
            stop_bot()
            break

def create_dashboard(state):
    """Creates the trading dashboard layout, showing various metrics and logs based on the bot's state."""

    # Safely retrieve values from state with default fallbacks if None
    current_price = state.get('current_price', 0.0)
    current_bid = state.get('current_bid', 0.0)
    current_ask = state.get('current_ask', 0.0)
    current_rsi = state.get('current_rsi', 0.0)
    upper_band = state.get('upper_band', 0.0)
    lower_band = state.get('lower_band', 0.0)
    usd_balance = state.get('balance', 0.0)
    total_profit_loss = state.get('total_profit_or_loss', 0.0)
    buy_signal_counter = state.get('buy_signal_counter', 0)

    # Indicators (RSI, Bollinger Bands, Buy Signal)
    indicators_text = Text.assemble(
        ("RSI: ", "bold cyan"), f"{current_rsi:.2f}  |  ",
        ("Upper Band: ", "bold cyan"), f"${upper_band:.4f}  |  ",
        ("Lower Band: ", "bold cyan"), f"${lower_band:.4f}  |  ",
        ("Buy Signal Count: ", "bold cyan"), f"{buy_signal_counter}"
    )
    indicators_panel = Panel(indicators_text, title="Indicators", border_style="green")

    # Trading Data Panel
    trading_data_text = Text.assemble(
        ("PAIR: ", "bold cyan"), f"{state.get('pair', 'N/A')} | ",
        ("INTERVAL: ", "bold cyan"), f"{state.get('interval', 'N/A')}min | ",
        ("CURRENT PRICE: ", "bold cyan"), f"${current_price:.6f} | ",
        ("BID: ", "bold cyan"), f"${current_bid:.6f} | ",
        ("ASK: ", "bold cyan"), f"${current_ask:.6f} | ",
        ("USD BALANCE: ", "bold cyan"), f"${usd_balance:.2f} | ",
        ("TOTAL P/L: ", "bold cyan"), f"${total_profit_loss:.2f}"
    )
    trading_data_panel = Panel(trading_data_text, title="Current Trading Data", border_style="green")

    # Positions Panel
    positions_table = Table.grid(expand=True)
    positions_table.add_column("Position")
    positions_table.add_column("Volume")
    positions_table.add_column("P/L")

    for i, (position_id, position) in enumerate(state.get('positions', {}).items(), start=1):
        buy_price = position.get('buy_price', 0.0)
        volume = position.get('volume', 0.0)
        position_pl = (current_price - buy_price) * volume
        pl_color = "green" if position_pl >= 0 else "red"
        position_pl_text = Text(f"${position_pl:.4f}", style=pl_color)

        positions_table.add_row(
            f"Position {i}",
            f"{volume:.4f}",
            position_pl_text
        )

    positions_panel = Panel(positions_table, title="Position Data", border_style="green")

    # Log Panel to display recent log messages
    log_panel_text = "\n".join(state.get('log_messages', [])[-10:])  # Display the last 10 log entries
    log_panel = Panel(log_panel_text, title="Log Messages", border_style="blue")

    # Menu Panel
    menu_text = Text.assemble(
        ("1. ", "bold cyan"), "Close All Positions  |  ",
        ("2. ", "bold cyan"), "Close Position by Number  |  ",
        ("3. ", "bold cyan"), "Enter New Position  |  ",
        ("4. ", "bold cyan"), "Pause Bot  |  ",
        ("5. ", "bold cyan"), "Resume Bot  |  ",
        ("6. ", "bold cyan"), "Exit"
    )
    menu_panel = Panel(menu_text, title="Menu Options", border_style="red")

    # Main layout
    layout = Layout()

    # Split layout into two sections: Left for Position Data and Right for Logs and Menu
    layout.split_column(
        Layout(trading_data_panel, size=4),
        Layout(positions_panel, size=10),
        Layout(indicators_panel, size=4),
        Layout(log_panel, size=8),
        Layout(menu_panel, size=6)
    )

    return layout

def draw_dashboard(state):
    """Renders the dashboard layout once based on the current state."""
    console = Console()
    layout = create_dashboard(state)
    console.clear()  # Clear the screen before drawing
    console.print(layout)

def trading_logic(state):
    """
    Main trading logic that runs in a loop using the provided state.

    Args:
        state (dict): The current state of the trading bot.
    """
    log_message('debug', 'Trading logic started.')

    try:
        # Use the trading pair from the state
        pair = state['pair']

        # Track last OHLC data fetch time
        ohlc_last_fetched = None  # Time when OHLC data was last fetched
        ohlc_interval_seconds = state['interval'] * 60  # Convert interval to seconds

        console = Console()

        while not stop_signal.is_set():


            current_time = time.time()

            # Step 1: Fetch OHLC data if the interval has passed
            if ohlc_last_fetched is None or (current_time - ohlc_last_fetched >= ohlc_interval_seconds):
                log_message('debug', f"Fetching OHLC data for pair: {pair}")

                # Fetch OHLC data
                ohlc_data = fetch_ohlc_data(pair, interval=state['interval'])

                if ohlc_data is not None and not ohlc_data.empty:
                    ohlc_last_fetched = current_time  # Update the last fetched time
                    state['ohlc_data'] = ohlc_data  # Save OHLC data to state

                    # Print the length of OHLC data instead of the full data
                    log_message('debug', f"Length of OHLC data: {len(ohlc_data)}")
                else:
                    log_message('warning', f"Failed to fetch OHLC data for {pair} or data is empty. Retrying...")
                    time.sleep(30)
                    continue

            # Step 2: Fetch current prices (bid, ask, and last trade price)
            log_message('debug', f"Fetching current price for pair: {pair}")

            # Fetch current prices
            price_data = fetch_current_price(pair)

            if price_data and price_data['current_price'] is not None:
                state['current_price'] = price_data['current_price']
                state['current_bid'] = price_data['bid']
                state['current_ask'] = price_data['ask']

                # Print current price data for debugging
                log_message('debug',
                            f"Fetched current prices - Bid: {state['current_bid']}, Ask: {state['current_ask']}, "
                            f"Current Price: {state['current_price']}")
            else:
                log_message('warning', f"Failed to fetch current price data for {pair}. Retrying...")
                time.sleep(30)
                continue

            # Step 3: Calculate indicators if both OHLC data and current price are available
            if 'ohlc_data' in state and state['current_price']:
                log_message('debug', f"Calculating indicators for pair: {pair}")

                # Calculate indicators (RSI, Bollinger Bands, etc.)
                indicators = calculate_indicators(state['ohlc_data'], state['current_price'])

                if indicators:
                    if indicators['rsi'] is not None:
                        state['current_rsi'] = indicators['rsi']
                        log_message('debug', f"RSI calculated successfully: {state['current_rsi']}")
                    else:
                        log_message('warning', "RSI calculation returned None.")

                    if indicators['bollinger_bands'] is not None:
                        state['lower_band'] = indicators['bollinger_bands']['Lower Band'].iloc[-1]
                        log_message('debug', f"Lower Band calculated successfully: {state['lower_band']}")
                    else:
                        log_message('error', "Bollinger Bands calculation returned None.")
                else:
                    log_message('warning', f"Failed to calculate indicators for {pair}. Retrying...")
                    time.sleep(30)
                    continue

                # Debug: Print the current state values after indicators calculation
                log_message('debug', f"State after indicators calculation:\n"
                                     f"Current Price: {state.get('current_price')}\n"
                                     f"Current Bid: {state.get('current_bid')}\n"
                                     f"Current Ask: {state.get('current_ask')}\n"
                                     f"RSI: {state.get('current_rsi')}\n"
                                     f"Lower Bollinger Band: {state.get('lower_band')}\n"
                                     f"OHLC Data Length: {len(state.get('ohlc_data'))}\n"
                                     f"Buy Signal Counter: {state.get('buy_signal_counter')}")

                # Step 4: Run sell condition check
                log_message('debug', "Running sell condition check.")
                sell_condition(state)

                # Step 5: Run buy condition check
                log_message('debug', "Running buy condition check.")
                buy_condition(pair, state, ohlc_data)

            else:
                log_message('warning',
                            'Required data (OHLC data or current price) is missing. Skipping indicator calculation.')

            # Wait before checking again to avoid flooding the API
            time.sleep(30)

    except Exception as e:
        log_message('error', f"An error occurred in the trading logic: {e}")
    finally:
        log_message('info', 'Trading logic stopped.')

def main():
    global trading_thread

    # Log file is created before setting up the logger
    log_filename = f"trading_bot_{datetime.now().strftime('%Y-%m-%d')}.log"

    if not os.path.exists(log_filename):
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Log file created for today {datetime.now().strftime('%Y-%m-%d')}.\n")

    log_message('info', 'Starting the trading bot...')

    # Load or initialize the bot's state
    state = load_or_initialize_state(api)  # Use this to handle both loading and initialization

    if state is None:
        log_message('error', "Failed to initialize or load state.")
        return

    # Start the trading logic in a background thread, passing the state to it
    trading_thread = threading.Thread(target=trading_logic, args=(state,))
    trading_thread.daemon = True  # Daemon thread so it closes with the main thread
    trading_thread.start()

    # Menu interaction loop
    while True:
        try:
            # Wait for the user to hit Enter to display the menu
            input("\nPress Enter to enter command mode...")
            menu()  # Display the menu when Enter is pressed
        except KeyboardInterrupt:
            log_message('info', "Bot manually stopped.")
            stop_bot()  # Gracefully stop the bot if interrupted
            break

if __name__ == "__main__":
    main()
