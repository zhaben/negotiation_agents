Send your teammate these files to integrate agent
  negotiation with their existing marketplace:

  📁 Files to Send:

  1. Core Agent Files:

  - buyer_agent.py - Buyer agent with max price logic
  - seller_agent.py - Seller agent with min price logic
  - negotiate.py - Simulation runner
  - negotiations.json - Shared communication file (can be
  empty)

  2. Integration Instructions:

  Create a zip/folder with:
  negotiation_agents/
  ├── buyer_agent.py
  ├── seller_agent.py  
  ├── negotiate.py
  ├── negotiations.json
  └── README.md

  3. README.md for your teammate:

  # Agent Negotiation System

  ## Quick Setup
  1. Copy these files to your marketplace directory
  2. Install dependencies: `pip install httpx`
  3. Run simulation: `python negotiate.py --duration 60`

  ## Integration with Your MCP Server
  Add these tools to your server.py:

  ```python
  import json
  import os

  @mcp.tool()
  async def get_negotiations() -> str:
      """View active and completed negotiations"""
      try:
          with open("negotiations.json", "r") as f:
              data = json.load(f)

          active = len(data.get("active_negotiations", {}))
          completed =
  len(data.get("completed_negotiations", []))

          return f"Active: {active}, Completed:
  {completed}"
      except:
          return "No negotiations found"

  @mcp.tool()
  async def start_negotiation(item_id: str, buyer_budget:
  int) -> str:
      """Start a negotiation for an item"""
      # Add your negotiation starting logic
      return f"Started negotiation for item {item_id} with
  budget ${buyer_budget}"

  Usage

  - python negotiate.py - Run full simulation
  - python buyer_agent.py - Run buyer only
  - python seller_agent.py - Run seller only
  - Check negotiations.json for real-time updates

  ### **4. Key Points to Explain:**

  **Tell your teammate:**
  - "Drop these files in your marketplace folder"
  - "The agents communicate through `negotiations.json`"
  - "Your MCP server can read this file to show negotiation
   status"
  - "Buyers have max budgets, sellers have min prices"
  - "Run `python negotiate.py` to see them negotiate
  automatically"

  ### **5. Demo Command:**
  ```bash
  # After they copy the files:
  python negotiate.py --duration 30

  This gives them a working agent negotiation system that
  integrates with their existing marketplace MCP server!
