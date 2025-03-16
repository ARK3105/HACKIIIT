"""
Expiration & Freshness Monitoring Agent - Tracks expiry dates of perishable items
and reminds users to use them before they spoil.
"""

import os
import json
import datetime
from datetime import timedelta
from moya.conversation.thread import Thread
from moya.tools.base_tool import BaseTool
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig


def load_inventory(user_id: str) -> dict:
    """
    Load the user's inventory with expiration dates.
    
    Args:
        user_id (str): The ID of the user whose inventory to load.
        
    Returns:
        dict: The user's inventory with item details including expiration dates.
    """
    try:
        # In a real application, this would load from a database or file system
        with open(f"data/{user_id}_inventory.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return empty inventory if file doesn't exist
        return {"items": []}


def save_inventory(user_id: str, inventory: dict) -> bool:
    """
    Save the user's updated inventory.
    
    Args:
        user_id (str): The ID of the user whose inventory to save.
        inventory (dict): The updated inventory to save.
        
    Returns:
        bool: True if save was successful, False otherwise.
    """
    try:
        # Ensure the data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save the inventory to a JSON file
        with open(f"data/{user_id}_inventory.json", "w") as f:
            json.dump(inventory, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving inventory: {e}")
        return False


def check_expiring_items(user_id: str, days_threshold: int = 7) -> list:
    """
    Check for items that will expire within the specified number of days.
    
    Args:
        user_id (str): The ID of the user to check items for.
        days_threshold (int): Number of days to look ahead for expiring items.
        
    Returns:
        list: List of items expiring within the threshold, sorted by days until expiration.
    """
    inventory = load_inventory(user_id)
    today = datetime.datetime.now().date()
    expiring_items = []
    
    for item in inventory.get("items", []):
        if "expiration_date" in item:
            try:
                exp_date = datetime.datetime.strptime(item["expiration_date"], "%Y-%m-%d").date()
                days_until_expiration = (exp_date - today).days
                
                if 0 <= days_until_expiration <= days_threshold:
                    item["days_until_expiration"] = days_until_expiration
                    expiring_items.append(item)
                elif days_until_expiration < 0:
                    # Item has already expired
                    item["days_until_expiration"] = days_until_expiration
                    expiring_items.append(item)
            except ValueError:
                # Skip items with invalid date format
                continue
    
    # Sort by days until expiration (ascending)
    expiring_items.sort(key=lambda x: x["days_until_expiration"])
    return expiring_items


def add_item_with_expiry(user_id: str, item_name: str, expiration_date: str, quantity: float = 1, unit: str = "item") -> bool:
    """
    Add an item to the inventory with its expiration date.
    
    Args:
        user_id (str): The ID of the user whose inventory to update.
        item_name (str): Name of the item to add.
        expiration_date (str): Expiration date in YYYY-MM-DD format.
        quantity (float): Quantity of the item.
        unit (str): Unit of measurement (e.g., item, kg, liter).
        
    Returns:
        bool: True if item was added successfully, False otherwise.
    """
    try:
        # Validate date format
        datetime.datetime.strptime(expiration_date, "%Y-%m-%d")
        
        # Load inventory
        inventory = load_inventory(user_id)
        
        # Add new item
        new_item = {
            "id": str(len(inventory.get("items", [])) + 1),
            "name": item_name,
            "quantity": quantity,
            "unit": unit,
            "expiration_date": expiration_date,
            "date_added": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        
        if "items" not in inventory:
            inventory["items"] = []
            
        inventory["items"].append(new_item)
        
        # Save updated inventory
        return save_inventory(user_id, inventory)
    except ValueError:
        # Invalid date format
        return False


def generate_usage_suggestions(expiring_items: list) -> list:
    """
    Generate suggestions for using expiring items.
    
    Args:
        expiring_items (list): List of items that are expiring soon.
        
    Returns:
        list: List of suggestions for using the expiring items.
    """
    suggestions = []
    
    for item in expiring_items:
        days = item["days_until_expiration"]
        
        if days < 0:
            suggestion = {
                "item": item["name"],
                "urgency": "expired",
                "message": f"{item['name']} expired {abs(days)} days ago. Check if it's still safe to consume or discard it.",
                "recommendation": "Check for signs of spoilage and discard if necessary."
            }
        elif days == 0:
            suggestion = {
                "item": item["name"],
                "urgency": "critical",
                "message": f"{item['name']} expires today! Use it immediately.",
                "recommendation": f"Consider using {item['name']} in tonight's meal."
            }
        elif days <= 2:
            suggestion = {
                "item": item["name"],
                "urgency": "high",
                "message": f"{item['name']} expires in {days} days.",
                "recommendation": f"Plan to use {item['name']} very soon in your next meal."
            }
        else:
            suggestion = {
                "item": item["name"],
                "urgency": "moderate",
                "message": f"{item['name']} expires in {days} days.",
                "recommendation": f"Include {item['name']} in your meal planning for this week."
            }
        
        suggestions.append(suggestion)
    
    return suggestions


def setup_expiration_agent():
    """
    Set up the Expiration & Freshness Monitoring Agent with all necessary tools.
    
    Returns:
        tuple: A tuple containing the orchestrator and the agent.
    """
    # Set up tool registry and memory components
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    
    # Create tools for the expiration agent
    check_expiring_items_tool = BaseTool(
        name="check_expiring_items_tool",
        description="Check for items in the user's inventory that will expire soon",
        function=check_expiring_items,
        parameters={
            "user_id": {
                "type": "string",
                "description": "The ID of the user whose inventory to check"
            },
            "days_threshold": {
                "type": "integer",
                "description": "Number of days to look ahead for expiring items (default: 7)"
            }
        },
        required=["user_id"]
    )
    tool_registry.register_tool(check_expiring_items_tool)
    
    add_item_tool = BaseTool(
        name="add_item_with_expiry_tool",
        description="Add an item to the inventory with its expiration date",
        function=add_item_with_expiry,
        parameters={
            "user_id": {
                "type": "string",
                "description": "The ID of the user whose inventory to update"
            },
            "item_name": {
                "type": "string",
                "description": "Name of the item to add"
            },
            "expiration_date": {
                "type": "string",
                "description": "Expiration date in YYYY-MM-DD format"
            },
            "quantity": {
                "type": "number",
                "description": "Quantity of the item (default: 1)"
            },
            "unit": {
                "type": "string",
                "description": "Unit of measurement (e.g., item, kg, liter) (default: item)"
            }
        },
        required=["user_id", "item_name", "expiration_date"]
    )
    tool_registry.register_tool(add_item_tool)
    
    generate_suggestions_tool = BaseTool(
        name="generate_usage_suggestions_tool",
        description="Generate suggestions for using expiring items",
        function=generate_usage_suggestions,
        parameters={
            "expiring_items": {
                "type": "array",
                "description": "List of items that are expiring soon"
            }
        },
        required=["expiring_items"]
    )
    tool_registry.register_tool(generate_suggestions_tool)
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="expiration_monitoring_agent",
        description="An agent that monitors expiration dates of items and provides notifications",
        model_name="gpt-4o",
        agent_type="ExpirationMonitoringAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are an Expiration & Freshness Monitoring Agent that helps users track the expiration dates
            of their grocery items to reduce food waste. You provide timely reminders and suggestions for
            using items before they spoil.
            
            Your primary functions include:
            1. Checking for items that will expire soon
            2. Adding new items with their expiration dates
            3. Providing suggestions for using expiring items
            
            Always begin by storing the user's message in memory and fetch conversation history before
            generating your final response. Provide friendly, helpful advice focused on reducing food waste.
            
            When a user asks about expiring items, use the check_expiring_items_tool and then the
            generate_usage_suggestions_tool to provide useful recommendations.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create Azure OpenAI agent
    agent = AzureOpenAIAgent(
        config=agent_config
    )
    
    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="expiration_monitoring_agent"
    )
    
    return orchestrator, agent


def main():
    """
    Main function to run the Expiration & Freshness Monitoring Agent in an interactive mode.
    """
    orchestrator, agent = setup_expiration_agent()
    thread_id = "expiration_monitor_001"
    EphemeralMemory.store_message(
        thread_id=thread_id, 
        sender="system", 
        content=f"Starting Expiration & Freshness Monitoring, thread ID = {thread_id}"
    )
    
    # Create a default user ID for this session
    user_id = "user_123"
    
    print("Welcome to the Expiration & Freshness Monitoring Agent!")
    print("I'll help you track your groceries and remind you about items that will expire soon.")
    print("Type 'quit' or 'exit' to end the session.")
    print("-" * 70)
    
    # Example of how to add sample data (in a real app, this would be part of onboarding)
    print("Adding some sample items to your inventory for demonstration...")
    today = datetime.datetime.now().date()
    
    # Add sample items with various expiration dates
    sample_items = [
        {"name": "Milk", "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"), "quantity": 1, "unit": "gallon"},
        {"name": "Eggs", "date": (today + timedelta(days=10)).strftime("%Y-%m-%d"), "quantity": 12, "unit": "count"},
        {"name": "Spinach", "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "quantity": 1, "unit": "bag"},
        {"name": "Chicken Breast", "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "quantity": 0.5, "unit": "kg"},
        {"name": "Yogurt", "date": (today + timedelta(days=7)).strftime("%Y-%m-%d"), "quantity": 6, "unit": "cups"}
    ]
    
    for item in sample_items:
        add_item_with_expiry(user_id, item["name"], item["date"], item["quantity"], item["unit"])
    
    print("Sample inventory created successfully!")
    print("-" * 70)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("\nThank you for using the Expiration & Freshness Monitoring Agent. Goodbye!")
            break
        
        # Store user message
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_input)
        
        # Enrich input with user_id and conversation history
        session_summary = EphemeralMemory.get_thread_summary(thread_id)
        enriched_input = f"{session_summary}\nuser_id: {user_id}\nCurrent user message: {user_input}"
        
        # Print Assistant prompt
        print("\nAgent: ", end="", flush=True)
        
        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)
        
        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )
        
        # Store assistant message
        EphemeralMemory.store_message(thread_id=thread_id, sender="assistant", content=response)
        print()


if __name__ == "__main__":
    main()