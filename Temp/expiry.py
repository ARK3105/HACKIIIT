"""
Expiration & Freshness Monitoring Agent - Tracks expiry dates of perishable items
and reminds users to use them before they spoil.
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from moya.conversation.thread import Thread
from moya.tools.base_tool import BaseTool
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
from moya.conversation.message import Message


class FreshnessMonitor:
    """Class to handle operations related to tracking item freshness and expiry dates."""
    
    @staticmethod
    def load_inventory() -> List[Dict]:
        """
        Load inventory data from JSON file.
        
        Returns:
            List[Dict]: List of inventory items
        """
        try:
            with open("item_inventory.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create the file with an empty array if it doesn't exist
            FreshnessMonitor._ensure_inventory_file()
            return []
            
    @staticmethod
    def _ensure_inventory_file():
        """Create inventory file if it doesn't exist with empty JSON array"""
        if not os.path.exists("item_inventory.json"):
            with open("item_inventory.json", 'w') as f:
                json.dump([], f)  # Initialize with empty array        
            
    @staticmethod
    def save_inventory(inventory: List[Dict]) -> None:
        """
        Save inventory data to JSON file.
        
        Args:
            inventory (List[Dict]): List of inventory items to save
        """
        with open("item_inventory.json", "w") as f:
            json.dump(inventory, f, indent=2)
    
    @staticmethod
    def get_expiring_items(days_threshold: int = 7) -> List[Dict]:
        """
        Get items that will expire within the specified number of days.
        
        Args:
            days_threshold (int): Number of days to look ahead for expiring items
            
        Returns:
            List[Dict]: List of items that will expire soon
        """
        inventory = FreshnessMonitor.load_inventory()
        expiring_items = []
        today = datetime.now().date()
        
        for item in inventory:
            # Ensure item is a dictionary
            if not isinstance(item, dict):
                continue
                
            # Skip items without expiry dates
            if not item.get("expiry_date"):
                continue
                
            try:
                expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                days_until_expiry = (expiry_date - today).days
                
                if 0 <= days_until_expiry <= days_threshold:
                    item["days_until_expiry"] = days_until_expiry
                    expiring_items.append(item)
            except (ValueError, TypeError):
                # Skip items with invalid date formats
                continue
                
        # Sort by expiry date (soonest first)
        expiring_items.sort(key=lambda x: x["days_until_expiry"])
        return expiring_items
    
    @staticmethod
    def get_expired_items() -> List[Dict]:
        """
        Get items that have already expired.
        
        Returns:
            List[Dict]: List of expired items
        """
        inventory = FreshnessMonitor.load_inventory()
        # print("THIS IS INVENTORY",inventory)
        expired_items = []
        today = datetime.now().date()
        # print("I AM REACHING HERE")
        
        for item in inventory:
            # print("THIS IS ITEM",item)
            # Ensure item is a dictionary
            if not isinstance(item, dict):
                continue
                
            # Skip items without expiry dates
            if not item.get("expiry_date"):
                continue
                
            try:
                expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                days_since_expiry = (today - expiry_date).days
                
                if days_since_expiry >= 0:
                    item["days_since_expiry"] = days_since_expiry
                    expired_items.append(item)
            except (ValueError, TypeError):
                continue
        

                
        # Sort by how long ago they expired (most recent first)
        expired_items.sort(key=lambda x: x["days_since_expiry"])
        return expired_items
    
    @staticmethod
    def update_expiry_date(item_id: str, new_expiry_date: str) -> bool:
        """
        Update the expiry date for a specific item.
        
        Args:
            item_id (str): ID of the item to update
            new_expiry_date (str): New expiry date in YYYY-MM-DD format
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        inventory = FreshnessMonitor.load_inventory()
        
        # Validate date format
        try:
            datetime.strptime(new_expiry_date, "%Y-%m-%d")
        except ValueError:
            return False
            
        for item in inventory:
            # Skip non-dictionary items
            if not isinstance(item, dict):
                continue
                
            if item.get("item_id") == item_id:
                item["expiry_date"] = new_expiry_date
                FreshnessMonitor.save_inventory(inventory)
                return True
                
        return False
    
    @staticmethod
    def get_usage_recommendations(user_id: str) -> List[Dict]:
        """
        Generate recommendations for items that should be used soon based on expiry dates.
        Optionally match with recipes when possible.
        
        Args:
            user_id (str): ID of the user to generate recommendations for
            
        Returns:
            List[Dict]: List of recommendations with usage suggestions
        """
        expiring_items = FreshnessMonitor.get_expiring_items(days_threshold=5)
        recommendations = []
        
        # Load recipes to match with expiring ingredients
        try:
            with open("recipe_planning.json", "r") as f:
                recipes = json.load(f)
        except FileNotFoundError:
            recipes = []
        
        for item in expiring_items:
            recommendation = {
                "item_id": item["item_id"],
                "name": item["name"],
                "days_until_expiry": item["days_until_expiry"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "recipe_suggestions": []
            }
            
            # Find recipes that use this ingredient
            for recipe in recipes:
                for ingredient in recipe.get("ingredients", []):
                    if ingredient.get("item_id") == item["item_id"]:
                        recommendation["recipe_suggestions"].append({
                            "recipe_id": recipe["recipe_id"],
                            "name": recipe["name"]
                        })
            
            recommendations.append(recommendation)
            
        return recommendations

def initialize_data_files():
    """Ensure all required data files exist with proper initial structure"""
    # Initialize inventory file
    if not os.path.exists("item_inventory.json"):
        with open("item_inventory.json", "w") as f:
            json.dump([], f)
            
    # Initialize recipe file
    if not os.path.exists("recipe_planning.json"):
        with open("recipe_planning.json", "w") as f:
            json.dump([], f)
            
    # Initialize users file
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump([], f)
            
    # Initialize purchase history file
    if not os.path.exists("purchase_history.json"):
        with open("purchase_history.json", "w") as f:
            json.dump([], f)

# Tool definitions for the agent
def get_expiring_items_tool(days_threshold: int = 7) -> str:
    """
    Tool to fetch items that will expire within the specified number of days.
    
    Args:
        days_threshold (int): Number of days to look ahead for expiring items
        
    Returns:
        str: JSON string with items that will expire soon
    """
    expiring_items = FreshnessMonitor.get_expiring_items(days_threshold)
    if not expiring_items:
        return "No items are expiring within the specified timeframe."
        
    result = f"Found {len(expiring_items)} items expiring within {days_threshold} days:\n\n"
    for item in expiring_items:
        result += f"• {item['name']} - Expires in {item['days_until_expiry']} days "
        result += f"(Quantity: {item['quantity']} {item['unit']})\n"
        
    return result


def get_expired_items_tool() -> str:
    """
    Tool to fetch items that have already expired.
    
    Returns:
        str: JSON string with expired items
    """
    expired_items = FreshnessMonitor.get_expired_items()
    if not expired_items:
        return "No expired items found in inventory."
        
    result = f"Found {len(expired_items)} expired items:\n\n"
    for item in expired_items:
        result += f"• {item['name']} - Expired {item['days_since_expiry']} days ago "
        result += f"(Quantity: {item['quantity']} {item['unit']})\n"
        
    return result


def update_expiry_date_tool(item_id: str, new_expiry_date: str) -> str:
    """
    Tool to update the expiry date for a specific item.
    
    Args:
        item_id (str): ID of the item to update
        new_expiry_date (str): New expiry date in YYYY-MM-DD format
        
    Returns:
        str: Success or failure message
    """
    success = FreshnessMonitor.update_expiry_date(item_id, new_expiry_date)
    if success:
        return f"Successfully updated expiry date for item {item_id} to {new_expiry_date}."
    else:
        return f"Failed to update expiry date. Item {item_id} not found or invalid date format."


def get_usage_recommendations_tool(user_id: str) -> str:
    """
    Tool to generate recommendations for items that should be used soon.
    
    Args:
        user_id (str): ID of the user to generate recommendations for
        
    Returns:
        str: Recommendations for using expiring items
    """
    recommendations = FreshnessMonitor.get_usage_recommendations(user_id)
    if not recommendations:
        return "No immediate usage recommendations. All items have sufficient shelf life."
        
    result = "Usage recommendations for items expiring soon:\n\n"
    for rec in recommendations:
        result += f"• {rec['name']} - Use within {rec['days_until_expiry']} days!\n"
        if rec['recipe_suggestions']:
            result += "  Recipe suggestions:\n"
            for recipe in rec['recipe_suggestions'][:3]:  # Limit to 3 suggestions
                result += f"  - {recipe['name']}\n"
        else:
            result += "  No recipe suggestions available for this item.\n"
        result += "\n"
        
    return result


def setup_agent():
    """
    Set up the AzureOpenAI agent with memory capabilities and return the orchestrator and agent.
    
    Returns:
        tuple: A tuple containing the orchestrator and the agent.
    """
    # Set up memory components
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    
    # Register freshness monitoring tools
    expiring_items_tool = BaseTool(
        name="get_expiring_items_tool",
        description="Tool to fetch items that will expire within the specified number of days",
        function=get_expiring_items_tool,
        parameters={
            "days_threshold": {
                "type": "integer",
                "description": "Number of days to look ahead for expiring items (default: 7)"
            }
        },
        required=[]  # Make days_threshold optional
    )
    tool_registry.register_tool(expiring_items_tool)
    
    expired_items_tool = BaseTool(
        name="get_expired_items_tool",
        description="Tool to fetch items that have already expired",
        function=get_expired_items_tool,
        parameters={},
        required=[]
    )
    tool_registry.register_tool(expired_items_tool)
    
    update_expiry_tool = BaseTool(
        name="update_expiry_date_tool",
        description="Tool to update the expiry date for a specific item",
        function=update_expiry_date_tool,
        parameters={
            "item_id": {
                "type": "string",
                "description": "ID of the item to update"
            },
            "new_expiry_date": {
                "type": "string",
                "description": "New expiry date in YYYY-MM-DD format"
            }
        },
        required=["item_id", "new_expiry_date"]
    )
    tool_registry.register_tool(update_expiry_tool)
    
    recommendations_tool = BaseTool(
        name="get_usage_recommendations_tool",
        description="Tool to generate recommendations for items that should be used soon",
        function=get_usage_recommendations_tool,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user to generate recommendations for"
            }
        },
        required=["user_id"]
    )
    tool_registry.register_tool(recommendations_tool)
    
    
    
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="freshness_monitoring_agent",
        description="An agent that monitors expiry dates and recommends actions to prevent food waste",
        model_name="gpt-4o",
        agent_type="FreshnessMonitoringAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are an Expiration & Freshness Monitoring Agent, focused on helping users prevent food waste.
            Your primary responsibilities include:
            1. Tracking expiry dates of perishable items
            2. Alerting users about items that are about to expire
            3. Recommending recipes or usage ideas for ingredients that need to be used soon
            4. Helping users update expiry dates when they check their inventory
            5. Providing daily reports on expiring items for each user
            6. Sending notifications to users about expiring items
            7. Generating meal suggestions based on expiring items
    
            
            You have access to tools that help you retrieve information about expiring items and
            generate recommendations. Always provide actionable advice to help users minimize food waste.
            
            When users ask about their inventory, first check for expired items, then check for
            items expiring soon, and finally provide usage recommendations when appropriate.
            
            Store conversation context in memory to provide personalized recommendations.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create Azure OpenAI agent with memory capabilities
    agent = AzureOpenAIAgent(
        config=agent_config
    )
    
    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="freshness_monitoring_agent"
    )
    
    return orchestrator, agent


def main():
    # Initialize data files
    initialize_data_files()
    orchestrator, agent = setup_agent()
    thread_id = "freshness_monitoring_001"
    EphemeralMemory.store_message(
        thread_id=thread_id, 
        sender="system", 
        content=f"Starting freshness monitoring session, thread ID = {thread_id}"
    )
    
        # Uncomment these lines to enable scheduled features
    # schedule_notifications()
    batch_update_from_purchase_history()
    print("Welcome to Freshness Monitoring Assistant! (Type 'quit' or 'exit' to end)")
    print("I'll help you track expiry dates and prevent food waste.")
    print("-" * 60)
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye! Remember to check your expiring items regularly.")
            break
            
        # Store user message
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_input)
        
        # Get conversation summary and enrich input
        session_summary = EphemeralMemory.get_thread_summary(thread_id)
        enriched_input = f"{session_summary}\nCurrent user message: {user_input}"
        
        # Print Assistant prompt
        print("\nAssistant: ", end="", flush=True)
        
        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)
            
        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )
        
        # Store assistant's response in memory
        EphemeralMemory.store_message(thread_id=thread_id, sender="assistant", content=response)
        
        # Print newline after response
        print()

def batch_update_from_purchase_history():
    """
    Update inventory expiry dates based on recent purchases in the purchase history.
    This would typically run as a scheduled job after new purchases are added.
    """
    try:
        with open("item_inventory.json", "r") as f:
            inventory = json.load(f)
        with open("purchase_history.json", "r") as f:
            purchase_history = json.load(f)
    except FileNotFoundError:
        print("Required files not found.")
        return
    
    # Get today's date for calculations
    today = datetime.now().date()
    
    # Define shelf life estimates for different categories (in days)
    shelf_life_by_category = {
        "Dairy": 14,
        "Bakery": 7,
        "Produce": 10,
        "Meat": 5,
        "Seafood": 3,
        "Pantry": 365,
        "Frozen": 180,
        "Beverages": 30,
        "Snacks": 60,
        "Prepared": 4,
    }
    
    # Process recent purchases
    updated_count = 0
    
    for user_purchases in purchase_history:
        for purchase in user_purchases.get("purchases", []):
            # Parse purchase date
            try:
                purchase_date = datetime.strptime(purchase["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            
            # Only process recent purchases (within last 7 days)
            if (today - purchase_date).days > 7:
                continue
                
            # Find matching inventory item
            item_id = purchase.get("item_id")
            if not item_id:
                continue
                
            for item in inventory:
                if item["item_id"] == item_id:
                    # Determine expiry date based on category
                    category = item.get("category", "Pantry")
                    shelf_life = shelf_life_by_category.get(category, 14)  # Default 2 weeks
                    
                    # Calculate expiry date from purchase date
                    expiry_date = purchase_date + timedelta(days=shelf_life)
                    item["expiry_date"] = expiry_date.strftime("%Y-%m-%d")
                    updated_count += 1
    
    if updated_count > 0:
        # Save updated inventory
        with open("item_inventory.json", "w") as f:
            json.dump(inventory, f, indent=2)
        print(f"Updated expiry dates for {updated_count} items based on recent purchases.")


if __name__ == "__main__":
    main()
