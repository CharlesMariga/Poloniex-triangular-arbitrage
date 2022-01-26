
from random import triangular
import func_arbitrage
import json
import time

# Global variables
coin_price_url = "https://poloniex.com/public?command=returnTicker"

"""
    Step 0: Finding coins which can be traded
    Exchange: Poloniex
    https://docs.poloniex.com/#introduction
"""


def step_0():
    # Extract list of coins and prices from exchange
    coin_json = func_arbitrage.get_coin_tickers(coin_price_url)

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

    # Save structured list to json file
    with open("structured_triangular_pairs.json", "w") as fp:
        json.dump(structured_pair, fp)


"""
    Step 2: Calculate surface arbitrage opportunities
    Exchange: Poloniex
    https://docs.poloniex.com/#introduction
"""


def step_2():
    # Get structured pairs
    with open("structured_triangular_pairs.json") as json_file:
        structured_pairs = json.load(json_file)

    # Get lattest surface prices
    prices_json = func_arbitrage.get_coin_tickers(coin_price_url)

    # Loop through and structure price information
    for t_pair in structured_pairs:
        prices_dict = func_arbitrage.get_price_for_t_pair(
            t_pair, prices_json)
        surface_arb = func_arbitrage.calc_triangular_arb_surface_rate(
            t_pair, prices_dict)

        if len(surface_arb) > 0:
            # print(surface_arb)
            real_rate_arb = func_arbitrage.get_depth_from_order_book(
                surface_arb)
            if "profit_loss" in real_rate_arb:
                print("Starting amount: ", real_rate_arb["starting_amount"])
                print("Final amount: ", real_rate_arb["acquired_coin_t3"])
                print("Profit/loss: ", real_rate_arb["profit_loss"])
                print("% profit/loss: ", real_rate_arb["real_rate_perc"])
                print("-----------------------------------")
                time.sleep(20)


""" MAIN """
if __name__ == "__main__":
    # coin_list = step_0()
    # structured_pairs = step_1(coin_list)

    while True:
        step_2()
