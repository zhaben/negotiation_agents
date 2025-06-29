#!/usr/bin/env python3
"""
Buyer Agent - Negotiates prices for marketplace items
Connects to MCP server and uses shared JSON file for communication
"""

import json
import time
import random
import httpx
import asyncio
from datetime import datetime

class BuyerAgent:
    def __init__(self, agent_id="buyer_001", max_budget=1000):
        self.agent_id = agent_id
        self.max_budget = max_budget
        self.negotiations_file = "negotiations.json"
        self.mcp_server_url = "http://localhost:8080"
        
        # Buyer preferences and maximum prices for different categories
        self.max_prices = {
            "Electronics": 0.85,  # Willing to pay up to 85% of asking price
            "Furniture": 0.70,    # 70% for furniture
            "Sports": 0.80,       # 80% for sports equipment
            "default": 0.75       # 75% for other categories
        }
        
        # Negotiation strategy
        self.initial_offer_percentage = 0.60  # Start at 60% of asking price
        self.increment_percentage = 0.05      # Increase by 5% each round
        self.max_rounds = 5                   # Maximum negotiation rounds
        
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
    
    async def get_marketplace_items(self):
        """Fetch items from MCP server"""
        try:
            async with httpx.AsyncClient() as client:
                # Simulate MCP call to search_items
                response = await client.get(f"{self.mcp_server_url}/api/search_items")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"❌ Error fetching items: {e}")
            
        # Fallback: return sample items (simulating MCP response)
        return [
            {"id": "1", "title": "iPhone 12 Pro", "asking_price": 520, "category": "Electronics"},
            {"id": "2", "title": "Vintage Leather Sofa", "asking_price": 350, "category": "Furniture"},
            {"id": "3", "title": "Mountain Bike", "asking_price": 850, "category": "Sports"}
        ]
    
    def calculate_max_offer(self, item):
        """Calculate maximum offer for an item based on category and budget"""
        asking_price = item["asking_price"]
        category = item.get("category", "default")
        
        # Get category-specific max percentage
        max_percentage = self.max_prices.get(category, self.max_prices["default"])
        max_offer = int(asking_price * max_percentage)
        
        # Don't exceed total budget
        return min(max_offer, self.max_budget)
    
    def calculate_initial_offer(self, item):
        """Calculate initial offer (conservative start)"""
        asking_price = item["asking_price"]
        return int(asking_price * self.initial_offer_percentage)
    
    def start_negotiation(self, item):
        """Start a new negotiation for an item"""
        negotiations = self.load_negotiations()
        
        max_offer = self.calculate_max_offer(item)
        initial_offer = self.calculate_initial_offer(item)
        
        # Don't negotiate if asking price is already within budget
        if item["asking_price"] <= max_offer:
            print(f"✅ Item {item['id']} is already within budget. Buying at asking price: ${item['asking_price']}")
            return
        
        # Don't negotiate if even our max offer is too low
        if initial_offer > max_offer:
            print(f"❌ Item {item['id']} is too expensive. Max budget: ${max_offer}, asking: ${item['asking_price']}")
            return
        
        negotiation_id = f"neg_{item['id']}_{int(time.time())}"
        
        negotiation = {
            "id": negotiation_id,
            "item_id": item["id"],
            "item_title": item["title"],
            "asking_price": item["asking_price"],
            "buyer_id": self.agent_id,
            "buyer_max_offer": max_offer,
            "current_offer": initial_offer,
            "round": 1,
            "status": "active",
            "history": [],
            "started_at": datetime.now().isoformat()
        }
        
        # Add initial offer to history
        negotiation["history"].append({
            "round": 1,
            "from": "buyer",
            "action": "initial_offer",
            "amount": initial_offer,
            "message": f"Hi! I'm interested in your {item['title']}. Would you consider ${initial_offer}?",
            "timestamp": datetime.now().isoformat()
        })
        
        negotiations["active_negotiations"][negotiation_id] = negotiation
        negotiations["agent_status"]["buyer_agent"] = "negotiating"
        
        self.save_negotiations(negotiations)
        
        print(f"🏪 Started negotiation for {item['title']}")
        print(f"💰 Asking: ${item['asking_price']}, Initial Offer: ${initial_offer}, Max Budget: ${max_offer}")
        
        return negotiation_id
    
    def respond_to_counter_offer(self, negotiation_id):
        """Respond to seller's counter-offer"""
        negotiations = self.load_negotiations()
        
        if negotiation_id not in negotiations["active_negotiations"]:
            return
        
        negotiation = negotiations["active_negotiations"][negotiation_id]
        
        # Get latest seller response
        seller_responses = [h for h in negotiation["history"] if h["from"] == "seller"]
        if not seller_responses:
            return
        
        latest_response = seller_responses[-1]
        seller_counter = latest_response.get("amount", negotiation["asking_price"])
        
        # Check if we've reached max rounds
        if negotiation["round"] >= self.max_rounds:
            self._finalize_negotiation(negotiation_id, "max_rounds_reached")
            return
        
        # Calculate new offer
        current_offer = negotiation["current_offer"]
        max_offer = negotiation["buyer_max_offer"]
        
        # Increase offer by increment percentage
        new_offer = int(current_offer * (1 + self.increment_percentage))
        
        # Don't exceed max budget
        new_offer = min(new_offer, max_offer)
        
        # If seller's counter is within our max, accept it
        if seller_counter <= max_offer:
            self._accept_offer(negotiation_id, seller_counter)
            return
        
        # If we've reached our max and seller hasn't budged, walk away
        if new_offer >= max_offer and seller_counter > max_offer:
            self._finalize_negotiation(negotiation_id, "walked_away")
            return
        
        # Make counter-offer
        negotiation["current_offer"] = new_offer
        negotiation["round"] += 1
        
        # Add response to history
        messages = [
            f"I can go up to ${new_offer}. That's a fair price!",
            f"How about ${new_offer}? That's the best I can do.",
            f"Meet me halfway at ${new_offer}?",
            f"${new_offer} is my final offer for this quality item."
        ]
        
        negotiation["history"].append({
            "round": negotiation["round"],
            "from": "buyer",
            "action": "counter_offer",
            "amount": new_offer,
            "message": random.choice(messages),
            "timestamp": datetime.now().isoformat()
        })
        
        negotiations["active_negotiations"][negotiation_id] = negotiation
        self.save_negotiations(negotiations)
        
        print(f"💬 Counter-offered ${new_offer} for {negotiation['item_title']} (Round {negotiation['round']})")
    
    def _accept_offer(self, negotiation_id, amount):
        """Accept seller's offer"""
        negotiations = self.load_negotiations()
        negotiation = negotiations["active_negotiations"][negotiation_id]
        
        negotiation["status"] = "accepted"
        negotiation["final_price"] = amount
        negotiation["history"].append({
            "round": negotiation["round"] + 1,
            "from": "buyer",
            "action": "accept",
            "amount": amount,
            "message": f"Deal! I'll take it for ${amount}. When can we complete the transaction?",
            "timestamp": datetime.now().isoformat()
        })
        
        # Move to completed negotiations
        negotiations["completed_negotiations"].append(negotiation)
        del negotiations["active_negotiations"][negotiation_id]
        
        if not negotiations["active_negotiations"]:
            negotiations["agent_status"]["buyer_agent"] = "idle"
        
        self.save_negotiations(negotiations)
        
        print(f"✅ Accepted offer of ${amount} for {negotiation['item_title']}")
    
    def _finalize_negotiation(self, negotiation_id, reason):
        """Finalize negotiation (walked away or max rounds)"""
        negotiations = self.load_negotiations()
        negotiation = negotiations["active_negotiations"][negotiation_id]
        
        negotiation["status"] = reason
        
        if reason == "walked_away":
            message = "Thanks for your time, but I can't meet that price. Good luck with the sale!"
        else:
            message = "I think we're too far apart on price. Thanks for negotiating with me."
        
        negotiation["history"].append({
            "round": negotiation["round"] + 1,
            "from": "buyer",
            "action": "end",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Move to completed negotiations
        negotiations["completed_negotiations"].append(negotiation)
        del negotiations["active_negotiations"][negotiation_id]
        
        if not negotiations["active_negotiations"]:
            negotiations["agent_status"]["buyer_agent"] = "idle"
        
        self.save_negotiations(negotiations)
        
        print(f"❌ Ended negotiation for {negotiation['item_title']} - {reason}")
    
    def check_for_responses(self):
        """Check for seller responses and react"""
        negotiations = self.load_negotiations()
        
        for neg_id, negotiation in negotiations["active_negotiations"].items():
            if negotiation.get("buyer_id") == self.agent_id:
                # Check if seller has responded since our last action
                buyer_actions = [h for h in negotiation["history"] if h["from"] == "buyer"]
                seller_actions = [h for h in negotiation["history"] if h["from"] == "seller"]
                
                if len(seller_actions) > len(buyer_actions) - 1:
                    # Seller has responded, we need to react
                    self.respond_to_counter_offer(neg_id)
    
    async def run(self):
        """Main agent loop"""
        print(f"🤖 Buyer Agent {self.agent_id} starting...")
        print(f"💰 Budget: ${self.max_budget}")
        
        # Get items from marketplace
        items = await self.get_marketplace_items()
        
        # Start negotiations for interesting items
        for item in items[:2]:  # Negotiate for first 2 items
            self.start_negotiation(item)
            await asyncio.sleep(1)  # Small delay between negotiations
        
        # Monitor for responses
        while True:
            self.check_for_responses()
            await asyncio.sleep(2)  # Check every 2 seconds
            
            # Check if all negotiations are complete
            negotiations = self.load_negotiations()
            if not negotiations["active_negotiations"]:
                print("✅ All negotiations complete!")
                break

if __name__ == "__main__":
    buyer = BuyerAgent()
    asyncio.run(buyer.run())