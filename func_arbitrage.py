import requests
import json
import time


# Make a get request
def get_coin_tickers(url):
    req = requests.get(url)
    return json.loads(req.text)


# Loop through each object and find the tradable pairs
def collect_tradables(coin_json):
    coin_list = []
    for coin in coin_json:
        is_frozen = coin_json[coin]["isFrozen"]
        post_only = coin_json[coin]["postOnly"]

        if is_frozen == "0" and post_only == "0":
            coin_list.append(coin)
    return coin_list


# Structure arbitrage Pairs
def structure_triangular_pairs(coin_list):
    triangular_pairs_list = []
    remove_duplicates_list = []
    pairs_list = coin_list[0:]

    # Get pair A
    for pair_a in pairs_list:
        pair_a_split = pair_a.split("_")
        a_base = pair_a_split[0]
        a_quote = pair_a_split[1]

        # Assign A to a box
        a_pair_box = [a_base, a_quote]

        # Get pair B
        for pair_b in pairs_list:
            pair_b_split = pair_b.split("_")
            b_base = pair_b_split[0]
            b_quote = pair_b_split[1]

            if pair_a != pair_b:
                if b_base in a_pair_box or b_quote in a_pair_box:

                    # Get pair C
                    for pair_c in pairs_list:
                        pair_c_split = pair_c.split("_")
                        c_base = pair_c_split[0]
                        c_quote = pair_c_split[1]

                        # Count the number of matching C items
                        if pair_c != pair_a and pair_c != pair_b:
                            combine_all = [pair_a, pair_b, pair_c]
                            pair_box = [a_base, a_quote, b_base,
                                        b_quote, c_base, c_quote]

                            count_c_base = 0
                            for i in pair_box:
                                if i == c_base:
                                    count_c_base += 1

                            count_c_quote = 0
                            for i in pair_box:
                                if i == c_quote:
                                    count_c_quote += 1

                            # Determining triangular match
                            if (count_c_base == 2 and count_c_quote == 2
                                    and c_base != c_quote):
                                combined = pair_a + "," + pair_b + "," + pair_c
                                unique_item = "".join(sorted(combine_all))

                                if unique_item not in remove_duplicates_list:
                                    match_dict = {
                                        "a_base": a_base,
                                        "b_base": b_base,
                                        "c_base": c_base,
                                        "a_quote": a_quote,
                                        "b_quote": b_quote,
                                        "c_quote": c_quote,
                                        "pair_a": pair_a,
                                        "pair_b": pair_b,
                                        "pair_c": pair_c,
                                        "combined": combined
                                    }
                                    triangular_pairs_list.append(match_dict)
                                    remove_duplicates_list.append(unique_item)

    return triangular_pairs_list


# Structure prices
def get_price_for_t_pair(t_pair, prices_json):
    # Extract pair info
    pair_a = t_pair["pair_a"]
    pair_b = t_pair["pair_b"]
    pair_c = t_pair["pair_c"]

    # Extract price information for give pairs
    pair_a_ask = float(prices_json[pair_a]["lowestAsk"])
    pair_a_bid = float(prices_json[pair_a]["highestBid"])
    pair_b_ask = float(prices_json[pair_b]["lowestAsk"])
    pair_b_bid = float(prices_json[pair_b]["highestBid"])
    pair_c_bid = float(prices_json[pair_c]["highestBid"])
    pair_c_ask = float(prices_json[pair_c]["lowestAsk"])

    # Output dictionary
    return {
        "pair_a_ask": pair_a_ask,
        "pair_a_bid": pair_a_bid,
        "pair_b_ask": pair_b_ask,
        "pair_b_bid": pair_b_bid,
        "pair_c_ask": pair_c_ask,
        "pair_c_bid": pair_c_bid
    }


# Calculate surface rate arbitrage opportunity
def calc_triangular_arb_surface_rate(t_pair, prices_dict):
    # Amount of the starting coin (Coin you have at hand)
    starting_amount = 1
    min_surface_rate = 0
    surface_dict = {}

    # Which pair is being transacted
    # (pair_a, pair_b, pair_c)
    contract_2 = ""
    contract_3 = ""

    # Direction of trade (base_to_quote) or (quote_to_base)
    direction_trade_1 = ""
    direction_trade_2 = ""
    direction_trade_3 = ""

    # Acquired coin after each transaction
    acquired_coin_t2 = 0
    acquired_coin_t3 = 0

    # Whether the calculation is over or not
    calculated = 0

    # Extract pair variables
    a_base = t_pair["a_base"]
    a_quote = t_pair["a_quote"]
    b_base = t_pair["b_base"]
    b_quote = t_pair["b_quote"]
    c_base = t_pair["c_base"]
    c_quote = t_pair["c_quote"]
    pair_a = t_pair["pair_a"]
    pair_b = t_pair["pair_b"]
    pair_c = t_pair["pair_c"]

    # Extract price information
    a_ask = prices_dict["pair_a_ask"]
    a_bid = prices_dict["pair_a_bid"]
    b_ask = prices_dict["pair_b_ask"]
    b_bid = prices_dict["pair_b_bid"]
    c_ask = prices_dict["pair_c_ask"]
    c_bid = prices_dict["pair_c_bid"]

    # Set directions and loop through
    direction_list = ["forward", "reverse"]
    for direction in direction_list:
        calculated = 0

        # Set additional variables for swap information
        swap_1 = ""
        swap_2 = ""
        swap_3 = ""
        swap_1_rate = 0  # Rate of exchange for transaction 1 (t1)
        swap_2_rate = 0  # Rate of exchange for transaction 2 (t2)
        swap_3_rate = 0  # Rate of exchange for transaction 3 (t3)

        """
            Polonied Exchange!
            If we are swapping the coin on the left (Base) with the coin on
            the right (Quote) then we divide by the ask (or mulitply by 1 / 
            ask)
            If we are swapping the coin on the right (Quote) wih tehe coin on
            the left (Base) then we multiply by the bid
        """
        # Assume we are starting with a_base and swapping for a_quote
        if direction == "forward":
            swap_1 = a_base
            swap_2 = a_quote
            swap_1_rate = 1 / a_ask
            direction_trade_1 = "base_to_quote"

        # Assumte we are stargin with a_quote and swapping for a_base
        if direction == "reverse":
            swap_1 = a_quote
            swap_2 = a_base
            swap_1_rate = a_bid
            direction_trade_1 = "quote_to_base"

        # Place first trade
        contract_1 = pair_a
        acquired_coin_t1 = swap_1_rate * starting_amount

        """ FORWARD """
        if direction == "forward":
            """ SCENARIO 1: a_quote matching b_quote """
            # Check if a_quote matches b_quote
            if a_quote == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_b

                # Check if b_base (acquired coin) matches c_base
                if b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # Check if b_base (acquired coin) matches c_quote
                if b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            """ SCENARIO 2: a_quote matching b_base """
            # Check if a_quote is equal to b_base
            if a_quote == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_b

                # Check if b_quote (acquired coin) matches c_base
                if b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # Check if b_quote (acquired coin) matches c_quote
                if b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            """ SCENARIO 3: a_quote matching c_quote """
            # Check if a_quote matches c_quote
            if a_quote == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_c

                # Check if c_base (acquired coin) matches b_base
                if c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # Check if c_base (acquired coin) matches b_quote
                if c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            """ SCENARIO 4: a_quote matching c_base """
            # Check if a_quote is equal to c_base
            if a_quote == c_base and calculated == 0:

                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_c

                # Check if c_quote (acquired coin) matches b_base
                if c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # Check if c_quote (acquired coin) matches b_quote
                if c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        """ REVERSE """
        if direction == "reverse":
            """ SCENARIO 1: a_base matching b_quote """
            # Check if a_base matches b_quote
            if a_base == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_b

                # Check if a_base (acquired coin) matches c_base
                if b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # Check if b_base (acquired coin) matches c_quote
                if b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            """ SCENARIO 2: a_base matching b_base """
            # Check if a_base is equal to b_base
            if a_base == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_b

                # Check if b_quote (acquired coin) matches c_base
                if b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_c

                # Check if b_quote (acquired coin) matches c_quote
                if b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_c

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            """ SCENARIO 3: a_base matching c_quote """
            # Check if a_base matches c_quote
            if a_base == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "quote_to_base"
                contract_2 = pair_c

                # Check if c_base (acquired coin) matches b_base
                if c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # Check if c_base (acquired coin) matches b_quote
                if c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            """ SCENARIO 4: a_base matching c_base """
            # Check if a_base is equal to c_base
            if a_base == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = "base_to_quote"
                contract_2 = pair_c

                # Check if c_quote (acquired coin) matches b_base
                if c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = "base_to_quote"
                    contract_3 = pair_b

                # Check if c_base (acquired coin) matches b_quote
                if c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = "quote_to_base"
                    contract_3 = pair_b

                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        """ PROFIT / LOSS OUTPUT """
        # Profit and loss calculations
        profit_loss = acquired_coin_t3 - starting_amount
        profit_loss_perc = (profit_loss / starting_amount) * \
            100 if profit_loss != 0 else 0

        # Trade Descriptions
        trade_description_1 = f"""Start with {swap_1} of {starting_amount}.
            Swap at {swap_1_rate} for {swap_2} acquiring {acquired_coin_t1}"""
        trade_description_2 = f"""Swap {acquired_coin_t1} of {swap_2} at 
            {swap_2_rate} for {swap_3} acquiring {acquired_coin_t2}"""
        trade_description_3 = f"""Swap {acquired_coin_t2} of {swap_3} at 
            {swap_3_rate} for {swap_1} acquiring {acquired_coin_t3}"""

        # Output Results
        if profit_loss_perc > min_surface_rate:
            surface_dict = {
                "swap_1": swap_1,
                "swap_2": swap_2,
                "swap_3": swap_3,
                "contract_1": contract_1,
                "contract_2": contract_2,
                "contract_3": contract_3,
                "direction_trade_1": direction_trade_1,
                "direction_trade_2": direction_trade_2,
                "direction_trade_3": direction_trade_3,
                "starting_amount": starting_amount,
                "acquired_coin_t1": acquired_coin_t1,
                "acquired_coin_t2": acquired_coin_t2,
                "acquired_coin_t3": acquired_coin_t3,
                "swap_1_rate": swap_1_rate,
                "swap_2_rate": swap_2_rate,
                "swap_3_rate": swap_3_rate,
                "profit_loss": profit_loss,
                "profit_loss_perc": profit_loss_perc,
                "direction": direction,
                "trade_description_1": trade_description_1,
                "trade_description_2": trade_description_2,
                "trade_description_3": trade_description_3
            }
            return surface_dict
    return surface_dict


# Reformat orderbook for depth calculation
def reformat_orderbook(prices, c_direction):
    price_list_main = []

    if c_direction == "base_to_quote":
        for price in prices["asks"]:
            ask_price = float(price[0])
            adjusted_price = 1 / ask_price if ask_price != 0 else 0
            adjusted_quantity = float(price[1]) * ask_price
            price_list_main.append([adjusted_price, adjusted_quantity])
    elif c_direction == "quote_to_base":
        for price in prices["bids"]:
            bid_price = float(price[0])
            adjusted_price = bid_price if bid_price != 0 else 0
            adjusted_quantity = float(price[1])
            price_list_main.append([adjusted_price, adjusted_quantity])

    return price_list_main


# Get acquired coin for depth calculation (aka Depth calculation)
"""
        CHALLENGE
        Full amount of starting amount can be eaten on the first level
        (level 0)
        Some of the starting amount can be eaten up by multiple levels
        Some coins may not have enough liquidity
    """


def calculate_acquired_coin(amount_in, order_book):
    # Initialize variables
    trading_balance = amount_in
    quantity_bought = 0
    acquired_coin = 0
    counts = 0

    for level in order_book:
        # Extract the level price and quantity
        level_price = level[0]
        level_available_quantity = level[1]

        # Full amount of starting amount can be eaten on the first level 
        # (level 0)
        # Amount in is <= first_level_total_amount
        if trading_balance <= level_available_quantity:
            quantity_bought = trading_balance
            trading_balance = 0
            amount_bought = quantity_bought * level_price
        elif trading_balance > level_available_quantity:
            quantity_bought = level_available_quantity
            trading_balance -= quantity_bought
            amount_bought = quantity_bought * level_price

        # Accumulate acquired coin
        acquired_coin += amount_bought

        # Exit trade if there is no trading_balance left
        if trading_balance == 0:
            return acquired_coin

        # Exit if not enough order book levels
        counts += 1
        if counts == len(order_book):
            return int(0)


# Get the depth from the orderbook
def get_depth_from_order_book(surface_arb):

    # Extract initial variables
    swap_1 = surface_arb["swap_1"]
    starting_amount = 100
    starting_amount_dict = {"BTC": 0.05, "ETH": 0.1}

    if swap_1 in starting_amount_dict:
        starting_amount = starting_amount_dict[swap_1]

    # Define pairs
    contract_1 = surface_arb["contract_1"]
    contract_2 = surface_arb["contract_2"]
    contract_3 = surface_arb["contract_3"]

    # Define direction for trades
    contract_1_direction = surface_arb["direction_trade_1"]
    contract_2_direction = surface_arb["direction_trade_2"]
    contract_3_direction = surface_arb["direction_trade_3"]

    # Get orderbook for first trade assesment
    url1 = f"""https://poloniex.com/public?command=returnOrderBook
        &currencyPair={contract_1}&depth=20"""
    depth_1_prices = get_coin_tickers(url1)
    if len(depth_1_prices["asks"]) == 0 or len(depth_1_prices["bids"]) == 0:
        return {}
    depth_1_reformatted_prices = reformat_orderbook(
        depth_1_prices, contract_1_direction)
    time.sleep(0.3)

    url2 = f"""https://poloniex.com/public?command=returnOrderBook&
        currencyPair={contract_2}&depth=20"""
    depth_2_prices = get_coin_tickers(url2)
    if len(depth_2_prices["asks"]) == 0 or len(depth_2_prices["bids"]) == 0:
        return {}
    depth_2_reformatted_prices = reformat_orderbook(
        depth_2_prices, contract_2_direction)
    time.sleep(0.3)

    url3 = f"""https://poloniex.com/public?command=returnOrderBook&
        currencyPair={contract_3}&depth=20"""
    depth_3_prices = get_coin_tickers(url3)
    if len(depth_3_prices["asks"]) == 0 or len(depth_3_prices["bids"]) == 0:
        return {}
    depth_3_reformatted_prices = reformat_orderbook(
        depth_3_prices, contract_3_direction)

    # Get acquired coin for trade1
    acquired_coin_t1 = calculate_acquired_coin(
        starting_amount, depth_1_reformatted_prices)
    acquired_coin_t2 = calculate_acquired_coin(
        acquired_coin_t1, depth_2_reformatted_prices)
    acquired_coin_t3 = calculate_acquired_coin(
        acquired_coin_t2, depth_3_reformatted_prices)

    # Calculate profit loss (Also known as real rate)
    profit_loss = acquired_coin_t3 - starting_amount
    real_rate_perc = (profit_loss / starting_amount) * \
        100 if profit_loss != 0 else 0

    if real_rate_perc > -1:
        return {
            "starting_amount": starting_amount,
            "acquired_coin_t3": acquired_coin_t3,
            "profit_loss": profit_loss,
            "real_rate_perc": real_rate_perc,
            "contract_1": contract_1,
            "contract_2": contract_2,
            "contract_3": contract_3,
            "contract_1_direction": contract_1_direction,
            "contract_2_direction": contract_2_direction,
            "contract_3_direction": contract_3_direction,
        }
    else:
        return {}
