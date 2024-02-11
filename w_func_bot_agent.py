from func_private import place_market_order, check_order_status
from datetime import datetime, timedelta
import time
from func_messaging import send_message

from pprint import pprint

# Class: Agent for managing opening and checking trades
class BotAgent:
     
    """
        Primary function of BotAgent handles opening and checking order status
    """
    
    # Initialize class
    def __init__(
        self,
        client,
        market_1,
        market_2,
        base_side,
        base_size,
        base_price,
        quote_side,
        quote_size,
        quote_price,
        accept_failsafe_base_price,
        z_score,
        half_life,
        hedge_ratio,
    ):
        # Initialize class variables (link parameters and attributes)
        self.client = client
        self.market_1 = market_1
        self.market_2 = market_2
        self.base_side = base_side
        self.base_size = base_size
        self.base_price = base_price
        self.quote_side = quote_side
        self.quote_size = quote_size
        self.quote_price = quote_price
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.half_life = half_life
        self.hedge_ratio = hedge_ratio
        
        # Initialize output variable
        # Pair status options are FAILED, LIVE, CLOSE, ERROR
        self.order_dict = {
            "market_1": market_1,
            "market_2": market_2,
            "hedge_ratio": hedge_ratio,
            "z_score": z_score,
            "half_life": half_life,
            "order_id_m1": "",
            "order_m1_size": base_size,
            "order_m1_side": base_side,
            "order_time_m1": "", # how long since the order created
            "order_id_m2": "",
            "order_m2_size": quote_size,
            "order_m2_side": quote_side,
            "order_time_m2": "", # how long since the order created
            "pair_status": "",
            "comment": ""
        }
        
    # Check order status by id (After placing an order? )
    def check_order_status_by_id(self, order_id):
        
        # Allow time to process
        time.sleep(2)
        
        # Check order status
        order_status = check_order_status(self.client, order_id)

        # Guard: If order cancelled move onto next pair
        if order_status == "CANCELED":
            print(f"{self.market_1} vs {self.market_2} - Order cancelled...")
            self.order_dict["pair_status"] = "FAILED"
            return "failed"
        
        # Guard: If order not filled wait until order expiration
        if order_status != "FAILED":
            time.sleep(15)
            order_status = check_order_status(self.client, order_id)
            
            # Guard: If order cancelled move onto next pair (again)
            if order_status == "CANCELED":
                print(f"{self.market_1} vs {self.market_2} - Order cancelled...")
                self.order_dict["pair_status"] = "FAILED"
                return "failed"
            
            # Guard: If not filled, cancel order
            if order_status != "FILLED":
                self.client.private.cancel_order(order_id=order_id)
                self.order_dict["pair_status"] = "ERROR"
                print(f"{self.market_1} vs {self.market_2} - Order error...")
                return "error"
            
        # Return live
        return "live"
        
    # Open trades
    def open_trades(self):
        
        print("===== Manage Entries =====")
        print(f"Placing trade for {self.market_1} & {self.market_2}")

        # Print status - Opening first order
        print(f"- Placing first order: {self.market_1}...")
        print(f"-- Side: {self.base_side}, Size: {self.base_size}, Price: {self.base_price}")
        
        # Place Base Order
        try:
            base_order = place_market_order(
                self.client,
                market=self.market_1,
                side=self.base_side,
                size=self.base_size,
                price=self.base_price,
                reduce_only=False
            )
            
            # Store the order id
            self.order_dict["order_id_m1"] = base_order["order"]["id"]
            self.order_dict["order_time_m1"] = datetime.now().isoformat()
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 1 {self.market_1}: {e}"
            print("-- Error: placing base order - 101")
            return self.order_dict
        
        # ===================== debug - start ===========================
        
        # Check base order status
        base_order_status = self.client.private.get_order_by_id(self.order_dict["order_id_m1"]).data["order"]["status"]
        
        time.sleep(0.5)
        # Proceed when only base order is "FILLED"
        if base_order_status == "FILLED":
            
            # Place quote order
            try:
                print("- Base order placed successfully. Now placing quote order...")
                quote_order = place_market_order(
                    self.client,
                    market=self.market_2,
                    side=self.quote_side,
                    size=self.quote_size,
                    price=self.quote_price,
                    reduce_only=False
                )
                
                # Store the order id
                self.order_dict["order_id_m2"] = quote_order["order"]["id"]
                self.order_dict["order_time_m2"] = datetime.now().isoformat()
            except Exception as e:
                self.order_dict["pair_status"] = "ERROR"
                self.order_dict["comments"] = f"Market 2 {self.market_2}: {e}"
                print(" - Error: placing quote order - 102")
                exit(1)
            
            # Check if quote order is NOT "FILLED"
            time.sleep(0.5)
            if self.client.private.get_order_by_id(self.order_dict["order_id_m2"]).data["order"]["status"] != "FILLED":
                print("- Failed placing quote order.")
                # Cancel the quote order which is not filled yet
                
                try:
                    print("-- Now Cancelling the quote order...")
                    self.client.private.cancel_order(order_id=self.order_dict["order_id_m2"])
                except Exception as e:
                    self.order_dict["pair_status"] = "ERROR"
                    self.order_dict["comments"] = f"Close Market 2 {self.market_2}: {e}"
                    print(" - Error: cancelling quote order - 103")
                    print("ABORT PROGRAM")
                    print("Unexpected Error")
                    exit(1)
                
                # Proceed only if quote order is cancelled
                time.sleep(0.5)
                if self.client.private.get_order_by_id(self.order_dict["order_id_m2"]).data["order"]["status"] != "CANCELED":
                    self.order_dict["pair_status"] = "ERROR"
                    self.order_dict["comments"] = f"Market 2 {self.market_2}: {e}"
                    print(" -- Failed canceling quote order")
                    exit(1)
                
                # Place reduce-only order for base order
                try:
                    print("-- Now placing reduce-only order for base order...")
                    close_order = place_market_order(
                        self.client,
                        market=self.market_1,
                        side=self.quote_side,
                        size=self.base_size,
                        price=self.accept_failsafe_base_price,
                        reduce_only=True
                    )
                    
                    # Ensure order is live before proceeding
                    time.sleep(2)
                    order_status_close_order = self.client.private.get_order_by_id(close_order["order"]["id"]).data["order"]["status"]
                    if order_status_close_order != "FILLED":
                        print("ABORT PROGRAM")
                        print("Unexpected Error")
                        print(" - Fail placing reduce-only order for base order")
                        
                        # !!!!!!!!!!!!! CONSIDER SENDING MESSAGE HERE !!!!!!!!!!!!
                        send_message("Failed to execute. Code Red! Error code: 104")
                        
                        # ABORT
                        exit(1)
                    
                except Exception as e:
                    self.order_dict["pair_status"] = "ERROR"
                    self.order_dict["comments"] = f"Close Market 1 {self.market_1}: {e}"
                    print("ABORT PROGRAM")
                    print("Unexpected Error")

                
                    # !!!!!!!!!!!!! CONSIDER SENDING MESSAGE HERE !!!!!!!!!!!!
                    send_message("Failed to execute. Code Red! Error code: 105")
                    
                    # ABORT
                    exit(1)
            
            # Both base and quote are FILLED
            print("Both base and quote are FILLED")
            self.order_dict["pair_status"] = "LIVE"
            return self.order_dict
        else: # If base order is not FILLED
            # Cancel the base order
            try:
                print("-- Now Cancelling the base order...")
                self.client.private.cancel_order(order_id=self.order_dict["order_id_m1"])
                
                
                # Ensure order is canceled before proceeding
                time.sleep(2)
                
                # If base order NOT canceled successfully
                if self.client.private.get_order_by_id(self.order_dict["order_id_m1"]).data["order"]["status"] != "CANCELED":
                    print("ABORT PROGRAM")
                    print("Unexpected Error")
                    print("Error canceling base order - 106")
                    
                    # !!!!!!!!!!!!! CONSIDER SENDING MESSAGE HERE !!!!!!!!!!!!
                    send_message("Failed to execute. Code Red! Error code: 106")
                    
                    # ABORT
                    exit(1)
                # If base order canceled successfully
                else:
                    self.order_dict["pair_status"] = "failed"
                    print("")
                    return self.order_dict
                
            except Exception as e:
                self.order_dict["pair_status"] = "ERROR"
                self.order_dict["comments"] = f"Close Market 1 {self.market_1}: {e}"
                print("ABORT PROGRAM")
                print("Unexpected Error")
                print("Error canceling base order - 107")
                
                # !!!!!!!!!!!!! CONSIDER SENDING MESSAGE HERE !!!!!!!!!!!!
                send_message("Failed to execute. Code Red! Error code: 107")
                
                # ABORT
                exit(1)
        
        # ===================== debug - end =============================
        
        # # Ensure order is live before processing
        # order_status_m1 = self.check_order_status_by_id(self.order_dict["order_id_m1"])
        
        
        # # Guard: Abort if order failed
        # if order_status_m1 != "live":
        #     self.order_dict["pair_status"] = "ERROR"
        #     self.order_dict["comments"] = f"{self.market_1} failed to fill"
        #     return self.order_dict
        
        # # Print status - Opening second order
        # print("---")
        # print(f"{self.market_2}: Placing second order...")
        # print(f"Side: {self.quote_side}, Size: {self.quote_size}, Price: {self.quote_price}")
        # print("---")
        
        # # Place Quote Order
        # try:
        #     quote_order = place_market_order(
        #         self.client,
        #         market=self.market_2,
        #         side=self.quote_side,
        #         size=self.quote_size,
        #         price=self.quote_price,
        #         reduce_only=False
        #     )
            
        #     # Store the order id
        #     self.order_dict["order_id_m2"] = quote_order["order"]["id"]
        #     self.order_dict["order_time_m2"] = datetime.now().isoformat()
        # except Exception as e:
        #     self.order_dict["pair_status"] = "ERROR"
        #     self.order_dict["comments"] = f"Market 2 {self.market_2}: {e}"
        #     return self.order_dict
        
        # # Ensure order is live before processing
        # order_status_m2 = self.check_order_status_by_id(self.order_dict["order_id_m2"])
        
        # # Guard: Abort if order failed

        # if order_status_m2 != "live":
        #     self.order_dict["pair_status"] = "ERROR"
        #     self.order_dict["comments"] = f"{self.market_2} failed to fill"
        
        #     # Close first order (base order) if second failed
        #     try:
        #         print("Cancelling the first order due to the second failed...")
        #         close_order = place_market_order(
        #             self.client,
        #             market=self.market_1,
        #             side=self.quote_side,
        #             size=self.base_size,
        #             price=self.accept_failsafe_base_price,
        #             reduce_only=True
        #         )
                
        #         # Ensure order is live before proceeding
        #         time.sleep(2)
        #         order_status_close_order = check_order_status(self.client, close_order["order"]["id"])
        #         if order_status_close_order != "FILLED":
        #             print("ABORT PROGRAM")
        #             print("Unexpected Error")
        #             print(order_status_close_order)
                    
        #             # !!!!!!!!!!!!! CONSIDER SENDING MESSAGE HERE !!!!!!!!!!!!
        #             send_message("Failed to execute. Code Red! Error code: 100")
                    
        #             # ABORT
        #             exit(1)
                
        #     except Exception as e:
        #         self.order_dict["pair_status"] = "ERROR"
        #         self.order_dict["comments"] = f"Close Market 1 {self.market_1}: {e}"
        #         print("ABORT PROGRAM")
        #         print("Unexpected Error")
        #         print(order_status_close_order)
                
        #         # !!!!!!!!!!!!! CONSIDER SENDING MESSAGE HERE !!!!!!!!!!!!
        #         send_message("Failed to execute. Code Red! Error code: 101")
                
        #         # ABORT
        #         exit(1)
                
        # # Return success result
        # else:
        #     self.order_dict["pair_status"] = "LIVE"
        #     return self.order_dict
    
    