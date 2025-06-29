#!/usr/bin/env python3
"""
Negotiation Simulation Script
Runs both buyer and seller agents simultaneously to demonstrate price negotiation
"""

import asyncio
import json
import time
from datetime import datetime
import subprocess
import sys
import os

class NegotiationSimulator:
    def __init__(self):
        self.negotiations_file = "negotiations.json"
        self.simulation_duration = 60  # Run for 60 seconds
        
    def reset_negotiations(self):
        """Reset negotiations file to initial state"""
        initial_state = {
            "active_negotiations": {},
            "completed_negotiations": [],
            "agent_status": {
                "buyer_agent": "idle",
                "seller_agent": "idle"
            }
        }
        
        with open(self.negotiations_file, 'w') as f:
            json.dump(initial_state, f, indent=2)
        
        print("🔄 Reset negotiations file")
    
    def load_negotiations(self):
        """Load current negotiations"""
        try:
            with open(self.negotiations_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"active_negotiations": {}, "completed_negotiations": [], "agent_status": {}}
    
    def display_summary(self):
        """Display negotiation summary"""
        data = self.load_negotiations()
        
        print("\n" + "="*60)
        print("📊 NEGOTIATION SUMMARY")
        print("="*60)
        
        # Active negotiations
        active = data.get("active_negotiations", {})
        print(f"\n🔄 Active Negotiations: {len(active)}")
        for neg_id, neg in active.items():
            print(f"  • {neg['item_title']}: ${neg['current_offer']} (Round {neg['round']})")
        
        # Completed negotiations
        completed = data.get("completed_negotiations", [])
        print(f"\n✅ Completed Negotiations: {len(completed)}")
        
        successful_deals = []
        failed_deals = []
        
        for neg in completed:
            if neg["status"] == "accepted":
                successful_deals.append(neg)
            else:
                failed_deals.append(neg)
        
        print(f"\n💰 Successful Deals: {len(successful_deals)}")
        total_savings = 0
        for deal in successful_deals:
            asking = deal["asking_price"]
            final = deal["final_price"]
            savings = asking - final
            total_savings += savings
            savings_pct = (savings / asking) * 100
            
            print(f"  • {deal['item_title']}: ${final} (was ${asking}) - Saved ${savings} ({savings_pct:.1f}%)")
        
        if successful_deals:
            print(f"  💵 Total Savings: ${total_savings}")
        
        print(f"\n❌ Failed Negotiations: {len(failed_deals)}")
        for deal in failed_deals:
            reason = deal["status"].replace("_", " ").title()
            print(f"  • {deal['item_title']}: {reason}")
        
        # Agent status
        status = data.get("agent_status", {})
        print(f"\n🤖 Agent Status:")
        for agent, state in status.items():
            print(f"  • {agent}: {state}")
    
    def display_live_updates(self):
        """Display live negotiation updates"""
        data = self.load_negotiations()
        
        # Show recent history
        recent_activity = []
        
        # Get activity from active negotiations
        for neg in data.get("active_negotiations", {}).values():
            for event in neg.get("history", []):
                event["negotiation"] = neg["item_title"]
                recent_activity.append(event)
        
        # Get activity from completed negotiations (last 5)
        for neg in data.get("completed_negotiations", [])[-5:]:
            for event in neg.get("history", [])[-2:]:  # Last 2 events
                event["negotiation"] = neg["item_title"]
                recent_activity.append(event)
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Display last 5 events
        print(f"\n📱 Recent Activity:")
        for event in recent_activity[:5]:
            timestamp = event.get("timestamp", "")
            if timestamp:
                time_str = timestamp.split("T")[1][:8]  # Extract time part
            else:
                time_str = "??:??:??"
            
            agent = "🛒" if event["from"] == "buyer" else "🏪"
            action = event["action"].replace("_", " ").title()
            amount = event.get("amount", "")
            amount_str = f"${amount}" if amount else ""
            
            print(f"  {time_str} {agent} {action} {amount_str} - {event['negotiation']}")
            
            # Show message if it's short
            message = event.get("message", "")
            if message and len(message) <= 60:
                print(f"    💬 \"{message}\"")
    
    async def monitor_negotiations(self):
        """Monitor and display negotiation progress"""
        print("🔍 Monitoring negotiations...")
        start_time = time.time()
        
        while time.time() - start_time < self.simulation_duration:
            # Clear screen for live updates
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("🤝 MARKETPLACE NEGOTIATION SIMULATION")
            print("=" * 50)
            print(f"⏰ Running time: {int(time.time() - start_time)}s / {self.simulation_duration}s")
            
            self.display_live_updates()
            self.display_summary()
            
            await asyncio.sleep(3)  # Update every 3 seconds
        
        print(f"\n⏰ Simulation time completed ({self.simulation_duration}s)")
    
    async def run_simulation(self):
        """Run the complete negotiation simulation"""
        print("🚀 Starting Marketplace Negotiation Simulation")
        print("=" * 50)
        
        # Reset state
        self.reset_negotiations()
        
        # Import agents here to run them programmatically
        try:
            from buyer_agent import BuyerAgent
            from seller_agent import SellerAgent
            
            # Create agents
            buyer = BuyerAgent(agent_id="buyer_001", max_budget=1200)
            seller = SellerAgent(agent_id="seller_001")
            
            print("✅ Agents created successfully")
            
            # Start both agents concurrently
            tasks = [
                asyncio.create_task(buyer.run(), name="buyer"),
                asyncio.create_task(seller.run(), name="seller"),
                asyncio.create_task(self.monitor_negotiations(), name="monitor")
            ]
            
            print("🎬 Starting simulation...")
            
            # Run until monitor completes or agents finish
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=self.simulation_duration + 10
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            print("\n🏁 Simulation completed!")
            
            # Final summary
            self.display_summary()
            
        except ImportError as e:
            print(f"❌ Could not import agents: {e}")
            print("Make sure buyer_agent.py and seller_agent.py are in the same directory")
        except Exception as e:
            print(f"❌ Simulation error: {e}")
    
    async def run_separate_processes(self):
        """Alternative: Run agents as separate processes"""
        print("🚀 Starting agents as separate processes...")
        
        self.reset_negotiations()
        
        # Start buyer agent
        buyer_process = subprocess.Popen([
            sys.executable, "buyer_agent.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Start seller agent  
        seller_process = subprocess.Popen([
            sys.executable, "seller_agent.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Agents started as separate processes")
        
        # Monitor negotiations
        await self.monitor_negotiations()
        
        # Terminate processes
        buyer_process.terminate()
        seller_process.terminate()
        
        print("🏁 Simulation completed!")
        self.display_summary()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run marketplace negotiation simulation")
    parser.add_argument(
        "--mode", 
        choices=["integrated", "separate"], 
        default="integrated",
        help="Run agents integrated or as separate processes"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60,
        help="Simulation duration in seconds"
    )
    
    args = parser.parse_args()
    
    simulator = NegotiationSimulator()
    simulator.simulation_duration = args.duration
    
    if args.mode == "separate":
        asyncio.run(simulator.run_separate_processes())
    else:
        asyncio.run(simulator.run_simulation())

if __name__ == "__main__":
    main()