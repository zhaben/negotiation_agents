#!/usr/bin/env python3
"""
Seller Agent - Responds to buyer offers and negotiates prices
Uses shared JSON file for communication with buyer agents
"""

import json
import time
import random
import asyncio
from datetime import datetime

class SellerAgent:
    def __init__(self, agent_id="seller_001"):
        self.agent_id = agent_id
        self.negotiations_file = "negotiations.json"
        
        # Seller items and minimum acceptable prices
        self.inventory = {
            "1": {
                "title": "iPhone 12 Pro",
                "asking_price": 520,
                "minimum_price": 420,  # Won't go below this
                "category": "Electronics",
                "urgency": 0.3  # 0.3 = not urgent to sell (higher = more willing to negotiate)
            },
            "2": {
                "title": "Vintage Leather Sofa",
                "asking_price": 350,
                "minimum_price": 250,
                "category": "Furniture",
                "urgency": 0.7  # More urgent to sell
            },
            "3": {
                "title": "Mountain Bike",
                "asking_price": 850,
                "minimum_price": 700,
                "category": "Sports",
                "urgency": 0.5  # Moderate urgency
            }
        }
        
        # Negotiation strategy parameters
        self.initial_discount = 0.05   # Initial 5% discount from asking price
        self.max_discount_per_round = 0.03  # Max 3% additional discount per round
        self.patience_threshold = 3    # Start getting more flexible after 3 rounds
        
    def load_negotiations(self):
        """Load current negotiations from JSON file"""
        try:
            with open(self.negotiations_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"active_negotiations": {}, "completed_negotiations": [], "agent_status": {}}
    
    def save_negotiations(self, data):
        """Save negotiations to JSON file"""
        with open(self.negotiations_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_counter_offer(self, negotiation):
        """Calculate counter-offer based on strategy and item specifics"""
        item_id = negotiation["item_id"]
        if item_id not in self.inventory:
            return negotiation["asking_price"]
        
        item = self.inventory[item_id]
        asking_price = item["asking_price"]
        minimum_price = item["minimum_price"]
        urgency = item["urgency"]
        round_num = negotiation["round"]
        buyer_offer = negotiation["current_offer"]
        
        # Base discount starts small and increases with rounds and urgency
        base_discount = self.initial_discount + (round_num - 1) * self.max_discount_per_round
        urgency_bonus = urgency * 0.1  # Up to 10% additional discount based on urgency
        
        total_discount = min(base_discount + urgency_bonus, 0.25)  # Cap at 25% discount
        
        # Calculate our counter-offer
        counter_offer = int(asking_price * (1 - total_discount))
        
        # Never go below minimum price
        counter_offer = max(counter_offer, minimum_price)
        
        # If buyer's offer is close to our counter (within 5%), meet them halfway
        if abs(buyer_offer - counter_offer) <= (asking_price * 0.05):
            counter_offer = (buyer_offer + counter_offer) // 2
            counter_offer = max(counter_offer, minimum_price)
        
        # If buyer's offer is already above our minimum and we're urgent, consider accepting
        if buyer_offer >= minimum_price and urgency > 0.6 and round_num >= 2:
            if random.random() < urgency:  # Random chance based on urgency
                return buyer_offer  # Accept their offer
        
        return counter_offer
    
    def generate_response_message(self, negotiation, counter_offer):
        """Generate a contextual response message"""
        item = self.inventory[negotiation["item_id"]]
        buyer_offer = negotiation["current_offer"]
        asking_price = item["asking_price"]
        round_num = negotiation["round"]
        
        # Different message styles based on the situation
        if counter_offer == buyer_offer:
            # Accepting their offer
            messages = [
                f"You've got a deal at ${counter_offer}! When would you like to pick it up?",
                f"${counter_offer} works for me. This {item['title']} is yours!",
                f"Sold! ${counter_offer} it is. I'll hold it for you."
            ]
        elif counter_offer > buyer_offer * 1.1:
            # Big gap, firm on price
            messages = [
                f"I appreciate the offer, but ${counter_offer} is the best I can do. This {item['title']} is worth every penny!",
                f"I can come down to ${counter_offer}, but that's really pushing it for such a quality item.",
                f"How about ${counter_offer}? I've had a lot of interest in this {item['title']}."
            ]
        else:
            # Getting closer, more flexible
            messages = [
                f"You're getting closer! I could do ${counter_offer}. What do you think?",
                f"Let's meet at ${counter_offer} - that's a fair price for both of us.",
                f"I'm willing to go to ${counter_offer}. This {item['title']} won't last long at this price!"
            ]
        
        # Add urgency-based messages for higher urgency items
        if item["urgency"] > 0.6 and round_num >= 2:
            urgent_messages = [
                f"I'm motivated to sell, so ${counter_offer} works for me.",
                f"I need to move this quickly - ${counter_offer} and it's yours today!",
                f"${counter_offer} and we have a deal. I'm ready to close this now."
            ]
            messages.extend(urgent_messages)
        
        return random.choice(messages)
    
    def respond_to_offer(self, negotiation_id):
        """Respond to a buyer's offer"""
        negotiations = self.load_negotiations()
        
        if negotiation_id not in negotiations["active_negotiations"]:
            return
        
        negotiation = negotiations["active_negotiations"][negotiation_id]
        item_id = negotiation["item_id"]
        
        # Check if this is our item and if buyer has made the latest move
        if item_id not in self.inventory:
            return
        
        # Get latest buyer action
        buyer_actions = [h for h in negotiation["history"] if h["from"] == "buyer"]
        seller_actions = [h for h in negotiation["history"] if h["from"] == "seller"]
        
        # Only respond if buyer has acted more recently than us
        if len(buyer_actions) <= len(seller_actions):
            return
        
        latest_buyer_action = buyer_actions[-1]
        
        # Don't respond to end actions
        if latest_buyer_action["action"] in ["end", "accept"]:
            return
        
        # Calculate our response
        counter_offer = self.calculate_counter_offer(negotiation)
        message = self.generate_response_message(negotiation, counter_offer)
        
        # Determine action type
        buyer_offer = negotiation["current_offer"]
        if counter_offer == buyer_offer:
            action = "accept"
            negotiation["status"] = "accepted"
            negotiation["final_price"] = counter_offer
        else:
            action = "counter_offer"
        
        # Add our response to history
        response = {
            "round": negotiation["round"],
            "from": "seller",
            "action": action,
            "amount": counter_offer,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        negotiation["history"].append(response)
        
        # If we accepted, move to completed negotiations
        if action == "accept":
            negotiations["completed_negotiations"].append(negotiation)
            del negotiations["active_negotiations"][negotiation_id]
            print(f"✅ Accepted ${counter_offer} for {negotiation['item_title']}")
        else:
            negotiations["active_negotiations"][negotiation_id] = negotiation
            print(f"💬 Counter-offered ${counter_offer} for {negotiation['item_title']} (Round {negotiation['round']})")
        
        # Update agent status
        if not negotiations["active_negotiations"]:
            negotiations["agent_status"]["seller_agent"] = "idle"
        else:
            negotiations["agent_status"]["seller_agent"] = "negotiating"
        
        self.save_negotiations(negotiations)
    
    def check_for_offers(self):
        """Check for new buyer offers that need responses"""
        negotiations = self.load_negotiations()
        
        for neg_id, negotiation in negotiations["active_negotiations"].items():
            item_id = negotiation["item_id"]
            
            # Only respond to negotiations for our items
            if item_id in self.inventory:
                self.respond_to_offer(neg_id)
    
    def display_inventory_status(self):
        """Display current inventory and negotiation status"""
        negotiations = self.load_negotiations()
        
        print(f"\n📦 Seller Inventory Status:")
        for item_id, item in self.inventory.items():
            # Check if item has active negotiations
            active_neg = None
            for neg_id, neg in negotiations["active_negotiations"].items():
                if neg["item_id"] == item_id:
                    active_neg = neg
                    break
            
            # Check if item was sold
            sold = False
            for completed_neg in negotiations["completed_negotiations"]:
                if completed_neg["item_id"] == item_id and completed_neg["status"] == "accepted":
                    sold = True
                    final_price = completed_neg["final_price"]
                    break
            
            status = "SOLD" if sold else "NEGOTIATING" if active_neg else "AVAILABLE"
            price_info = f"${final_price}" if sold else f"${item['asking_price']} (min: ${item['minimum_price']})"
            
            print(f"  • {item['title']}: {status} - {price_info}")
            
            if active_neg:
                latest_offer = active_neg["current_offer"]
                print(f"    💰 Current offer: ${latest_offer} (Round {active_neg['round']})")
    
    async def run(self):
        """Main seller agent loop"""
        print(f"🏪 Seller Agent {self.agent_id} starting...")
        print(f"📦 Managing {len(self.inventory)} items")
        
        # Display initial inventory
        self.display_inventory_status()
        
        while True:
            # Check for new offers to respond to
            self.check_for_offers()
            
            # Display status every 10 seconds
            self.display_inventory_status()
            
            await asyncio.sleep(3)  # Check every 3 seconds
            
            # Check if all items are sold or negotiations ended
            negotiations = self.load_negotiations()
            if not negotiations["active_negotiations"]:
                # Check if we have any items left to sell
                sold_items = set()
                for completed_neg in negotiations["completed_negotiations"]:
                    if completed_neg["status"] == "accepted":
                        sold_items.add(completed_neg["item_id"])
                
                if len(sold_items) == len(self.inventory):
                    print("🎉 All items sold! Closing shop.")
                    break
                elif not any(neg.get("item_id") in self.inventory for neg in negotiations["active_negotiations"].values()):
                    print("💤 No active negotiations. Waiting for buyers...")

if __name__ == "__main__":
    seller = SellerAgent()
    asyncio.run(seller.run())