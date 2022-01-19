
from random import triangular
import func_arbitrage

"""
    Step 0: Finding coins which can be traded
    Exchange: Poloniex
    https://docs.poloniex.com/#introduction
"""


def step_0():
    # Extract list of coins and prices from exchange
    coin_json = func_arbitrage.get_coin_tickers(
        "https://poloniex.com/public?command=returnTicker")

    # Loop through each object and find the tradable pairs
    # Return a list of tradable coins
    return func_arbitrage.collect_tradables(coin_json)


"""
    Step 1: Structuring triangular pairs
    Calculation only
"""


def step_1(coin_list):
    # Structure the list of tradeable triangular arbitrage pairs
    structured_pair = func_arbitrage.structure_triangular_pairs(coin_list)


""" MAIN """
if __name__ == "__main__":
    coin_list = step_0()
    structured_pairs = step_1(coin_list)
