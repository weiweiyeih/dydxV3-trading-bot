from dydx3.constants import API_HOST_SEPOLIA, API_HOST_MAINNET
from decouple import config # Enable us to access our .env variables

# !!!! SELECT MODE !!!!
MODE = "DEVELOPMENT" # or "PRODUCTION"

# Close all open positions and orders
ABORT_ALL_POSITIONS = True # Recommendation: Testnet -> True, Production -> False

# Find Cointegrated Pairs
FIND_COINTEGRATED = True

# Manage exits
MANAGE_EXITS = True

# Manage entries
PLACE_TRADES = True

# W's note: Exit when z_score_current crosses "zero" (default) or "the opposite of z_score_traded"
EXIT_WHEN_CROSS_ZERO = False 

# Resolution (timeframe)
RESOLUTION = "1HOUR" # Hourly timeframe

# Stats Window (When calculating a rolling average for Z-score)
WINDOW = 21 # Do a rolling moving average based on 21 days

# Threshold - Opening
MAX_HALF_LIFE = 24
ZSCORE_THRESHOLD = 1.5
USD_PER_TRADE = 50 # $50 on each short and $50 on each long
USD_MIN_COLLATERAL = 1500 # the min. portfolio value in your DYDX account # default: 1800

# Threshold - Closing
# If we open a trade when Z-score hits -1.5, then we will close the trade when it crosses +1.5 (or 0)
CLOSE_AT_ZSCORE_CROSS = True

# Ethereum Address
ETHEREUM_ADDRESS = "0xC62401919639742bBB6BBC995A78D057B261d649"

# KEYS - Production
# Must to be on Mainnet on DYDX
STARK_PRIVATE_KEY_MAINNET = config("STARK_PRIVATE_KEY_MAINNET")
DYDX_API_KEY_MAINNET = config("DYDX_API_KEY_MAINNET")
DYDX_API_SECRET_MAINNET = config("DYDX_API_SECRET_MAINNET")
DYDX_API_PASSPHRASE_MAINNET = config("DYDX_API_PASSPHRASE_MAINNET")

# KEYS - Development
# Must to be on Testnet on DYDX
STARK_PRIVATE_KEY_TESTNET = config("STARK_PRIVATE_KEY_TESTNET")
DYDX_API_KEY_TESTNET = config("DYDX_API_KEY_TESTNET")
DYDX_API_SECRET_TESTNET = config("DYDX_API_SECRET_TESTNET")
DYDX_API_PASSPHRASE_TESTNET = config("DYDX_API_PASSPHRASE_TESTNET")

# KEYS - Export
STARK_PRIVATE_KEY = STARK_PRIVATE_KEY_MAINNET if MODE == "PRODUCTION" else STARK_PRIVATE_KEY_TESTNET
DYDX_API_KEY = DYDX_API_KEY_MAINNET if MODE == "PRODUCTION" else DYDX_API_KEY_TESTNET
DYDX_API_SECRET = DYDX_API_SECRET_MAINNET if MODE == "PRODUCTION" else DYDX_API_SECRET_TESTNET
DYDX_API_PASSPHRASE = DYDX_API_PASSPHRASE_MAINNET if MODE == "PRODUCTION" else DYDX_API_PASSPHRASE_TESTNET

# HOST - Export
HOST = API_HOST_MAINNET if MODE == "PRODUCTION" else API_HOST_SEPOLIA

# HTTP PROVIDER (Alchemy)
HTTP_PROVIDER_MAINNET = "https://eth-mainnet.g.alchemy.com/v2/z8BpwE0CQrmh3woOE3WLg8hO8GeLNAH5"
HTTP_PROVIDER_TESTNET = "https://eth-sepolia.g.alchemy.com/v2/3Q8a_FUS8348OeeAGwlFqmLHxaNrCDaz"
HTTP_PROVIDER = HTTP_PROVIDER_MAINNET if MODE == "PRODUCTION" else HTTP_PROVIDER_TESTNET
