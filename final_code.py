# import os
# import json
# import datetime
# import random
# import uuid
# from typing import Dict, List, Any, Optional
# from datetime import datetime, timedelta
# from moya.conversation.thread import Thread
# from moya.tools.base_tool import BaseTool
# from moya.tools.ephemeral_memory import EphemeralMemory
# from moya.tools.tool_registry import ToolRegistry
# from moya.registry.agent_registry import AgentRegistry
# from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
# from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
# from moya.conversation.message import Message


# #### AGENT 1: Freshness Agent ####


# class FreshnessMonitor:
#     """Class to handle operations related to tracking item freshness and expiry dates."""
    
#     @staticmethod
#     def load_inventory() -> List[Dict]:
#         """
#         Load inventory data from JSON file.
        
#         Returns:
#             List[Dict]: List of inventory items
#         """
#         try:
#             with open("item_inventory.json", "r") as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             # Create the file with an empty array if it doesn't exist
#             FreshnessMonitor._ensure_inventory_file()
#             return []
            
#     @staticmethod
#     def _ensure_inventory_file():
#         """Create inventory file if it doesn't exist with empty JSON array"""
#         if not os.path.exists("item_inventory.json"):
#             with open("item_inventory.json", 'w') as f:
#                 json.dump([], f)  # Initialize with empty array        
            
#     @staticmethod
#     def save_inventory(inventory: List[Dict]) -> None:
#         """
#         Save inventory data to JSON file.
        
#         Args:
#             inventory (List[Dict]): List of inventory items to save
#         """
#         with open("item_inventory.json", "w") as f:
#             json.dump(inventory, f, indent=2)
    
#     @staticmethod
#     def get_expiring_items(days_threshold: int = 7) -> List[Dict]:
#         """
#         Get items that will expire within the specified number of days.
        
#         Args:
#             days_threshold (int): Number of days to look ahead for expiring items
            
#         Returns:
#             List[Dict]: List of items that will expire soon
#         """
#         inventory = FreshnessMonitor.load_inventory()
#         expiring_items = []
#         today = datetime.now().date()
        
#         for item in inventory:
#             # Ensure item is a dictionary
#             if not isinstance(item, dict):
#                 continue
                
#             # Skip items without expiry dates
#             if not item.get("expiry_date"):
#                 continue
                
#             try:
#                 expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
#                 days_until_expiry = (expiry_date - today).days
                
#                 if 0 <= days_until_expiry <= days_threshold:
#                     item["days_until_expiry"] = days_until_expiry
#                     expiring_items.append(item)
#             except (ValueError, TypeError):
#                 # Skip items with invalid date formats
#                 continue
                
#         # Sort by expiry date (soonest first)
#         expiring_items.sort(key=lambda x: x["days_until_expiry"])
#         return expiring_items
    
#     @staticmethod
#     def get_expired_items() -> List[Dict]:
#         """
#         Get items that have already expired.
        
#         Returns:
#             List[Dict]: List of expired items
#         """
#         inventory = FreshnessMonitor.load_inventory()
#         # print("THIS IS INVENTORY",inventory)
#         expired_items = []
#         today = datetime.now().date()
#         # print("I AM REACHING HERE")
        
#         for item in inventory:
#             # print("THIS IS ITEM",item)
#             # Ensure item is a dictionary
#             if not isinstance(item, dict):
#                 continue
                
#             # Skip items without expiry dates
#             if not item.get("expiry_date"):
#                 continue
                
#             try:
#                 expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
#                 days_since_expiry = (today - expiry_date).days
                
#                 if days_since_expiry >= 0:
#                     item["days_since_expiry"] = days_since_expiry
#                     expired_items.append(item)
#             except (ValueError, TypeError):
#                 continue
        

                
#         # Sort by how long ago they expired (most recent first)
#         expired_items.sort(key=lambda x: x["days_since_expiry"])
#         return expired_items
    
#     @staticmethod
#     def update_expiry_date(item_id: str, new_expiry_date: str) -> bool:
#         """
#         Update the expiry date for a specific item.
        
#         Args:
#             item_id (str): ID of the item to update
#             new_expiry_date (str): New expiry date in YYYY-MM-DD format
            
#         Returns:
#             bool: True if update was successful, False otherwise
#         """
#         inventory = FreshnessMonitor.load_inventory()
        
#         # Validate date format
#         try:
#             datetime.strptime(new_expiry_date, "%Y-%m-%d")
#         except ValueError:
#             return False
            
#         for item in inventory:
#             # Skip non-dictionary items
#             if not isinstance(item, dict):
#                 continue
                
#             if item.get("item_id") == item_id:
#                 item["expiry_date"] = new_expiry_date
#                 FreshnessMonitor.save_inventory(inventory)
#                 return True
                
#         return False
    
#     @staticmethod
#     def get_usage_recommendations(user_id: str) -> List[Dict]:
#         """
#         Generate recommendations for items that should be used soon based on expiry dates.
#         Optionally match with recipes when possible.
        
#         Args:
#             user_id (str): ID of the user to generate recommendations for
            
#         Returns:
#             List[Dict]: List of recommendations with usage suggestions
#         """
#         expiring_items = FreshnessMonitor.get_expiring_items(days_threshold=5)
#         recommendations = []
        
#         # Load recipes to match with expiring ingredients
#         try:
#             with open("recipe_planning.json", "r") as f:
#                 recipes = json.load(f)
#         except FileNotFoundError:
#             recipes = []
        
#         for item in expiring_items:
#             recommendation = {
#                 "item_id": item["item_id"],
#                 "name": item["name"],
#                 "days_until_expiry": item["days_until_expiry"],
#                 "quantity": item["quantity"],
#                 "unit": item["unit"],
#                 "recipe_suggestions": []
#             }
            
#             # Find recipes that use this ingredient
#             for recipe in recipes:
#                 for ingredient in recipe.get("ingredients", []):
#                     if ingredient.get("item_id") == item["item_id"]:
#                         recommendation["recipe_suggestions"].append({
#                             "recipe_id": recipe["recipe_id"],
#                             "name": recipe["name"]
#                         })
            
#             recommendations.append(recommendation)
            
#         return recommendations

# def initialize_data_files():
#     """Ensure all required data files exist with proper initial structure"""
#     # Initialize inventory file
#     if not os.path.exists("item_inventory.json"):
#         with open("item_inventory.json", "w") as f:
#             json.dump([], f)
            
#     # Initialize recipe file
#     if not os.path.exists("recipe_planning.json"):
#         with open("recipe_planning.json", "w") as f:
#             json.dump([], f)
            
#     # Initialize users file
#     if not os.path.exists("users.json"):
#         with open("users.json", "w") as f:
#             json.dump([], f)
            
#     # Initialize purchase history file
#     if not os.path.exists("purchase_history.json"):
#         with open("purchase_history.json", "w") as f:
#             json.dump([], f)

# # Tool definitions for the agent
# def get_expiring_items_tool(days_threshold: int = 7) -> str:
#     """
#     Tool to fetch items that will expire within the specified number of days.
    
#     Args:
#         days_threshold (int): Number of days to look ahead for expiring items
        
#     Returns:
#         str: JSON string with items that will expire soon
#     """
#     expiring_items = FreshnessMonitor.get_expiring_items(days_threshold)
#     if not expiring_items:
#         return "No items are expiring within the specified timeframe."
        
#     result = f"Found {len(expiring_items)} items expiring within {days_threshold} days:\n\n"
#     for item in expiring_items:
#         result += f"• {item['name']} - Expires in {item['days_until_expiry']} days "
#         result += f"(Quantity: {item['quantity']} {item['unit']})\n"
        
#     return result


# def get_expired_items_tool() -> str:
#     """
#     Tool to fetch items that have already expired.
    
#     Returns:
#         str: JSON string with expired items
#     """
#     expired_items = FreshnessMonitor.get_expired_items()
#     if not expired_items:
#         return "No expired items found in inventory."
        
#     result = f"Found {len(expired_items)} expired items:\n\n"
#     for item in expired_items:
#         result += f"• {item['name']} - Expired {item['days_since_expiry']} days ago "
#         result += f"(Quantity: {item['quantity']} {item['unit']})\n"
        
#     return result


# def update_expiry_date_tool(item_id: str, new_expiry_date: str) -> str:
#     """
#     Tool to update the expiry date for a specific item.
    
#     Args:
#         item_id (str): ID of the item to update
#         new_expiry_date (str): New expiry date in YYYY-MM-DD format
        
#     Returns:
#         str: Success or failure message
#     """
#     success = FreshnessMonitor.update_expiry_date(item_id, new_expiry_date)
#     if success:
#         return f"Successfully updated expiry date for item {item_id} to {new_expiry_date}."
#     else:
#         return f"Failed to update expiry date. Item {item_id} not found or invalid date format."


# def get_usage_recommendations_tool(user_id: str) -> str:
#     """
#     Tool to generate recommendations for items that should be used soon.
    
#     Args:
#         user_id (str): ID of the user to generate recommendations for
        
#     Returns:
#         str: Recommendations for using expiring items
#     """
#     recommendations = FreshnessMonitor.get_usage_recommendations(user_id)
#     if not recommendations:
#         return "No immediate usage recommendations. All items have sufficient shelf life."
        
#     result = "Usage recommendations for items expiring soon:\n\n"
#     for rec in recommendations:
#         result += f"• {rec['name']} - Use within {rec['days_until_expiry']} days!\n"
#         if rec['recipe_suggestions']:
#             result += "  Recipe suggestions:\n"
#             for recipe in rec['recipe_suggestions'][:3]:  # Limit to 3 suggestions
#                 result += f"  - {recipe['name']}\n"
#         else: 
#             result += "  No recipe suggestions available for this item.\n"
#         result += "\n"
        
#     return result   




# def setup_memory_components():
#     """Set up memory components for the agents."""
#     tool_registry = ToolRegistry()
#     EphemeralMemory.configure_memory_tools(tool_registry)
#     return tool_registry

# def create_freshness_agent(tool_registry):
#     """
#     Set up the AzureOpenAI agent with memory capabilities and return the orchestrator and agent.
    
#     Returns:
#         tuple: A tuple containing the orchestrator and the agent.
#     """
#     # Set up memory components
#     tool_registry = ToolRegistry()
#     EphemeralMemory.configure_memory_tools(tool_registry)
    
#     # Register freshness monitoring tools
#     expiring_items_tool = BaseTool(
#         name="get_expiring_items_tool",
#         description="Tool to fetch items that will expire within the specified number of days",
#         function=get_expiring_items_tool,
#         parameters={
#             "days_threshold": {
#                 "type": "integer",
#                 "description": "Number of days to look ahead for expiring items (default: 7)"
#             }
#         },
#         required=[]  # Make days_threshold optional
#     )
#     tool_registry.register_tool(expiring_items_tool)
    
#     expired_items_tool = BaseTool(
#         name="get_expired_items_tool",
#         description="Tool to fetch items that have already expired",
#         function=get_expired_items_tool,
#         parameters={},
#         required=[]
#     )
#     tool_registry.register_tool(expired_items_tool)
    
#     update_expiry_tool = BaseTool(
#         name="update_expiry_date_tool",
#         description="Tool to update the expiry date for a specific item",
#         function=update_expiry_date_tool,
#         parameters={
#             "item_id": {
#                 "type": "string",
#                 "description": "ID of the item to update"
#             },
#             "new_expiry_date": {
#                 "type": "string",
#                 "description": "New expiry date in YYYY-MM-DD format"
#             }
#         },
#         required=["item_id", "new_expiry_date"]
#     )
#     tool_registry.register_tool(update_expiry_tool)
    
#     recommendations_tool = BaseTool(
#         name="get_usage_recommendations_tool",
#         description="Tool to generate recommendations for items that should be used soon",
#         function=get_usage_recommendations_tool,
#         parameters={
#             "user_id": {
#                 "type": "string",
#                 "description": "ID of the user to generate recommendations for"
#             }
#         },
#         required=["user_id"]
#     )
#     tool_registry.register_tool(recommendations_tool)
    
#     agent_config = AzureOpenAIAgentConfig(
#         agent_name="freshness_monitoring_agent",
#         description="An agent that monitors expiry dates and recommends actions to prevent food waste",
#         model_name="gpt-4o",
#         agent_type="FreshnessMonitoringAgent",
#         tool_registry=tool_registry,
#         system_prompt="""
#             You are an Expiration & Freshness Monitoring Agent, focused on helping users prevent food waste.
#             Your primary responsibilities include:
#             1. Tracking expiry dates of perishable items
#             2. Alerting users about items that are about to expire
#             3. Recommending recipes or usage ideas for ingredients that need to be used soon
#             4. Helping users update expiry dates when they check their inventory
#             5. Providing daily reports on expiring items for each user
#             6. Sending notifications to users about expiring items
#             7. Generating meal suggestions based on expiring items
    
            
#             You have access to tools that help you retrieve information about expiring items and
#             generate recommendations. Always provide actionable advice to help users minimize food waste.
            
#             When users ask about their inventory, first check for expired items, then check for
#             items expiring soon, and finally provide usage recommendations when appropriate.
            
#             Store conversation context in memory to provide personalized recommendations.
#         """,
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
#         organization=None
#     )
    
#     return AzureOpenAIAgent(config=agent_config)

# def create_consumption_agent(tool_registry):
#     """Create the consumption tracking agent."""
#     agent_config = AzureOpenAIAgentConfig(
#         agent_name="consumption_agent",
#         description="Agent for tracking consumption patterns and shopping recommendations",
#         model_name="gpt-4o",
#         agent_type="ChatAgent",
#         tool_registry=tool_registry,
#         system_prompt="""
#         You are the Consumption Agent, responsible for tracking food consumption patterns and providing
#         shopping recommendations based on usage history.
        
#         You can:
#         1. Log consumption of food items
#         2. Predict when items will run out based on usage patterns
#         3. Recommend shopping based on consumption history
        
#         Always respond in a helpful, food-focused manner.
#         """,
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"
#     )
    
#     return AzureOpenAIAgent(config=agent_config)

# def create_shopping_list_agent(tool_registry):
#     """Create the shopping list management agent."""
#     agent_config = AzureOpenAIAgentConfig(
#         agent_name="shopping_list_agent",
#         description="Agent for creating and optimizing shopping lists",
#         model_name="gpt-4o",
#         agent_type="ChatAgent",
#         tool_registry=tool_registry,
#         system_prompt="""
#         You are the Shopping List Agent, responsible for helping users create and optimize their
#         shopping lists based on needs, recipes, and budget.
        
#         You can:
#         1. Create new shopping lists
#         2. Add or remove items from lists
#         3. Optimize lists for budget or nutrition
        
#         Always respond in a helpful, food-focused manner.
#         """,
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"
#     )
    
#     return AzureOpenAIAgent(config=agent_config)

# def create_dietary_agent(tool_registry):
#     """Create the dietary preferences and nutrition agent."""
#     agent_config = AzureOpenAIAgentConfig(
#         agent_name="dietary_agent",
#         description="Agent for dietary preferences, restrictions, and nutritional analysis",
#         model_name="gpt-4o",
#         agent_type="ChatAgent",
#         tool_registry=tool_registry,
#         system_prompt="""
#         You are the Dietary Agent, responsible for helping users with dietary preferences,
#         restrictions, and nutritional analysis.
        
#         You can:
#         1. Track dietary preferences and restrictions
#         2. Analyze nutritional content of foods and meals
#         3. Suggest alternatives based on dietary needs
        
#         Always respond in a helpful, food-focused manner.
#         """,
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"
#     )
    
#     return AzureOpenAIAgent(config=agent_config)


# ##### MEAL PLANNING AGENT #####

# class RecipePlanner:
#     """Class to handle operations related to recipe planning and meal suggestions."""
    
#     @staticmethod
#     def load_recipes() -> List[Dict]:
#         """
#         Load recipe data from JSON file.
        
#         Returns:
#             List[Dict]: List of recipe items
#         """
#         try:
#             with open("recipe_planning.json", "r") as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             # Create the file with an empty array if it doesn't exist
#             RecipePlanner._ensure_recipe_file()
#             return []
            
#     @staticmethod
#     def _ensure_recipe_file():
#         """Create recipe file if it doesn't exist with empty JSON array"""
#         if not os.path.exists("recipe_planning.json"):
#             with open("recipe_planning.json", 'w') as f:
#                 json.dump([], f)  # Initialize with empty array
    
#     @staticmethod
#     def load_inventory() -> List[Dict]:
#         """
#         Load inventory data from JSON file.
        
#         Returns:
#             List[Dict]: List of inventory items
#         """
#         try:
#             with open("item_inventory.json", "r") as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             # Create the file with an empty array if it doesn't exist
#             RecipePlanner._ensure_inventory_file()
#             return []
            
#     @staticmethod
#     def _ensure_inventory_file():
#         """Create inventory file if it doesn't exist with empty JSON array"""
#         if not os.path.exists("item_inventory.json"):
#             with open("item_inventory.json", 'w') as f:
#                 json.dump([], f)  # Initialize with empty array
    
#     @staticmethod
#     def load_users() -> List[Dict]:
#         """
#         Load user data from JSON file.
        
#         Returns:
#             List[Dict]: List of user data
#         """
#         try:
#             with open("users.json", "r") as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             # Create the file with an empty array if it doesn't exist
#             RecipePlanner._ensure_users_file()
#             return []
            
#     @staticmethod
#     def _ensure_users_file():
#         """Create users file if it doesn't exist with empty JSON array"""
#         if not os.path.exists("users.json"):
#             with open("users.json", 'w') as f:
#                 json.dump([], f)  # Initialize with empty array
    
#     @staticmethod
#     def save_recipes(recipes: List[Dict]) -> None:
#         """
#         Save recipe data to JSON file.
        
#         Args:
#             recipes (List[Dict]): List of recipe items to save
#         """
#         with open("recipe_planning.json", "w") as f:
#             json.dump(recipes, f, indent=2)
    
#     @staticmethod
#     def get_user_preferences(user_id: str) -> Dict:
#         """
#         Get user preferences for recipe recommendations.
        
#         Args:
#             user_id (str): ID of the user
            
#         Returns:
#             Dict: User preferences including diet restrictions, allergies, etc.
#         """
#         users = RecipePlanner.load_users()
        
#         for user in users:
#             if not isinstance(user, dict):
#                 continue
                
#             if user.get("user_id") == user_id:
#                 return user.get("preferences", {})
                
#         return {}  # Return empty dict if user not found
    
#     @staticmethod
#     def get_available_ingredients() -> List[Dict]:
#         """
#         Get all available ingredients from inventory.
        
#         Returns:
#             List[Dict]: List of available ingredients
#         """
#         inventory = RecipePlanner.load_inventory()
#         available_ingredients = []
        
#         for item in inventory:
#             if not isinstance(item, dict):
#                 continue
                
#             # Skip items with zero or negative quantity
#             if item.get("quantity", 0) <= 0:
#                 continue
                
#             # Skip expired items
#             if item.get("expiry_date"):
#                 try:
#                     expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
#                     if expiry_date < datetime.now().date():
#                         continue
#                 except (ValueError, TypeError):
#                     pass
                    
#             available_ingredients.append(item)
            
#         return available_ingredients
    
#     @staticmethod
#     def find_recipes_by_ingredients(ingredients: List[Dict], match_threshold: float = 0.7) -> List[Dict]:
#         """
#         Find recipes that can be made with available ingredients.
        
#         Args:
#             ingredients (List[Dict]): List of available ingredients
#             match_threshold (float): Minimum fraction of recipe ingredients that must be available
            
#         Returns:
#             List[Dict]: List of recipes that can be made, sorted by match percentage
#         """
#         recipes = RecipePlanner.load_recipes()
#         matches = []
        
#         ingredient_ids = [ing["item_id"] for ing in ingredients]
        
#         for recipe in recipes:
#             if not isinstance(recipe, dict):
#                 continue
                
#             # Count number of matching ingredients
#             recipe_ingredients = recipe.get("ingredients", [])
#             if not recipe_ingredients:
#                 continue
                
#             matching_count = sum(1 for ing in recipe_ingredients if ing.get("item_id") in ingredient_ids)
#             match_percentage = matching_count / len(recipe_ingredients)
            
#             # Add recipes that meet the threshold
#             if match_percentage >= match_threshold:
#                 recipe_copy = recipe.copy()
#                 recipe_copy["match_percentage"] = match_percentage
#                 recipe_copy["matching_ingredients"] = matching_count
#                 recipe_copy["total_ingredients"] = len(recipe_ingredients)
#                 recipe_copy["missing_ingredients"] = []
                
#                 # Add info about missing ingredients
#                 for ing in recipe_ingredients:
#                     if ing.get("item_id") not in ingredient_ids:
#                         recipe_copy["missing_ingredients"].append(ing)
                        
#                 matches.append(recipe_copy)
                
#         # Sort by match percentage (highest first)
#         matches.sort(key=lambda x: x["match_percentage"], reverse=True)
#         return matches
    
#     @staticmethod
#     def get_recipe_by_id(recipe_id: str) -> Dict:
#         """
#         Get a specific recipe by ID.
        
#         Args:
#             recipe_id (str): ID of the recipe to retrieve
            
#         Returns:
#             Dict: Recipe data or empty dict if not found
#         """
#         recipes = RecipePlanner.load_recipes()
        
#         for recipe in recipes:
#             if not isinstance(recipe, dict):
#                 continue
                
#             if recipe.get("recipe_id") == recipe_id:
#                 return recipe
                
#         return {}  # Return empty dict if recipe not found
    
#     @staticmethod
#     def add_recipe(recipe_data: Dict) -> bool:
#         """
#         Add a new recipe to the recipes collection.
        
#         Args:
#             recipe_data (Dict): Recipe data to add
            
#         Returns:
#             bool: True if successful, False otherwise
#         """
#         # Validate required fields
#         required_fields = ["recipe_id", "name", "ingredients", "steps"]
#         for field in required_fields:
#             if field not in recipe_data:
#                 return False
                
#         recipes = RecipePlanner.load_recipes()
        
#         # Check for duplicate recipe_id
#         for recipe in recipes:
#             if recipe.get("recipe_id") == recipe_data["recipe_id"]:
#                 return False  # Duplicate recipe ID
                
#         # Add the new recipe
#         recipes.append(recipe_data)
#         RecipePlanner.save_recipes(recipes)
#         return True
    
#     @staticmethod
#     def generate_meal_plan(user_id: str, days: int = 7) -> List[Dict]:
#         """
#         Generate a meal plan for the specified number of days.
        
#         Args:
#             user_id (str): ID of the user
#             days (int): Number of days to plan for
            
#         Returns:
#             List[Dict]: Meal plan with recipes for each day
#         """
#         preferences = RecipePlanner.get_user_preferences(user_id)
#         available_ingredients = RecipePlanner.get_available_ingredients()
        
#         # Get suitable recipes
#         suitable_recipes = RecipePlanner.find_recipes_by_ingredients(available_ingredients, match_threshold=0.6)
        
#         # Filter based on dietary preferences
#         if preferences.get("diet"):
#             diet = preferences["diet"].lower()
#             suitable_recipes = [r for r in suitable_recipes if r.get("diet", "").lower() == diet or not r.get("diet")]
            
#         # Filter out allergies
#         if preferences.get("allergies"):
#             allergies = [a.lower() for a in preferences["allergies"]]
#             filtered_recipes = []
            
#             for recipe in suitable_recipes:
#                 has_allergen = False
#                 for allergen in allergies:
#                     if allergen in recipe.get("name", "").lower() or any(allergen in ing.get("name", "").lower() for ing in recipe.get("ingredients", [])):
#                         has_allergen = True
#                         break
#                 if not has_allergen:
#                     filtered_recipes.append(recipe)
                    
#             suitable_recipes = filtered_recipes
            
#         # Create meal plan
#         meal_plan = []
#         today = datetime.now().date()
        
#         # Ensure we have enough recipes
#         while len(suitable_recipes) < days:
#             suitable_recipes.extend(suitable_recipes[:days-len(suitable_recipes)])
            
#         # Create a plan for each day
#         for day in range(days):
#             current_date = today + timedelta(days=day)
#             day_plan = {
#                 "date": current_date.strftime("%Y-%m-%d"),
#                 "day_name": current_date.strftime("%A"),
#                 "meals": []
#             }
            
#             # Add breakfast, lunch, dinner
#             meal_types = ["Breakfast", "Lunch", "Dinner"]
#             for meal_type in meal_types:
#                 recipe_index = (day * len(meal_types) + meal_types.index(meal_type)) % len(suitable_recipes)
#                 recipe = suitable_recipes[recipe_index]
                
#                 day_plan["meals"].append({
#                     "meal_type": meal_type,
#                     "recipe_id": recipe.get("recipe_id"),
#                     "recipe_name": recipe.get("name"),
#                     "match_percentage": recipe.get("match_percentage", 1.0),
#                     "missing_ingredients": recipe.get("missing_ingredients", [])
#                 })
                
#             meal_plan.append(day_plan)
            
#         return meal_plan

# def initialize_data_files():
#     """Ensure all required data files exist with proper initial structure"""
#     # Initialize inventory file
#     if not os.path.exists("item_inventory.json"):
#         with open("item_inventory.json", "w") as f:
#             json.dump([], f)
            
#     # Initialize recipe file
#     if not os.path.exists("recipe_planning.json"):
#         with open("recipe_planning.json", "w") as f:
#             json.dump([], f)
            
#     # Initialize users file
#     if not os.path.exists("users.json"):
#         with open("users.json", "w") as f:
#             json.dump([], f)

# # Tool definitions for the agent
# def find_recipes_tool(match_threshold: float = 0.7) -> str:
#     """
#     Tool to find recipes that can be made with available ingredients.
    
#     Args:
#         match_threshold (float): Minimum fraction of recipe ingredients that must be available
        
#     Returns:
#         str: Formatted string with recipe suggestions
#     """
#     available_ingredients = RecipePlanner.get_available_ingredients()
#     matching_recipes = RecipePlanner.find_recipes_by_ingredients(available_ingredients, match_threshold)
    
#     if not matching_recipes:
#         return "I couldn't find any recipes that match your available ingredients with the given threshold."
        
#     result = f"Found {len(matching_recipes)} recipes you can make with your ingredients:\n\n"
    
#     for recipe in matching_recipes:
#         match_percent = int(recipe["match_percentage"] * 100)
#         result += f"• {recipe['name']} (Match: {match_percent}%)\n"
#         result += f"  - {recipe['matching_ingredients']} of {recipe['total_ingredients']} ingredients available\n"
        
#         if recipe.get("missing_ingredients"):
#             result += "  - Missing: " + ", ".join(ing["name"] for ing in recipe["missing_ingredients"]) + "\n"
            
#         result += "\n"
        
#     return result

# def get_recipe_details_tool(recipe_id: str) -> str:
#     """
#     Tool to get detailed information about a specific recipe.
    
#     Args:
#         recipe_id (str): ID of the recipe to retrieve
        
#     Returns:
#         str: Formatted string with recipe details
#     """
#     recipe = RecipePlanner.get_recipe_by_id(recipe_id)
    
#     if not recipe:
#         return f"Recipe with ID {recipe_id} not found."
        
#     result = f"# {recipe['name']}\n\n"
    
#     # Ingredients section
#     result += "## Ingredients\n"
#     for ingredient in recipe.get("ingredients", []):
#         result += f"- {ingredient.get('quantity', '')} {ingredient.get('name', '')}\n"
    
#     # Steps section
#     result += "\n## Preparation Steps\n"
#     for i, step in enumerate(recipe.get("steps", []), 1):
#         result += f"{i}. {step}\n"
        
#     # Additional information if available
#     if recipe.get("prep_time"):
#         result += f"\nPreparation Time: {recipe['prep_time']}\n"
#     if recipe.get("cook_time"):
#         result += f"Cooking Time: {recipe['cook_time']}\n"
#     if recipe.get("servings"):
#         result += f"Servings: {recipe['servings']}\n"
#     if recipe.get("diet"):
#         result += f"Diet Type: {recipe['diet']}\n"
#     if recipe.get("cuisine"):
#         result += f"Cuisine: {recipe['cuisine']}\n"
        
#     return result

# def add_recipe_tool(recipe_json: str) -> str:
#     """
#     Tool to add a new recipe to the collection.
    
#     Args:
#         recipe_json (str): JSON string containing recipe data
        
#     Returns:
#         str: Success or failure message
#     """
#     try:
#         recipe_data = json.loads(recipe_json)
#     except json.JSONDecodeError:
#         return "Failed to add recipe. Invalid JSON format."
        
#     success = RecipePlanner.add_recipe(recipe_data)
    
#     if success:
#         return f"Successfully added recipe '{recipe_data.get('name')}' with ID {recipe_data.get('recipe_id')}."
#     else:
#         return "Failed to add recipe. Please ensure it has a unique recipe_id and all required fields."
# def generate_meal_plan_tool(user_id: str, days: int = 7) -> str:
#     """
#     Tool to generate a meal plan for the specified number of days.
    
#     Args:
#         user_id (str): ID of the user
#         days (int): Number of days to plan for
        
#     Returns:
#         str: Formatted string with meal plan
#     """
#     meal_plan = RecipePlanner.generate_meal_plan(user_id, days)
    
#     if not meal_plan:
#         return f"Could not generate a meal plan for user {user_id}. Please check inventory and recipes."
        
#     result = f"📋 {days}-DAY MEAL PLAN\n"
#     result += "=" * 40 + "\n\n"
    
#     for day in meal_plan:
#         result += f"📅 {day['day_name']} ({day['date']})\n"
#         result += "-" * 30 + "\n"
        
#         for meal in day.get("meals", []):
#             match_percent = int(meal.get("match_percentage", 1.0) * 100)
#             result += f"• {meal['meal_type']}: {meal['recipe_name']} (Match: {match_percent}%)\n"
            
#             if meal.get("missing_ingredients"):
#                 result += "  - Missing: " + ", ".join(ing["name"] for ing in meal["missing_ingredients"]) + "\n"
                
#         result += "\n"
        
#     result += "To see detailed recipe instructions, use the get_recipe_details tool with the recipe ID.\n"
    
#     return result

# def get_available_ingredients_tool() -> str:
#     """
#     Tool to list all available ingredients in the inventory.
    
#     Returns:
#         str: Formatted string with available ingredients
#     """
#     ingredients = RecipePlanner.get_available_ingredients()
    
#     if not ingredients:
#         return "Your inventory is empty. Please add some ingredients to get started."
        
#     # Group by category
#     categories = {}
#     for item in ingredients:
#         category = item.get("category", "Uncategorized")
#         if category not in categories:
#             categories[category] = []
#         categories[category].append(item)
        
#     result = "📦 AVAILABLE INGREDIENTS\n"
#     result += "=" * 40 + "\n\n"
    
#     for category, items in categories.items():
#         result += f"📑 {category}\n"
#         result += "-" * 20 + "\n"
        
#         for item in items:
#             expiry_info = ""
#             if item.get("expiry_date"):
#                 try:
#                     expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
#                     days_until_expiry = (expiry_date - datetime.now().date()).days
#                     expiry_info = f" (expires in {days_until_expiry} days)"
#                 except (ValueError, TypeError):
#                     pass
                    
#             result += f"• {item['name']} - {item.get('quantity', '')} {item.get('unit', '')}{expiry_info}\n"
            
#         result += "\n"
        
#     return result

# def get_user_preferences_tool(user_id: str) -> str:
#     """
#     Tool to get user preferences for recipe recommendations.
    
#     Args:
#         user_id (str): ID of the user
        
#     Returns:
#         str: Formatted string with user preferences
#     """
#     preferences = RecipePlanner.get_user_preferences(user_id)
    
#     if not preferences:
#         return f"No preferences found for user {user_id}."
        
#     result = "👤 USER PREFERENCES\n"
#     result += "=" * 30 + "\n\n"
    
#     for key, value in preferences.items():
#         result += f"• {key.capitalize()}: "
        
#         if isinstance(value, list):
#             result += ", ".join(value)
#         else:
#             result += str(value)
            
#         result += "\n"
        
#     return result


# def create_meal_planning_agent(tool_registry):
#     """
#     Set up the AzureOpenAI agent with memory capabilities and return the orchestrator and agent.
    
#     Returns:
#         tuple: A tuple containing the orchestrator and the agent.
#     """
#     # Set up memory components
#     tool_registry = ToolRegistry()
#     EphemeralMemory.configure_memory_tools(tool_registry)
    
#     # Register recipe planning tools
#     recipes_tool = BaseTool(
#         name="find_recipes_tool",
#         description="Find recipes that can be made with available ingredients",
#         function=find_recipes_tool,
#         parameters={
#             "match_threshold": {
#                 "type": "number",
#                 "description": "Minimum fraction of recipe ingredients that must be available (default: 0.7)"
#             }
#         },
#         required=[]  # Make match_threshold optional
#     )
#     tool_registry.register_tool(recipes_tool)
    
#     recipe_details_tool = BaseTool(
#         name="get_recipe_details_tool",
#         description="Get detailed information about a specific recipe",
#         function=get_recipe_details_tool,
#         parameters={
#             "recipe_id": {
#                 "type": "string",
#                 "description": "ID of the recipe to retrieve"
#             }
#         },
#         required=["recipe_id"]
#     )
#     tool_registry.register_tool(recipe_details_tool)
    
#     add_recipe_tool_obj = BaseTool(
#         name="add_recipe_tool",
#         description="Add a new recipe to the collection",
#         function=add_recipe_tool,
#         parameters={
#             "recipe_json": {
#                 "type": "string",
#                 "description": "JSON string containing recipe data"
#             }
#         },
#         required=["recipe_json"]
#     )
#     tool_registry.register_tool(add_recipe_tool_obj)
    
#     meal_plan_tool = BaseTool(
#         name="generate_meal_plan_tool",
#         description="Generate a meal plan for the specified number of days",
#         function=generate_meal_plan_tool,
#         parameters={
#             "user_id": {
#                 "type": "string",
#                 "description": "ID of the user"
#             },
#             "days": {
#                 "type": "integer",
#                 "description": "Number of days to plan for (default: 7)"
#             }
#         },
#         required=["user_id"]  # Make days optional
#     )
#     tool_registry.register_tool(meal_plan_tool)
    
#     ingredients_tool = BaseTool(
#         name="get_available_ingredients_tool",
#         description="List all available ingredients in the inventory",
#         function=get_available_ingredients_tool,
#         parameters={},
#         required=[]
#     )
#     tool_registry.register_tool(ingredients_tool)
    
#     preferences_tool = BaseTool(
#         name="get_user_preferences_tool",
#         description="Get user preferences for recipe recommendations",
#         function=get_user_preferences_tool,
#         parameters={
#             "user_id": {
#                 "type": "string",
#                 "description": "ID of the user"
#             }
#         },
#         required=["user_id"]
#     )
#     tool_registry.register_tool(preferences_tool)
    
#     # Create agent configuration
#     agent_config = AzureOpenAIAgentConfig(
#         agent_name="recipe_planning_agent",
#         description="An agent that suggests meal ideas based on available ingredients",
#         model_name="gpt-4o",
#         agent_type="RecipePlanningAgent",
#         tool_registry=tool_registry,
#         system_prompt="""
#             You are a Recipe & Meal Planning Agent, focused on helping users plan meals without extra shopping trips.
#             Your primary responsibilities include:
#             1. Suggesting recipes based on available ingredients in the user's inventory
#             2. Creating customized meal plans that maximize the use of available ingredients
#             3. Considering user preferences, dietary restrictions, and allergies
#             4. Providing detailed recipe instructions and information
#             5. Helping users make the most of ingredients before they expire
#             6. Minimizing food waste by suggesting recipes for soon-to-expire items
#             7. Organizing meals efficiently throughout the week
            
#             You have access to tools that help you find recipes, generate meal plans, and view available ingredients.
#             Always provide practical and actionable meal planning advice.
            
#             When users ask about meal ideas, first check their available ingredients, then consider their preferences,
#             and finally suggest recipes or meal plans that make the best use of what they have.
            
#             Store conversation context in memory to provide personalized recommendations.
#         """,
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
#         organization=None
#     )
    
#     return AzureOpenAIAgent(config=agent_config)














# def create_classifier_agent():
#     """Create the classifier agent that determines which agent should handle a request."""
#     agent_config = AzureOpenAIAgentConfig(
#         agent_name="classifier_agent",
#         description="Agent for classifying user requests and routing them to the appropriate agent",
#         model_name="gpt-4o",
#         agent_type="AgentClassifier",
#         tool_registry=None,
#         system_prompt="""
#         You are a Classifier Agent responsible for determining which agent should handle user requests.
        
#         Analyze the request and return ONLY ONE of the following agent names (no other text):
#         - freshness_agent - For requests about expiry dates, alerts about items to use soon
#         - consumption_agent - For logging consumption, predicting depletion, shopping recommendations
#         - shopping_list_agent - For creating or optimizing shopping lists
#         - dietary_agent - For dietary preferences, restrictions, nutritional analysis
#         - meal_planning_agent - For generating meal plans, recipes, nutritional information , inventory management
        
#         Return ONLY the agent name with no other text or explanation.
#         """,
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"
#     )
    
#     return AzureOpenAIAgent(config=agent_config)

# class FoodAssistantOrchestrator:
#     """
#     A specialized orchestrator for the food management system that combines
#     classification and agent execution in a cohesive flow.
#     """
#     def __init__(self, agents_dict):
#         """
#         Initialize the orchestrator with a dictionary of agents.
        
#         :param agents_dict: Dictionary mapping agent names to agent instances
#         """
#         self.agents_dict = agents_dict
#         print("THE AGENTS DICT IS are ", self.agents_dict)
#         self.agent_registry = AgentRegistry()
        
#         # Register all agents
#         for agent_name, agent in self.agents_dict.items():
#             self.agent_registry.register_agent(agent)  # Pass the name explicitly
            
            
#         # Create the classifier orchestrator
#         self.classifier_orchestrator = SimpleOrchestrator(
#             agent_registry=self.agent_registry,
#             default_agent_name="classifier_agent"
#         )
        
#     def process_message(self, thread_id: str, user_message: str, stream_callback=None) -> str:
#         try:
#             # Store user message for context
#             EphemeralMemory.store_message(
#                 thread_id=thread_id,
#                 sender="user",
#                 content=user_message
#             )
            
#             # Get conversation context
#             session_summary = EphemeralMemory.get_thread_summary(thread_id)
#             enriched_input = f"{session_summary}\nCurrent user message: {user_message}"
            
#             # Get classification from classifier agent directly
#             classifier_agent = self.agents_dict["classifier_agent"]
#             message = Message(content=enriched_input, thread_id=thread_id)
#             thread = Thread(messages=[message])
#             classification_result = classifier_agent.process_thread(thread).content.strip()
            
#             print(f"DEBUG: Classifier selected: {classification_result}")
            
#             # Direct execution of the selected agent
#             if classification_result in self.agents_dict:
#                 selected_agent = self.agents_dict[classification_result]
                
#                 # Create a message for the selected agent
#                 agent_message = Message(content=enriched_input, thread_id=thread_id)
#                 agent_thread = Thread(messages=[agent_message])
                
#                 # Get response directly from the agent
#                 response = selected_agent.process_thread(agent_thread).content
                
#                 # Add agent identifier
#                 full_response = f"[{classification_result}] {response}"
                
#                 # Use stream callback if provided
#                 if stream_callback:
#                     stream_callback(full_response)
#             else:
#                 full_response = f"I'm not sure how to handle that request. (Classification: {classification_result})"
#                 if stream_callback:
#                     stream_callback(full_response)
            
#             # Store the response in memory
#             EphemeralMemory.store_message(
#                 thread_id=thread_id,
#                 sender="assistant",
#                 content=full_response
#             )
            
#             return full_response
            
#         except Exception as e:
#             error_msg = f"Error processing message: {str(e)}"
#             print(f"\nDEBUG: {error_msg}")
#             return f"I encountered an issue while processing your request. {error_msg}"

# def create_agents():
#     """Create and configure all agents for the food management system."""
#     # Set up shared memory components
#     tool_registry = setup_memory_components()
    
#     # Create individual agents
#     freshness_agent = create_freshness_agent(tool_registry)
#     consumption_agent = create_consumption_agent(tool_registry)
#     shopping_list_agent = create_shopping_list_agent(tool_registry)
#     dietary_agent = create_dietary_agent(tool_registry)
#     meal_planning_agent = create_meal_planning_agent(tool_registry)
#     classifier_agent = create_classifier_agent()
    
#     return {
#         "freshness_agent": freshness_agent,
#         "consumption_agent": consumption_agent,
#         "shopping_list_agent": shopping_list_agent,
#         "dietary_agent": dietary_agent,
#         "meal_planning_agent": meal_planning_agent,
#         "classifier_agent": classifier_agent
#     }
# class DataManager:
#     """Base class for file operations across different data types"""
    
#     @staticmethod
#     def load_data(filename: str) -> List[Dict]:
#         """Load data from JSON file with error handling"""
#         try:
#             with open(filename, "r") as f:
#                 return json.load(f)
#         except FileNotFoundError:
#             # Create the file with an empty array if it doesn't exist
#             DataManager._ensure_file(filename)
#             return []
    
#     @staticmethod
#     def save_data(filename: str, data: List[Dict]) -> None:
#         """Save data to JSON file"""
#         with open(filename, "w") as f:
#             json.dump(data, f, indent=2)
    
#     @staticmethod
#     def _ensure_file(filename: str) -> None:
#         """Create file if it doesn't exist with empty JSON array"""
#         if not os.path.exists(filename):
#             with open(filename, 'w') as f:
#                 json.dump([], f)
    
#     @staticmethod
#     def initialize_data_files() -> None:
#         """Ensure all required data files exist with proper initial structure"""
#         required_files = [
#             "item_inventory.json",
#             "recipe_planning.json", 
#             "users.json", 
#             "purchase_history.json",
#             "shopping_list.json",
#             "consumption_history.json",
#             "meal_plans.json"
#         ]
        
#         for file in required_files:
#             DataManager._ensure_file(file)


# def main():
#     """Main function to create and configure all agents and handle user interaction."""
#     # Initialize data files if needed
#     if hasattr(DataManager, 'initialize_data_files'):
#         DataManager.initialize_data_files()
    
#     # Create all agents
#     agents_dict = create_agents()
    
#     # Create the specialized orchestrator
#     orchestrator = FoodAssistantOrchestrator(agents_dict)
    
#     # Set up conversation thread
#     thread_id = "food_assistant_conversation"

#     print("Welcome To HackIIIT, your personal food management assistant!")
#     print("How can I assist you today?")
#     print("Type 'exit' to end the conversation.")
#     print("-" * 50)
    
#     # Function to display streaming responses
#     def stream_callback(chunk):
#         print(chunk, end="", flush=True)

#     # Initialize the conversation with a system message
#     EphemeralMemory.store_message(
#         thread_id=thread_id, 
#         sender="system", 
#         content=f"thread ID: {thread_id}"
#     )

#     while True:
#         # Get user input
#         user_message = input("\nYou: ").strip()

#         # Check for exit condition
#         if user_message.lower() == 'exit':
#             print("\nThank you for using HACKIIIT. Goodbye!")
#             break

#         print("\nHACKIIIT: ", end="", flush=True)
        
#         # Process the message using our orchestrator
#         orchestrator.process_message(
#             thread_id=thread_id,
#             user_message=user_message,
#             stream_callback=stream_callback
#         )
        
#         print()  # Add a newline after the response

# if __name__ == "__main__":
#     main()