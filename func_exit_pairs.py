from constants import CLOSE_AT_ZSCORE_CROSS, EXIT_WHEN_CROSS_ZERO
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from func_private import place_market_order
from func_messaging import send_message # debug
import json
import time

from pprint import pprint

# Close positions
def manage_trade_exits(client):
    
    """
        Manage exiting open positions
        Based upon criteria set in constants
    """
    
    # Initialize saving output
    save_output = []
    
    # Opening JSON file
    try:
        open_positions_file = open("bot_agents.json")
        open_positions_dict = json.load(open_positions_file)
        print(f"{len(open_positions_dict)} pairs extracted from json file") # debug
        
    except:
        # In case no file exists
        return "complete"
    
    # Guard: Exit if no open positions in file
    if len(open_positions_dict) < 1:
        return "complete"
    
    # Get all open positions per trading platform
    exchange_pos = client.private.get_positions(status="OPEN")
    all_exc_pos = exchange_pos.data["positions"]
    markets_live = []
    for p in all_exc_pos:
        markets_live.append(p["market"])

    # Protect API
    time.sleep(0.5)
    
    # Check all saved positions match order record
    # Exit trade according to any exit trade rules
    for position in open_positions_dict:
        
        # Initialize is_close_trigger
        is_close = False
        
        # Get market info from the saved file
        # Extract position matching information from file - market 1
        position_market_m1 = position["market_1"]
        position_size_m1 = position["order_m1_size"]
        position_side_m1 = position["order_m1_side"]
        
        # Extract position matching information from file - market 2
        position_market_m2 = position["market_2"]
        position_size_m2 = position["order_m2_size"]
        position_side_m2 = position["order_m2_side"]
        
        print("") 
        
        # Protect API
        time.sleep(0.5)
        
        # Get order info m1 from DYDX
        order_m1 = client.private.get_order_by_id(position["order_id_m1"])
        order_market_m1 = order_m1.data["order"]["market"]
        order_size_m1 = order_m1.data["order"]["size"]
        order_side_m1 = order_m1.data["order"]["side"]
        
        # Use "position_size_m1" to format "order_size_m1" 
        # To fix: position_size_m1(2.0) != order_size_m1(2)
        order_size_m1 = float(order_size_m1)
        position_size_m1 = float(position_size_m1)
        order_size_m1 = format_number(order_size_m1, position_size_m1) # str
        position_size_m1 = str(position_size_m1) # str
        
        # Protect API
        time.sleep(0.5)
        
        # Get order info m2 from DYDX
        order_m2 = client.private.get_order_by_id(position["order_id_m2"])
        order_market_m2 = order_m2.data["order"]["market"]
        order_size_m2 = order_m2.data["order"]["size"]
        order_side_m2 = order_m2.data["order"]["side"]
        
        # Use "position_size_m2" to format "order_size_m2" 
        # To fix: position_size_m2(2.0) != order_size_m2(2)
        order_size_m2 = float(order_size_m2)
        position_size_m2 = float(position_size_m2)
        order_size_m2 = format_number(order_size_m2, position_size_m2) # str
        position_size_m2 = str(position_size_m2) # str
        
        # Perform matching check
        check_m1 = position_market_m1 == order_market_m1 and position_size_m1 == order_size_m1 and position_side_m1 == order_side_m1
        check_m2 = position_market_m2 == order_market_m2 and position_size_m2 == order_size_m2 and position_side_m2 == order_side_m2
        check_live = position_market_m1 in markets_live and position_market_m2 in markets_live

        # Guard: If not all match exit with error
        if not check_m1 or not check_m2 or not check_live:
            print(f"Warning: Not all open positions match exchange records for {position_market_m1} and {position_market_m2}")
            send_message(f"Warning: Not all open positions match exchange records for {position_market_m1} and {position_market_m2}")
            
            print("check_m1: ", check_m1) # debug
            print(position_market_m1, order_market_m1) # debug
            print(position_size_m1, order_size_m1) # debug
            print(type(position_size_m1), type(order_size_m1)) # debug
            print(position_side_m1, order_side_m1) # debug
            print("check_m2: ", check_m2) # debug
            print(position_market_m2, order_market_m2) # debug
            print(position_size_m2, order_size_m2) # debug
            print(type(position_size_m2), type(order_size_m2)) # debug
            print(position_side_m2, order_side_m2) # debug
            print("check_live: ", check_live) # debug
            print(position_market_m1 in markets_live) # debug
            print(position_market_m2 in markets_live) # debug
            exit(1) # debug
            continue
        
        # Get prices
        series_1 = get_candles_recent(client, position_market_m1)
        time.sleep(0.2)
        series_2 = get_candles_recent(client, position_market_m2)
        time.sleep(0.2)
        
        # Get markets for reference of tick size
        markets = client.public.get_markets().data
        
        # Protect API
        time.sleep(0.2)

        # Trigger close based on Z-score
        if CLOSE_AT_ZSCORE_CROSS:
            
            # Initialize z_score (retrieved from csv)
            hedge_ratio = position["hedge_ratio"]
            z_score_traded = position["z_score"] # When opened the trade
            if len(series_1) > 0 and len(series_1) == len(series_2):
                spread = series_1 - (hedge_ratio * series_2)
                z_score_current = calculate_zscore(spread).values.tolist()[-1]
            
            # Determine trigger: cross "zero" (default) or cross "opposite of z_score_traded"
            if EXIT_WHEN_CROSS_ZERO:
                z_score_level_check = abs(z_score_current) >= 0 # cross OPTION_1: "zero"
            else:
                z_score_level_check = abs(z_score_current) >= abs(z_score_traded) # cross OPTION_2: "opposite of z_score_traded"
            
            z_score_cross_check = (z_score_current < 0 and z_score_traded > 0) or (z_score_current > 0 and z_score_traded < 0)
            
            # Close trade
            if z_score_level_check and z_score_cross_check:
                
                # Initialize close trigger
                is_close = True
                
            ########### William's note (start) #############
            
            z_score_target = 0 if EXIT_WHEN_CROSS_ZERO else (z_score_traded * -1)
            
            print(f"===== Checking exit opportunity for pair: {position_market_m1} & {position_market_m2} =====")
            print(f"z_score_traded: {z_score_traded}")
            print(f"z_score_current: {z_score_current}")
            print(f"z_score_target: {z_score_target}")
            
            print(f"z_score left to exit: {round(abs(z_score_target - z_score_current) / abs(z_score_target - z_score_traded) * 100, 1)} %") 
            print(f"To close: {is_close}")

            print(f"==================================================================")
            ########### William's note (start) #############
                
        ###
        # Add any other close logic you want here
        # Trigger is_close
        ###
        
        # Close positions if triggered
        # TODO: Remove "not" for production
        if is_close: 
            # print("++++++++++ If NOT is_close ++++++++++")
            
            print("")
            print("===")
            print(f"Closing trade: {position_market_m1} & {position_market_m2}")
            
            # determine side - m1
            side_m1 = "SELL"
            if position_side_m1 == "SELL":
                side_m1 = "BUY"
            
            # determine side - m2
            side_m2 = "SELL"
            if position_side_m2 == "SELL":
                side_m2 = "BUY"
                
            # Get and format prices
            price_m1 = float(series_1[-1])
            price_m2 = float(series_2[-1])
            accept_price_m1 = price_m1 * 1.05 if side_m1 == "BUY" else price_m1 * 0.95
            accept_price_m2 = price_m2 * 1.05 if side_m2 == "BUY" else price_m2 * 0.95
            tick_size_m1 = markets["markets"][position_market_m1]["tickSize"]
            tick_size_m2 = markets["markets"][position_market_m2]["tickSize"]
            accept_price_m1 = format_number(accept_price_m1, tick_size_m1)
            accept_price_m2 = format_number(accept_price_m2, tick_size_m2)
            
            # Close positions
            try:
                
                # close positions for market 1
                print(">>> Closing market 1 <<<")
                print(f"Closing position for {position_market_m1}")
                
                close_order_m1 = place_market_order(
                    client, 
                    market=position_market_m1, 
                    side=side_m1, 
                    size=position_size_m1, 
                    price=accept_price_m1, 
                    reduce_only=True
                )
                
                print(close_order_m1["order"]["id"])
                print(">>> Market 1 Closed <<<")
                
                # Protect API
                time.sleep(1)
                
                # close positions for market 2
                print(">>> Closing market 2 <<<")
                print(f"Closing position for {position_market_m2}")
                
                close_order_m2 = place_market_order(
                    client, 
                    market=position_market_m2, 
                    side=side_m2, 
                    size=position_size_m2, 
                    price=accept_price_m2, 
                    reduce_only=True
                )
                
                print(close_order_m2["order"]["id"])
                print(">>> Market 2 Closed <<<")
                print("===")
                print("")
                
                # ===== W's note - start =====
                
                # Get position_market_m1
                closed_position_m1 = client.private.get_positions(
                    market=position_market_m1,
                    status="CLOSED",
                    limit=1
                    ) 
                print(f"closed_position_m1({closed_position_m1.data['positions'][0]['market']}) - realizedPnl: {closed_position_m1.data['positions'][0]['realizedPnl']}")
                
                # Get position_market_m2
                closed_position_m2 = client.private.get_positions(
                    market=position_market_m2,
                    status="CLOSED",
                    limit=1
                    ) 
                print(f"closed_position_m2({closed_position_m2.data['positions'][0]['market']}) - realizedPnl: {closed_position_m2.data['positions'][0]['realizedPnl']}")
                
                # Sum PNL
                print(f'Total PNL: {float(closed_position_m1.data["positions"][0]["realizedPnl"]) + float(closed_position_m2.data["positions"][0]["realizedPnl"])}')
                
                send_message(f'Total PNL: {float(closed_position_m1.data["positions"][0]["realizedPnl"]) + float(closed_position_m2.data["positions"][0]["realizedPnl"])}')
                
                # ===== W's note - end   =====
                
                send_message(f"Exited position_market_m1: {position_market_m1} & position_market_m2: {position_market_m2}")
                
                
                
            except Exception as e:
                print(f"Exit failed for {position_market_m1} with {position_market_m2}")
                save_output.append(position)
                
        # Keep record of items and save
        else:
            save_output.append(position)

    # Save remaining items
    print(f"{len(save_output)} pairs remaining open. Saving json file...")
    with open("bot_agents.json", "w") as f:
        json.dump(save_output, f)
        
    return "complete" # ============
    

