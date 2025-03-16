import os
import json
import datetime
import random
import uuid
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

# ===================================
# Data Utilities
# ===================================

class DataManager:
    """Base class for file operations across different data types"""
    
    @staticmethod
    def load_data(filename: str) -> List[Dict]:
        """Load data from JSON file with error handling"""
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create the file with an empty array if it doesn't exist
            DataManager._ensure_file(filename)
            return []
    
    @staticmethod
    def save_data(filename: str, data: List[Dict]) -> None:
        """Save data to JSON file"""
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def _ensure_file(filename: str) -> None:
        """Create file if it doesn't exist with empty JSON array"""
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump([], f)
    
    @staticmethod
    def initialize_data_files() -> None:
        """Ensure all required data files exist with proper initial structure"""
        required_files = [
            "item_inventory.json",
            "recipe_planning.json", 
            "users.json", 
            "purchase_history.json",
            "shopping_list.json",
            "consumption_history.json",
            "meal_plans.json"
        ]
        
        for file in required_files:
            DataManager._ensure_file(file)

# ===================================
# Agent 1: Freshness Monitoring Agent
# ===================================

class FreshnessMonitor:
    """Class to handle operations related to tracking item freshness and expiry dates."""
    
    @staticmethod
    def load_inventory() -> List[Dict]:
        """Load inventory data from JSON file."""
        return DataManager.load_data("item_inventory.json")
            
    @staticmethod
    def save_inventory(inventory: List[Dict]) -> None:
        """Save inventory data to JSON file."""
        DataManager.save_data("item_inventory.json", inventory)
    
    @staticmethod
    def get_expiring_items(days_threshold: int = 7) -> List[Dict]:
        """Get items that will expire within the specified number of days."""
        inventory = FreshnessMonitor.load_inventory()
        expiring_items = []
        today = datetime.now().date()
        
        for item in inventory:
            # Skip items without expiry dates
            if not isinstance(item, dict) or not item.get("expiry_date"):
                continue
                
            try:
                expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                days_until_expiry = (expiry_date - today).days
                
                if 0 <= days_until_expiry <= days_threshold:
                    item["days_until_expiry"] = days_until_expiry
                    expiring_items.append(item)
            except (ValueError, TypeError):
                continue
                
        # Sort by expiry date (soonest first)
        expiring_items.sort(key=lambda x: x["days_until_expiry"])
        return expiring_items
    
    @staticmethod
    def get_expired_items() -> List[Dict]:
        """Get items that have already expired."""
        inventory = FreshnessMonitor.load_inventory()
        expired_items = []
        today = datetime.now().date()
        
        for item in inventory:
            if not isinstance(item, dict) or not item.get("expiry_date"):
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
        """Update the expiry date for a specific item."""
        inventory = FreshnessMonitor.load_inventory()
        
        try:
            datetime.strptime(new_expiry_date, "%Y-%m-%d")
        except ValueError:
            return False
            
        for item in inventory:
            if not isinstance(item, dict):
                continue
                
            if item.get("item_id") == item_id:
                item["expiry_date"] = new_expiry_date
                FreshnessMonitor.save_inventory(inventory)
                return True
                
        return False
    
    @staticmethod
    def get_usage_recommendations(user_id: str) -> List[Dict]:
        """Generate recommendations for items that should be used soon based on expiry dates."""
        expiring_items = FreshnessMonitor.get_expiring_items(days_threshold=5)
        recipes = DataManager.load_data("recipe_planning.json")
        recommendations = []
        
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

    @staticmethod
    def generate_daily_report(user_id: str) -> str:
        """Generate a daily report of expiring items for a specific user."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get expiring items data
        expiring_soon = FreshnessMonitor.get_expiring_items(days_threshold=3)
        expiring_this_week = FreshnessMonitor.get_expiring_items(days_threshold=7)
        expired_items = FreshnessMonitor.get_expired_items()
        
        # Build the report
        report = f"FRESHNESS MONITORING DAILY REPORT - {today}\n"
        report += "=" * 50 + "\n\n"
        
        if expired_items:
            report += f"⚠️ EXPIRED ITEMS ({len(expired_items)})\n"
            report += "-" * 30 + "\n"
            for item in expired_items:
                report += f"• {item['name']} - Expired {item['days_since_expiry']} days ago\n"
            report += "\n"
        
        if expiring_soon:
            report += f"🚨 URGENT: USE WITHIN 3 DAYS ({len(expiring_soon)})\n"
            report += "-" * 30 + "\n"
            for item in expiring_soon:
                report += f"• {item['name']} - Expires in {item['days_until_expiry']} days\n"
            report += "\n"
        
        if expiring_this_week and len(expiring_this_week) > len(expiring_soon):
            report += f"⚠️ USE THIS WEEK ({len(expiring_this_week) - len(expiring_soon)})\n"
            report += "-" * 30 + "\n"
            for item in expiring_this_week:
                if item not in expiring_soon:  # Avoid duplicates
                    report += f"• {item['name']} - Expires in {item['days_until_expiry']} days\n"
            report += "\n"
        
        # Add meal recommendations based on expiring items
        recommendations = FreshnessMonitor.get_usage_recommendations(user_id)
        if recommendations:
            report += "🍳 MEAL SUGGESTIONS TO REDUCE WASTE\n"
            report += "-" * 30 + "\n"
            
            for rec in recommendations:
                if rec['recipe_suggestions']:
                    report += f"For {rec['name']} (expires in {rec['days_until_expiry']} days):\n"
                    for i, recipe in enumerate(rec['recipe_suggestions'][:3]):
                        report += f"  {i+1}. {recipe['name']}\n"
                    report += "\n"
        
        if not expired_items and not expiring_soon and not expiring_this_week:
            report += "✅ Good news! No items are expiring soon.\n\n"
        
        report += "=" * 50 + "\n"
        report += "Generated by Freshness Monitoring Agent"
        
        return report

# ===================================
# Agent 2: Consumption Tracking & Prediction Agent
# ===================================

class ConsumptionTracker:
    """Class for tracking and predicting item consumption patterns."""
    
    @staticmethod
    def log_consumption(item_id: str, user_id: str, quantity: float, unit: str) -> bool:
        """
        Log the consumption of an item to track usage patterns.
        
        Args:
            item_id (str): ID of the consumed item
            user_id (str): ID of the user who consumed the item
            quantity (float): Amount consumed
            unit (str): Unit of measurement
            
        Returns:
            bool: True if successfully logged, False otherwise
        """
        try:
            consumption_history = DataManager.load_data("consumption_history.json")
            
            # Create consumption entry
            consumption_entry = {
                "consumption_id": str(uuid.uuid4()),
                "item_id": item_id,
                "user_id": user_id,
                "quantity": quantity,
                "unit": unit,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            consumption_history.append(consumption_entry)
            DataManager.save_data("consumption_history.json", consumption_history)
            
            # Update inventory quantity
            inventory = FreshnessMonitor.load_inventory()
            for item in inventory:
                if item.get("item_id") == item_id:
                    if item.get("unit") == unit:
                        current_qty = float(item.get("quantity", 0))
                        new_qty = max(0, current_qty - quantity)
                        item["quantity"] = new_qty
                        FreshnessMonitor.save_inventory(inventory)
                    break
            
            return True
        except Exception as e:
            print(f"Error logging consumption: {str(e)}")
            return False
    
    @staticmethod
    def predict_depletion(item_id: str, user_id: str = None) -> Dict:
        """
        Predict when an item will be depleted based on consumption history.
        
        Args:
            item_id (str): ID of the item to analyze
            user_id (str, optional): Filter by specific user
            
        Returns:
            Dict: Prediction details including estimated depletion date
        """
        try:
            # Get item current quantity
            inventory = FreshnessMonitor.load_inventory()
            item_data = next((item for item in inventory if item.get("item_id") == item_id), None)
            
            if not item_data:
                return {"error": "Item not found in inventory"}
            
            current_quantity = float(item_data.get("quantity", 0))
            item_unit = item_data.get("unit", "")
            
            # Get consumption history
            consumption_history = DataManager.load_data("consumption_history.json")
            item_consumption = [
                entry for entry in consumption_history 
                if entry.get("item_id") == item_id and 
                (user_id is None or entry.get("user_id") == user_id)
            ]
            
            if not item_consumption:
                return {
                    "item_id": item_id,
                    "name": item_data.get("name", ""),
                    "current_quantity": current_quantity,
                    "unit": item_unit,
                    "prediction": "No consumption history available for prediction",
                    "days_until_depletion": None,
                    "depletion_date": None,
                    "confidence": "low"
                }
            
            # Calculate average daily consumption
            consumption_dates = {}
            for entry in item_consumption:
                date = entry.get("timestamp", "").split(" ")[0]
                if date:
                    consumption_dates[date] = consumption_dates.get(date, 0) + float(entry.get("quantity", 0))
            
            if not consumption_dates:
                return {
                    "item_id": item_id,
                    "name": item_data.get("name", ""),
                    "current_quantity": current_quantity,
                    "unit": item_unit,
                    "prediction": "Insufficient data for prediction",
                    "days_until_depletion": None,
                    "depletion_date": None,
                    "confidence": "low"
                }
            
            unique_days = len(consumption_dates)
            total_consumed = sum(consumption_dates.values())
            
            if unique_days < 2:
                # Not enough history for reliable prediction
                avg_daily = total_consumed / max(1, unique_days)
                confidence = "very low"
            else:
                # Calculate days between first and last consumption
                dates = sorted(list(consumption_dates.keys()))
                first_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
                last_date = datetime.strptime(dates[-1], "%Y-%m-%d").date()
                days_span = max(1, (last_date - first_date).days + 1)  # Add 1 to include both days
                
                avg_daily = total_consumed / days_span
                
                # Determine confidence level
                if days_span >= 14:
                    confidence = "high"
                elif days_span >= 7:
                    confidence = "medium"
                else:
                    confidence = "low"
            
            # Calculate days until depletion
            if avg_daily <= 0:
                days_until_depletion = None
                depletion_date = None
                prediction = "Cannot predict depletion with current consumption rate of 0"
            else:
                days_until_depletion = int(current_quantity / avg_daily)
                today = datetime.now().date()
                depletion_date = today + timedelta(days=days_until_depletion)
                
                if days_until_depletion <= 0:
                    prediction = "Item is depleted or nearly depleted"
                elif days_until_depletion <= 3:
                    prediction = "Critical: Item will be depleted very soon"
                elif days_until_depletion <= 7:
                    prediction = "Warning: Item will be depleted within a week"
                else:
                    prediction = f"Item estimated to last for {days_until_depletion} more days"
            
            return {
                "item_id": item_id,
                "name": item_data.get("name", ""),
                "current_quantity": current_quantity,
                "unit": item_unit,
                "prediction": prediction,
                "avg_daily_consumption": round(avg_daily, 2),
                "days_until_depletion": days_until_depletion,
                "depletion_date": depletion_date.strftime("%Y-%m-%d") if depletion_date else None,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"Error predicting depletion: {str(e)}")
            return {"error": f"Prediction failed: {str(e)}"}
    
    @staticmethod
    def get_shopping_recommendations(user_id: str, days_threshold: int = 7) -> List[Dict]:
        """
        Generate recommendations for items that need to be replenished soon.
        
        Args:
            user_id (str): ID of the user to generate recommendations for
            days_threshold (int): Threshold for days until depletion
            
        Returns:
            List[Dict]: List of items recommended for purchase
        """
        inventory = FreshnessMonitor.load_inventory()
        recommendations = []
        
        for item in inventory:
            item_id = item.get("item_id")
            if not item_id:
                continue
                
            prediction = ConsumptionTracker.predict_depletion(item_id, user_id)
            days_until_depletion = prediction.get("days_until_depletion")
            
            if days_until_depletion is not None and days_until_depletion <= days_threshold:
                recommendations.append({
                    "item_id": item_id,
                    "name": item.get("name", ""),
                    "current_quantity": item.get("quantity", 0),
                    "unit": item.get("unit", ""),
                    "days_until_depletion": days_until_depletion,
                    "depletion_date": prediction.get("depletion_date"),
                    "purchase_urgency": "high" if days_until_depletion <= 3 else "medium"
                })
        
        # Sort by urgency (days until depletion)
        recommendations.sort(key=lambda x: x["days_until_depletion"])
        return recommendations

# ===================================
# Agent 3: Smart Shopping List Generator Agent
# ===================================

class ShoppingListGenerator:
    """Class for generating and managing personalized shopping lists."""
    
    @staticmethod
    def get_user_preferences(user_id: str) -> Dict:
        """
        Get user preferences for shopping and meal planning.
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            Dict: User preferences including dietary restrictions and budget
        """
        users = DataManager.load_data("users.json")
        user = next((u for u in users if u.get("user_id") == user_id), None)
        
        if not user:
            return {"error": "User not found"}
            
        return user.get("preferences", {})
    
    @staticmethod
    def create_shopping_list(user_id: str, budget_constraint: float = None, store_preference: str = None) -> Dict:
        """
        Create a personalized shopping list based on predictions, meal plans, and preferences.
        
        Args:
            user_id (str): ID of the user
            budget_constraint (float, optional): Maximum budget for the shopping list
            store_preference (str, optional): Preferred store for shopping
            
        Returns:
            Dict: Shopping list with items, estimated cost, and metadata
        """
        # Get user preferences
        preferences = ShoppingListGenerator.get_user_preferences(user_id)
        
        if "error" in preferences:
            return {"error": preferences["error"]}
            
        # If no budget constraint provided, use user's default budget
        if budget_constraint is None:
            budget_constraint = float(preferences.get("budget", 0))
        
        # Get consumption predictions for low items
        consumption_recommendations = ConsumptionTracker.get_shopping_recommendations(user_id, days_threshold=10)
        
        # Get items from meal plans
        meal_plans = DataManager.load_data("meal_plans.json")
        user_meal_plans = [plan for plan in meal_plans if plan.get("user_id") == user_id]
        
        # Get current inventory
        inventory = FreshnessMonitor.load_inventory()
        
        # Compile shopping list items
        shopping_items = []
        estimated_cost = 0
        
        # First add items that are running low based on consumption patterns
        for item in consumption_recommendations:
            item_id = item.get("item_id")
            
            # Find item details in inventory
            inventory_item = next((inv for inv in inventory if inv.get("item_id") == item_id), None)
            
            if not inventory_item:
                continue
            
            # Check if the item meets dietary preferences
            category = inventory_item.get("category", "")
            
            # Skip items that don't align with dietary preferences
            diet_restriction = preferences.get("diet", "").lower()
            if diet_restriction == "vegetarian" and category in ["Meat", "Seafood"]:
                continue
            if diet_restriction == "vegan" and category in ["Meat", "Seafood", "Dairy"]:
                continue
                
            # Check for allergies
            allergies = preferences.get("allergies", [])
            allergy_tags = inventory_item.get("allergy_tags", [])
            
            if any(allergy in allergy_tags for allergy in allergies):
                continue
                
            # Calculate purchase quantity based on usage rate
            avg_daily = item.get("avg_daily_consumption", 0)
            if avg_daily <= 0:
                purchase_quantity = 1  # Default quantity
            else:
                # Calculate quantity to last 2 weeks
                purchase_quantity = max(1, round(avg_daily * 14))
                
            # Add to shopping items
            price = float(inventory_item.get("price", 0))
            item_cost = price * purchase_quantity
            
            # Check if adding this item would exceed budget
            if budget_constraint > 0 and estimated_cost + item_cost > budget_constraint:
                # Skip expensive items if budget is tight
                continue
                
            shopping_items.append({
                "item_id": item_id,
                "name": inventory_item.get("name", ""),
                "quantity": purchase_quantity,
                "unit": inventory_item.get("unit", ""),
                "estimated_price": price,
                "estimated_cost": item_cost,
                "store": store_preference or inventory_item.get("store", ""),
                "category": category,
                "reason": "Running low based on consumption patterns"
            })
            
            estimated_cost += item_cost
        
        # Next, add items from meal plans that aren't already in the list
        for plan in user_meal_plans:
            meal_date = plan.get("date", "")
            
            # Only consider upcoming meal plans (within next 7 days)
            try:
                plan_date = datetime.strptime(meal_date, "%Y-%m-%d").date()
                today = datetime.now().date()
                days_until_meal = (plan_date - today).days
                
                if days_until_meal < 0 or days_until_meal > 7:
                    continue
            except (ValueError, TypeError):
                continue
                
            # Get recipe details
            recipe_id = plan.get("recipe_id")
            recipes = DataManager.load_data("recipe_planning.json")
            recipe = next((r for r in recipes if r.get("recipe_id") == recipe_id), None)
            
            if not recipe:
                continue
                
            for ingredient in recipe.get("ingredients", []):
                item_id = ingredient.get("item_id")
                
                # Skip if item is already in shopping list
                if any(item.get("item_id") == item_id for item in shopping_items):
                    continue
                    
                # Check if we have enough in inventory
                inventory_item = next((inv for inv in inventory if inv.get("item_id") == item_id), None)
                
                if not inventory_item:
                    continue
                    
                current_qty = float(inventory_item.get("quantity", 0))
                needed_qty = float(ingredient.get("quantity", 0))
                
                if current_qty >= needed_qty:
                    # We have enough, no need to purchase
                    continue
                    
                # Check dietary restrictions and allergies
                category = inventory_item.get("category", "")
                
                diet_restriction = preferences.get("diet", "").lower()
                if diet_restriction == "vegetarian" and category in ["Meat", "Seafood"]:
                    continue
                if diet_restriction == "vegan" and category in ["Meat", "Seafood", "Dairy"]:
                    continue
                    
                allergies = preferences.get("allergies", [])
                allergy_tags = inventory_item.get("allergy_tags", [])
                
                if any(allergy in allergy_tags for allergy in allergies):
                    continue
                
                # Calculate how much to buy
                purchase_quantity = needed_qty - current_qty
                price = float(inventory_item.get("price", 0))
                item_cost = price * purchase_quantity
                
                # Check budget constraint
                if budget_constraint > 0 and estimated_cost + item_cost > budget_constraint:
                    continue
                    
                shopping_items.append({
                    "item_id": item_id,
                    "name": inventory_item.get("name", ""),
                    "quantity": purchase_quantity,
                    "unit": inventory_item.get("unit", ""),
                    "estimated_price": price,
                    "estimated_cost": item_cost,
                    "store": store_preference or inventory_item.get("store", ""),
                    "category": category,
                    "reason": f"Needed for {recipe.get('name')} on {meal_date}"
                })
                
                estimated_cost += item_cost
        
        # Create the final shopping list
        shopping_list = {
            "list_id": str(uuid.uuid4()),
            "user_id": user_id,
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
            "estimated_total": estimated_cost,
            "items": shopping_items,
            "store_preference": store_preference,
            "budget_constraint": budget_constraint,
            "notes": f"Generated based on consumption patterns and meal plans. Respects {preferences.get('diet', 'no')} diet and avoids {', '.join(preferences.get('allergies', ['no']))} allergies."
        }
        
        # Save to shopping list data
        all_shopping_lists = DataManager.load_data("shopping_list.json")
        all_shopping_lists.append(shopping_list)
        DataManager.save_data("shopping_list.json", all_shopping_lists)
        
        return shopping_list

    @staticmethod
    def optimize_shopping_list(list_id: str, optimization_criteria: str = "cost") -> Dict:
        """
        Optimize an existing shopping list based on given criteria.
        
        Args:
            list_id (str): ID of the shopping list to optimize
            optimization_criteria (str): Criteria for optimization ("cost", "nutrition", "waste")
            
        Returns:
            Dict: Optimized shopping list
        """
        shopping_lists = DataManager.load_data("shopping_list.json")
        shopping_list = next((lst for lst in shopping_lists if lst.get("list_id") == list_id), None)
        
        if not shopping_list:
            return {"error": "Shopping list not found"}
            
        items = shopping_list.get("items", [])
        
        if optimization_criteria == "cost":
            # Sort items by cost efficiency (cost per unit)
            for item in items:
                price = item.get("estimated_price", 0)
                quantity = item.get("quantity", 1)
                item["cost_efficiency"] = price / max(1, quantity)
                
            # Prioritize cost-efficient items
            items.sort(key=lambda x: x.get("cost_efficiency", float('inf')))
            
            # Update list note
            shopping_list["notes"] += " Cost-optimized version."
            
        elif optimization_criteria == "nutrition":
            # This would require nutritional data, placeholder for now
            shopping_list["notes"] += " Nutrition-optimized version."
            
        elif optimization_criteria == "waste":
            # Prioritize items that align with what we already have to reduce waste
            inventory = FreshnessMonitor.load_inventory()
            expiring_soon = FreshnessMonitor.get_expiring_items(days_threshold=10)
            expiring_item_ids = [item.get("item_id") for item in expiring_soon]
            
            # First include items that complement expiring items
            complement_scores = {}
            recipes = DataManager.load_data("recipe_planning.json")
            
            for item in items:
                item_id = item.get("item_id")
                complement_score = 0
                
                # Check if this item appears in recipes with expiring items
                for recipe in recipes:
                    recipe_ingredients = [ing.get("item_id") for ing in recipe.get("ingredients", [])]
                    
                    if item_id in recipe_ingredients:
                        # Count how many expiring items are used in this recipe
                        expiring_ingredients = [ing_id for ing_id in recipe_ingredients if ing_id in expiring_item_ids]
                        complement_score += len(expiring_ingredients)
                
                complement_scores[item_id] = complement_score
                
            # Sort items by complement score (higher is better)
            items.sort(key=lambda x: complement_scores.get(x.get("item_id"), 0), reverse=True)
            
            shopping_list["notes"] += " Waste-reduction optimized version."
        
        # Update the shopping list
        for i, lst in enumerate(shopping_lists):
            if lst.get("list_id") == list_id:
                shopping_lists[i] = shopping_list
                break
                
        DataManager.save_data("shopping_list.json", shopping_lists)
        return shopping_list

# ===================================
# Agent 4: Recipe & Meal Planning Agent
# ===================================

class MealPlanner:
    """Class for meal planning and recipe recommendations."""
    
    @staticmethod
    def suggest_recipes(user_id: str, ingredients: List[str] = None, preferences: Dict = None) -> List[Dict]:
         # Validate ingredients schema
        if ingredients:
            for ingredient in ingredients:
                if not isinstance(ingredient, dict) or 'item_id' not in ingredient or 'name' not in ingredient:
                    raise ValueError("Invalid ingredient format: Each ingredient must have 'item_id' and 'name'")
        """
        Suggest recipes based on available ingredients and user preferences.
        
        Args:
            user_id (str): ID of the user
            ingredients (List[str], optional): List of ingredient IDs to include
            preferences (Dict, optional): User preferences to override stored preferences
            
        Returns:
            List[Dict]: Suggested recipes with scores
        """
        # Get user preferences if not provided
        if not preferences:
            user_prefs = ShoppingListGenerator.get_user_preferences(user_id)
            if "error" in user_prefs:
                return []
            preferences = user_prefs
            
        # Get all recipes
        recipes = DataManager.load_data("recipe_planning.json")
        
        # Get inventory
        inventory = FreshnessMonitor.load_inventory()
        
        # Get expiring items
        expiring_items = FreshnessMonitor.get_expiring_items(days_threshold=5)
        expiring_item_ids = [item.get("item_id") for item in expiring_items]
        
        # Filter recipes based on dietary restrictions
        diet = preferences.get("diet", "").lower()
        allergies = preferences.get("allergies", [])
        
        filtered_recipes = []
        for recipe in recipes:
            # Check dietary compatibility
            recipe_diet = recipe.get("dietary_info", {}).get("diet", "").lower()
            recipe_allergens = recipe.get("dietary_info", {}).get("allergens", [])
            
            # Skip recipes that don't match dietary restrictions
            if diet == "vegetarian" and recipe_diet not in ["vegetarian", "vegan"]:
                continue
            if diet == "vegan" and recipe_diet != "vegan":
                continue
                
            # Skip recipes with allergens
            if any(allergen in recipe_allergens for allergen in allergies):
                continue
                
            filtered_recipes.append(recipe)
        
        # Score recipes based on available ingredients and expiring items
        scored_recipes = []
        for recipe in filtered_recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            
            # Count how many required ingredients we have
            available_count = 0
            expiring_count = 0
            missing_ingredients = []
            
            for ingredient in recipe_ingredients:
                ing_id = ingredient.get("item_id")
                ing_qty = float(ingredient.get("quantity", 0))
                
                # Check if ingredient is in inventory
                inventory_item = next((item for item in inventory if item.get("item_id") == ing_id), None)
                
                if inventory_item:
                    inv_qty = float(inventory_item.get("quantity", 0))
                    if inv_qty >= ing_qty:
                        available_count += 1
                        
                        # Check if ingredient is expiring soon
                        if ing_id in expiring_item_ids:
                            expiring_count += 1
                    else:
                        missing_ingredients.append({
                            "item_id": ing_id,
                            "name": ingredient.get("name", ""),
                            "have": inv_qty,
                            "need": ing_qty,
                            "unit": ingredient.get("unit", "")
                        })
                else:
                    missing_ingredients.append({
                        "item_id": ing_id,
                        "name": ingredient.get("name", ""),
                        "have": 0,
                        "need": ing_qty,
                        "unit": ingredient.get("unit", "")
                    })
            
            # Calculate score based on ingredients
            total_ingredients = len(recipe_ingredients)
            if total_ingredients == 0:
                continue  # Skip recipes with no ingredients
                
            availability_score = available_count / total_ingredients
            expiring_score = expiring_count / max(1, total_ingredients)
            
            # Prioritize recipes that use expiring ingredients
            final_score = (0.6 * availability_score) + (0.4 * expiring_score)
            
            scored_recipes.append({
                "recipe_id": recipe.get("recipe_id"),
                "name": recipe.get("name", ""),
                "availability_score": round(availability_score, 2),
                "expiring_score": round(expiring_score, 2),
                "final_score": round(final_score, 2),
                "total_ingredients": total_ingredients,
                "available_ingredients": available_count,
                "expiring_ingredients": expiring_count,
                "missing_ingredients": missing_ingredients,
                "prep_time": recipe.get("prep_time", ""),
                "dietary_info": recipe.get("dietary_info", {})
            })
        
        # Sort recipes by final score (highest first)
        scored_recipes.sort(key=lambda x: x["final_score"], reverse=True)
        
        # If specific ingredients were provided, further filter recipes
        if ingredients:
            ingredient_filtered = []
            for recipe in scored_recipes:
                recipe_ingredients = [ing.get("item_id") for ing in recipe.get("ingredients", [])]
                
                # Count how many of the specified ingredients are used
                used_count = sum(1 for ing_id in ingredients if ing_id in recipe_ingredients)
                
                if used_count > 0:
                    # Adjust score based on specified ingredients
                    recipe["specified_ingredients_score"] = used_count / len(ingredients)
                    recipe["final_score"] = (0.7 * recipe["final_score"]) + (0.3 * recipe["specified_ingredients_score"])
                    ingredient_filtered.append(recipe)
            
            scored_recipes = ingredient_filtered
            scored_recipes.sort(key=lambda x: x["final_score"], reverse=True)
        
        return scored_recipes
    
    @staticmethod
    def create_meal_plan(user_id: str, start_date: str, days: int = 7) -> Dict:
        """
        Create a meal plan for a specified number of days.
        
        Args:
            user_id (str): ID of the user
            start_date (str): Start date in YYYY-MM-DD format
            days (int): Number of days to plan for
            
        Returns:
            Dict: Meal plan with daily recipes
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD."}
        
        # Get recipe suggestions prioritizing expiring items
        recipe_suggestions = MealPlanner.suggest_recipes(user_id)
        
        if not recipe_suggestions:
            return {"error": "No suitable recipes found based on user preferences"}
        
        # Create meal plan
        meal_plan = {
            "plan_id": str(uuid.uuid4()),
            "user_id": user_id,
            "start_date": start_date,
            "end_date": (start + timedelta(days=days-1)).strftime("%Y-%m-%d"),
            "days": []
        }
        
        # Plan for each day
        recipe_index = 0
        for day in range(days):
            current_date = (start + timedelta(days=day)).strftime("%Y-%m-%d")
            
            # Select recipes for this day (for simplicity, just one main meal per day)
            if recipe_index < len(recipe_suggestions):
                recipe = recipe_suggestions[recipe_index]
                recipe_index += 1
            else:
                # If we ran out of high-scoring recipes, restart from the beginning
                recipe_index = 0
                recipe = recipe_suggestions[0] if recipe_suggestions else None
            
            if recipe:
                day_plan = {
                    "date": current_date,
                    "weekday": (start + timedelta(days=day)).strftime("%A"),
                    "meals": [{
                        "meal_type": "dinner",  # Simplified to just dinner for now
                        "recipe_id": recipe.get("recipe_id"),
                        "recipe_name": recipe.get("name"),
                        "missing_ingredients": recipe.get("missing_ingredients", [])
                    }]
                }
                
                meal_plan["days"].append(day_plan)
                
                # Add to meal_plans.json
                plan_entry = {
                    "date": current_date,
                    "user_id": user_id,
                    "recipe_id": recipe.get("recipe_id"),
                    "meal_type": "dinner"
                }
                
                meal_plans = DataManager.load_data("meal_plans.json")
                
                # Remove any existing plans for this date and user
                meal_plans = [plan for plan in meal_plans if not (
                    plan.get("date") == current_date and 
                    plan.get("user_id") == user_id and
                    plan.get("meal_type") == "dinner"
                )]
                
                meal_plans.append(plan_entry)
                DataManager.save_data("meal_plans.json", meal_plans)
        
        return meal_plan
    
    @staticmethod
    def generate_shopping_list_from_meal_plan(plan_id: str) -> Dict:
        """
        Generate a shopping list based on a specific meal plan.
        
        Args:
            plan_id (str): ID of the meal plan
            
        Returns:
            Dict: Shopping list with required ingredients
        """
        # This functionality is integrated with the ShoppingListGenerator
        # Here we would extract the meal plan details, identify missing ingredients,
        # and call the ShoppingListGenerator to create the list
        
        # For now, returning a placeholder
        return {"message": "This functionality is integrated with the ShoppingListGenerator"}

# ===================================
# Agent 5: Dietary & Preference Alignment Agent
# ===================================

class DietaryPreferenceManager:
    """Class for managing and applying dietary preferences and restrictions."""
    
    @staticmethod
    def update_user_preferences(user_id: str, preferences: Dict) -> bool:
        """
        Update a user's dietary preferences and restrictions.
        
        Args:
            user_id (str): ID of the user
            preferences (Dict): Updated preferences
            
        Returns:
            bool: True if successful, False otherwise
        """
        users = DataManager.load_data("users.json")
        user_index = None
        
        for i, user in enumerate(users):
            if user.get("user_id") == user_id:
                user_index = i
                break
        
        if user_index is None:
            return False
            
        # Update preferences
        users[user_index]["preferences"] = preferences
        DataManager.save_data("users.json", users)
        return True
    
    @staticmethod
    def check_item_compatibility(item_id: str, user_id: str) -> Dict:
        """
        Check if an item is compatible with a user's dietary preferences.
        
        Args:
            item_id (str): ID of the item to check
            user_id (str): ID of the user
            
        Returns:
            Dict: Compatibility assessment
        """
        # Get user preferences
        preferences = ShoppingListGenerator.get_user_preferences(user_id)
        
        if "error" in preferences:
            return {"error": preferences["error"]}
            
        # Get item details
        inventory = FreshnessMonitor.load_inventory()
        item = next((i for i in inventory if i.get("item_id") == item_id), None)
        
        if not item:
            return {"error": "Item not found"}
            
        # Check dietary compatibility
        diet = preferences.get("diet", "").lower()
        allergies = preferences.get("allergies", [])
        
        category = item.get("category", "")
        allergy_tags = item.get("allergy_tags", [])
        
        # Check diet compatibility
        diet_compatible = True
        if diet == "vegetarian" and category in ["Meat", "Seafood"]:
            diet_compatible = False
        if diet == "vegan" and category in ["Meat", "Seafood", "Dairy"]:
            diet_compatible = False
            
        # Check allergy compatibility
        allergy_compatible = not any(allergy in allergy_tags for allergy in allergies)
        
        return {
            "item_id": item_id,
            "name": item.get("name", ""),
            "diet_compatible": diet_compatible,
            "allergy_compatible": allergy_compatible,
            "overall_compatible": diet_compatible and allergy_compatible,
            "reasons": []  # Would list specific compatibility issues
        }
    
    @staticmethod
    def suggest_substitutions(item_id: str, user_id: str) -> List[Dict]:
        """
        Suggest substitute items for ones that don't match dietary preferences.
        
        Args:
            item_id (str): ID of the incompatible item
            user_id (str): ID of the user
            
        Returns:
            List[Dict]: List of substitute items
        """
        compatibility = DietaryPreferenceManager.check_item_compatibility(item_id, user_id)
        
        if "error" in compatibility or compatibility.get("overall_compatible", True):
            return []
            
        # Get user preferences
        preferences = ShoppingListGenerator.get_user_preferences(user_id)
        diet = preferences.get("diet", "").lower()
        
        # Get inventory
        inventory = FreshnessMonitor.load_inventory()
        item = next((i for i in inventory if i.get("item_id") == item_id), None)
        
        if not item:
            return []
            
        substitutes = []
        category = item.get("category", "")
        
        # Find substitutes based on dietary needs
        if category == "Meat" and diet in ["vegetarian", "vegan"]:
            # Suggest plant-based protein substitutes
            for inv_item in inventory:
                if inv_item.get("category") in ["Plant-based", "Protein"]:
                    substitutes.append({
                        "item_id": inv_item.get("item_id"),
                        "name": inv_item.get("name", ""),
                        "category": inv_item.get("category", ""),
                        "compatibility_score": 0.8,  # Placeholder score
                        "reason": "Plant-based protein alternative"
                    })
        elif category == "Dairy" and diet == "vegan":
            # Suggest plant-based dairy alternatives
            for inv_item in inventory:
                if "non-dairy" in inv_item.get("tags", []) or "plant-based" in inv_item.get("tags", []):
                    substitutes.append({
                        "item_id": inv_item.get("item_id"),
                        "name": inv_item.get("name", ""),
                        "category": inv_item.get("category", ""),
                        "compatibility_score": 0.9,  # Placeholder score
                        "reason": "Non-dairy alternative"
                    })
        
        # Check allergy compatibility for substitutes
        allergies = preferences.get("allergies", [])
        compatible_substitutes = []
        
        for sub in substitutes:
            sub_item = next((i for i in inventory if i.get("item_id") == sub.get("item_id")), None)
            if not sub_item:
                continue
                
            allergy_tags = sub_item.get("allergy_tags", [])
            if not any(allergy in allergy_tags for allergy in allergies):
                compatible_substitutes.append(sub)
        
        # Sort by compatibility score
        compatible_substitutes.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)
        return compatible_substitutes

    @staticmethod
    def analyze_nutritional_alignment(user_id: str) -> Dict:
        """
        Analyze how well current inventory and meal plans align with nutritional goals.
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            Dict: Analysis of nutritional alignment
        """
        # Get user preferences
        preferences = ShoppingListGenerator.get_user_preferences(user_id)
        
        if "error" in preferences:
            return {"error": preferences["error"]}
            
        # Get meal plans
        meal_plans = DataManager.load_data("meal_plans.json")
        user_meal_plans = [plan for plan in meal_plans if plan.get("user_id") == user_id]
        
        # Get recipes
        recipes = DataManager.load_data("recipe_planning.json")
        
        # Initialize nutritional tracking
        nutritional_data = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "vitamin_a": 0,
            "vitamin_c": 0,
            "calcium": 0,
            "iron": 0
        }
        
        meal_count = len(user_meal_plans)
        analyzed_meals = 0
        food_categories = {}
        
        # Analyze each meal plan
        for plan in user_meal_plans:
            recipe_id = plan.get("recipe_id")
            if not recipe_id:
                continue
                
            recipe = next((r for r in recipes if r.get("recipe_id") == recipe_id), None)
            if not recipe:
                continue
                
            analyzed_meals += 1
            
            # Track food categories for diversity analysis
            for ingredient in recipe.get("ingredients", []):
                category = ingredient.get("category", "Other")
                food_categories[category] = food_categories.get(category, 0) + 1
                
            # Add nutritional data if available
            if "nutritional_info" in recipe:
                for nutrient, value in recipe.get("nutritional_info", {}).items():
                    if nutrient in nutritional_data:
                        nutritional_data[nutrient] += value
        
        # Calculate daily averages if we have analyzed meals
        if analyzed_meals > 0:
            for nutrient in nutritional_data:
                nutritional_data[nutrient] /= analyzed_meals
        
        # Extract user nutritional goals
        user_goals = preferences.get("nutritional_goals", {})
        adherence_scores = {}
        overall_adherence = 0
        
        # Calculate adherence to nutritional goals
        for nutrient, goal in user_goals.items():
            if nutrient in nutritional_data and goal > 0:
                current = nutritional_data.get(nutrient, 0)
                # Score between 0-1 based on how close to goal
                if current <= goal:
                    adherence = current / goal
                else:
                    # Penalty for exceeding goal (for calories, fat, etc.)
                    adherence = max(0, 1 - ((current - goal) / goal))
                    
                adherence_scores[nutrient] = round(adherence, 2)
                overall_adherence += adherence
        
        if adherence_scores:
            overall_adherence /= len(adherence_scores)
        
        # Analyze food diversity
        diversity_score = min(1.0, len(food_categories) / 8)  # 8 categories considered diverse
        
        # Generate recommendations
        recommendations = []
        
        # Check protein intake
        if nutritional_data.get("protein", 0) < user_goals.get("protein", 50):
            recommendations.append("Increase protein intake with more lean meats, beans, or plant-based proteins")
            
        # Check fiber intake
        if nutritional_data.get("fiber", 0) < user_goals.get("fiber", 25):
            recommendations.append("Add more high-fiber foods like whole grains, fruits, and vegetables")
            
        # Check vitamin/mineral intake
        if nutritional_data.get("vitamin_c", 0) < user_goals.get("vitamin_c", 75):
            recommendations.append("Include more citrus fruits and colorful vegetables for vitamin C")
            
        if nutritional_data.get("calcium", 0) < user_goals.get("calcium", 1000):
            recommendations.append("Consider more calcium-rich foods like dairy or fortified plant alternatives")
            
        # Check diet diversity
        if diversity_score < 0.6:
            recommendations.append("Increase variety in your diet by including more diverse food groups")
            
        # Add default recommendations if none generated
        if not recommendations:
            recommendations = [
                "Maintain your balanced nutritional profile",
                "Consider adding more seasonal fruits and vegetables",
                "Stay hydrated with adequate water intake throughout the day"
            ]
        
        # Map overall adherence to descriptive rating
        if overall_adherence >= 0.8:
            adherence_rating = "high"
        elif overall_adherence >= 0.6:
            adherence_rating = "medium"
        else:
            adherence_rating = "low"
            
        # Map diversity score to descriptive rating
        if diversity_score >= 0.75:
            balance_rating = "high"
        elif diversity_score >= 0.5:
            balance_rating = "medium"
        else:
            balance_rating = "low"
        
        return {
            "user_id": user_id,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "meal_count": meal_count,
            "analyzed_meals": analyzed_meals,
            "dietary_adherence": adherence_rating,
            "nutritional_balance": balance_rating,
            "diversity_score": round(diversity_score, 2),
            "nutrients_per_meal": {k: round(v, 1) for k, v in nutritional_data.items()},
            "adherence_scores": adherence_scores,
            "overall_adherence": round(overall_adherence, 2),
            "food_category_distribution": food_categories,
            "recommendations": recommendations
        }
        

def setup_memory_components():
    """Set up shared memory components for agents."""
    # Initialize data files
    DataManager.initialize_data_files()
    
    # Set up tool registry with memory tools
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    
    return tool_registry

def create_freshness_agent(tool_registry):
    
    """Create the Freshness Monitoring Agent."""
    # Create tools for the freshness agent
    get_expiring_items_tool = BaseTool(
        name="get_expiring_items_tool",
        description="Get items that will expire within a specified number of days",
        function=FreshnessMonitor.get_expiring_items,
        parameters={
            "days_threshold": {
                "type": "integer",
                "description": "Number of days to look ahead for expiring items"
            }
        },
        required=[]  # days_threshold is optional with default value
    )
    
    get_expired_items_tool = BaseTool(
        name="get_expired_items_tool",
        description="Get items that have already expired",
        function=FreshnessMonitor.get_expired_items,
        parameters={},
        required=[]
    )
    
    update_expiry_date_tool = BaseTool(
        name="update_expiry_date_tool",
        description="Update the expiry date for a specific item",
        function=FreshnessMonitor.update_expiry_date,
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
    
    generate_daily_report_tool = BaseTool(
        name="generate_daily_report_tool",
        description="Generate a daily report of expiring items for a specific user",
        function=FreshnessMonitor.generate_daily_report,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            }
        },
        required=["user_id"]
    )
    
    # Register tools
    for tool in [get_expiring_items_tool, get_expired_items_tool, update_expiry_date_tool, generate_daily_report_tool]:
        tool_registry.register_tool(tool)
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="freshness_agent",
        description="Agent for monitoring food freshness and expiry dates",
        model_name="gpt-4o",
        agent_type="FreshnessAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are a Freshness Monitoring Agent responsible for tracking item expiry dates and alerting users about items that need to be used soon.
            You help reduce food waste by providing timely alerts and suggestions for using ingredients before they expire.
            When generating reports, be concise but informative, and prioritize urgent items that will expire soon.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create and return the agent
    return AzureOpenAIAgent(config=agent_config)

def create_consumption_agent(tool_registry):
    """Create the Consumption Tracking & Prediction Agent."""
    # Create tools for the consumption agent
    log_consumption_tool = BaseTool(
        name="log_consumption_tool",
        description="Log the consumption of an item to track usage patterns",
        function=ConsumptionTracker.log_consumption,
        parameters={
            "item_id": {
                "type": "string",
                "description": "ID of the consumed item"
            },
            "user_id": {
                "type": "string",
                "description": "ID of the user who consumed the item"
            },
            "quantity": {
                "type": "number",
                "description": "Amount consumed"
            },
            "unit": {
                "type": "string",
                "description": "Unit of measurement"
            }
        },
        required=["item_id", "user_id", "quantity", "unit"]
    )
    
    predict_depletion_tool = BaseTool(
        name="predict_depletion_tool",
        description="Predict when an item will be depleted based on consumption history",
        function=ConsumptionTracker.predict_depletion,
        parameters={
            "item_id": {
                "type": "string",
                "description": "ID of the item to analyze"
            },
            "user_id": {
                "type": "string",
                "description": "Filter by specific user (optional)"
            }
        },
        required=["item_id"]
    )
    
    get_shopping_recommendations_tool = BaseTool(
        name="get_shopping_recommendations_tool",
        description="Generate recommendations for items that need to be replenished soon",
        function=ConsumptionTracker.get_shopping_recommendations,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user to generate recommendations for"
            },
            "days_threshold": {
                "type": "integer",
                "description": "Threshold for days until depletion"
            }
        },
        required=["user_id"]
    )
    
    # Register tools
    for tool in [log_consumption_tool, predict_depletion_tool, get_shopping_recommendations_tool]:
        tool_registry.register_tool(tool)
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="consumption_agent",
        description="Agent for tracking and predicting item consumption patterns",
        model_name="gpt-4o",
        agent_type="ConsumptionAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are a Consumption Tracking & Prediction Agent that analyzes usage patterns and predicts when items will run out.
            Your goal is to help users maintain optimal inventory levels by providing insights on consumption trends.
            When making predictions, clearly communicate confidence levels and provide actionable recommendations.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create and return the agent
    return AzureOpenAIAgent(config=agent_config)

def create_shopping_list_agent(tool_registry):
    """Create the Smart Shopping List Generator Agent."""
    # Create tools for the shopping list agent
    create_shopping_list_tool = BaseTool(
        name="create_shopping_list_tool",
        description="Create a personalized shopping list based on predictions and meal plans",
        function=ShoppingListGenerator.create_shopping_list,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            },
            "budget_constraint": {
                "type": "number",
                "description": "Maximum budget for the shopping list (optional)"
            },
            "store_preference": {
                "type": "string",
                "description": "Preferred store for shopping (optional)"
            }
        },
        required=["user_id"]
    )
    
    optimize_shopping_list_tool = BaseTool(
        name="optimize_shopping_list_tool",
        description="Optimize an existing shopping list based on given criteria",
        function=ShoppingListGenerator.optimize_shopping_list,
        parameters={
            "list_id": {
                "type": "string",
                "description": "ID of the shopping list to optimize"
            },
            "optimization_criteria": {
                "type": "string",
                "description": "Criteria for optimization (cost, nutrition, waste)"
            }
        },
        required=["list_id"]
    )
    
    # Register tools
    for tool in [create_shopping_list_tool, optimize_shopping_list_tool]:
        tool_registry.register_tool(tool)
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="shopping_list_agent",
        description="Agent for generating smart shopping lists",
        model_name="gpt-4o",
        agent_type="ShoppingListAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are a Smart Shopping List Generator Agent that creates personalized shopping lists based on consumption patterns, expiring items, and meal plans.
            Your goal is to optimize shopping efficiency, reduce waste, and ensure users have what they need while respecting dietary preferences and budget constraints.
            When generating shopping lists, prioritize items that are running low and ingredients needed for upcoming meals.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create and return the agent
    return AzureOpenAIAgent(config=agent_config)

def create_meal_planning_agent(tool_registry):
    """Create the Recipe & Meal Planning Agent."""
    # Create tools for the meal planning agent
    suggest_recipes_tool = BaseTool(
    name="suggest_recipes_tool",
    description="Suggest recipes based on available ingredients and user preferences",
    function=MealPlanner.suggest_recipes,
    parameters={
        "user_id": {
            "type": "string",
            "description": "ID of the user"
        },
        "ingredients": {
            "type": "array",
            "description": "List of ingredient objects to include (optional)"
        },
        "preferences": {
            "type": "object",
            "description": "User preferences to override stored preferences (optional)"
        }
    },
    required=["user_id"]
)
    
    create_meal_plan_tool = BaseTool(
        name="create_meal_plan_tool",
        description="Create a meal plan for a specified number of days",
        function=MealPlanner.create_meal_plan,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            },
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format"
            },
            "days": {
                "type": "integer",
                "description": "Number of days to plan for"
            }
        },
        required=["user_id", "start_date"]
    )
    
    # Register tools
    for tool in [suggest_recipes_tool, create_meal_plan_tool]:
        tool_registry.register_tool(tool)
    
      # Register tools with the agent
    agent_config = AzureOpenAIAgentConfig(
        agent_name="meal_planning_agent",
        description="Agent for recipe suggestions and meal planning based on ingredients",
        model_name="gpt-4o",
        agent_type="Function",
        tool_registry=tool_registry,
        system_prompt="""
        You are a Recipe & Meal Planning Agent. You help users with:
        - Suggesting recipes based on available ingredients
        - Planning meals for the week
        - Finding recipes that use soon-to-expire ingredients
        
        Be specific in your recommendations and explain why you're suggesting certain recipes.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
  
  
    
    # Create and return the agent
    return AzureOpenAIAgent(config=agent_config)

def create_dietary_agent(tool_registry):
    """Create the Dietary & Preference Alignment Agent."""
    # Create tools for the dietary agent
    update_user_preferences_tool = BaseTool(
        name="update_user_preferences_tool",
        description="Update a user's dietary preferences and restrictions",
        function=DietaryPreferenceManager.update_user_preferences,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            },
            "preferences": {
                "type": "object",
                "description": "Updated preferences"
            }
        },
        required=["user_id", "preferences"]
    )
    
    check_item_compatibility_tool = BaseTool(
        name="check_item_compatibility_tool",
        description="Check if an item is compatible with a user's dietary preferences",
        function=DietaryPreferenceManager.check_item_compatibility,
        parameters={
            "item_id": {
                "type": "string",
                "description": "ID of the item to check"
            },
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            }
        },
        required=["item_id", "user_id"]
    )
    
    suggest_substitutions_tool = BaseTool(
        name="suggest_substitutions_tool",
        description="Suggest substitute items for ones that don't match dietary preferences",
        function=DietaryPreferenceManager.suggest_substitutions,
        parameters={
            "item_id": {
                "type": "string",
                "description": "ID of the incompatible item"
            },
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            }
        },
        required=["item_id", "user_id"]
    )
    
    analyze_nutritional_alignment_tool = BaseTool(
        name="analyze_nutritional_alignment_tool",
        description="Analyze how well current inventory and meal plans align with nutritional goals",
        function=DietaryPreferenceManager.analyze_nutritional_alignment,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            }
        },
        required=["user_id"]
    )
    
    # Register tools
    for tool in [update_user_preferences_tool, check_item_compatibility_tool, 
                 suggest_substitutions_tool, analyze_nutritional_alignment_tool]:
        tool_registry.register_tool(tool)
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="dietary_agent",
        description="Agent for managing dietary preferences and restrictions",
        model_name="gpt-4o",
        agent_type="DietaryAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are a Dietary & Preference Alignment Agent that helps users maintain their dietary preferences and nutritional goals.
            Your goal is to ensure shopping lists and meal plans align with user preferences and dietary restrictions.
            When analyzing nutritional alignment, provide specific recommendations for improvement.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create and return the agent
    return AzureOpenAIAgent(config=agent_config)


def create_classifier_agent():
    """Create the classifier agent that determines which agent should handle a request."""
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="classifier_agent",
        description="Agent for classifying user requests and routing them to the appropriate agent",
        model_name="gpt-4o",
        agent_type="AgentClassifier",
        tool_registry=None,
        system_prompt="""
        You are a Classifier Agent responsible for determining which agent should handle user requests.
        
        Analyze the request and return ONLY ONE of the following agent names (no other text):
        - freshness_agent - For requests about expiry dates, alerts about items to use soon
        - consumption_agent - For logging consumption, predicting depletion, shopping recommendations
        - shopping_list_agent - For creating or optimizing shopping lists
        - meal_planning_agent - For recipe suggestions, meal planning based on ingredients
        - dietary_agent - For dietary preferences, restrictions, nutritional analysis
        
        Return ONLY the agent name with no other text or explanation.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create and return the agent
    return AzureOpenAIAgent(config=agent_config)

def create_agents():
    """Create and configure all agents for the food management system."""
    # Set up shared memory components
    tool_registry = setup_memory_components()
    
    # Create individual agents
    freshness_agent = create_freshness_agent(tool_registry)
    consumption_agent = create_consumption_agent(tool_registry)
    shopping_list_agent = create_shopping_list_agent(tool_registry)
    # meal_planning_agent = create_meal_planning_agent(tool_registry)
    dietary_agent = create_dietary_agent(tool_registry)
    classifier_agent = create_classifier_agent()
    
    return {
        "freshness_agent": freshness_agent,
        "consumption_agent": consumption_agent,
        "shopping_list_agent": shopping_list_agent,
        # "meal_planning_agent": meal_planning_agent,
        "dietary_agent": dietary_agent,
        "classifier_agent": classifier_agent
    }
    
    
class FoodAssistantOrchestrator:
    """
    A specialized orchestrator for the food management system that combines
    classification and agent execution in a cohesive flow.
    """
    def __init__(self, agents_dict):
        """
        Initialize the orchestrator with a dictionary of agents.
        
        :param agents_dict: Dictionary mapping agent names to agent instances
        """
        self.agents_dict = agents_dict
        self.agent_registry = AgentRegistry()
        
        # Register all agents
        for agent_name, agent in self.agents_dict.items():
            self.agent_registry.register_agent(agent)
            
        # Create the classifier orchestrator
        self.classifier_orchestrator = SimpleOrchestrator(
            agent_registry=self.agent_registry,
            default_agent_name="classifier_agent"
        )
        
    def process_message(self, thread_id: str, user_message: str, stream_callback=None) -> str:
        """
        Process a user message through the two-step orchestration process.
        
        :param thread_id: The conversation thread ID
        :param user_message: The user's message
        :param stream_callback: Optional callback for streaming responses
        :return: The response from the selected agent
        """
        try:
            # Store user message for context
            EphemeralMemory.store_message(
                thread_id=thread_id,
                sender="user",
                content=user_message
            )
            
            # Get conversation context
            session_summary = EphemeralMemory.get_thread_summary(thread_id)
            enriched_input = f"{session_summary}\nCurrent user message: {user_message}"
            
            # Step 1: Classification - determine which agent should handle the request
            classification_result = self.classifier_orchestrator.orchestrate(
                thread_id=thread_id,
                user_message=enriched_input
            ).strip()
            
            print(f"DEBUG: Classifier selected: {classification_result}")
            
            # Step 2: Route to the appropriate agent
            if classification_result in self.agents_dict:
                # Create a dedicated orchestrator for the selected agent
                agent_orchestrator = SimpleOrchestrator(
                    agent_registry=self.agent_registry,
                    default_agent_name=classification_result
                )
                
                # Get response from the selected agent
                response = agent_orchestrator.orchestrate(
                    thread_id=thread_id,
                    user_message=enriched_input,
                    stream_callback=stream_callback
                )
                
                # Add agent identifier to response
                agent_prefix = f"[{classification_result}] "
                full_response = agent_prefix + response if not response.startswith(agent_prefix) else response
            else:
                # Fallback response if classification fails
                full_response = f"I'm not sure how to handle that request. (Classification attempted: {classification_result})"
                if stream_callback:
                    stream_callback(full_response)
            
            # Store the response in memory
            EphemeralMemory.store_message(
                thread_id=thread_id,
                sender="assistant",
                content=full_response
            )
            
            return full_response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(f"\nDEBUG: {error_msg}")
            return f"I encountered an issue while processing your request. {error_msg}"

def main():
    """Main function to create and configure all agents and handle user interaction."""
    # Initialize data files if needed
    if hasattr(DataManager, 'initialize_data_files'):
        DataManager.initialize_data_files()
    
    # Create all agents
    agents_dict = create_agents()
    
    # Create the specialized orchestrator
    orchestrator = FoodAssistantOrchestrator(agents_dict)
    
    # Set up conversation thread
    thread_id = "food_assistant_conversation"

    print("Welcome To HackIIIT, your personal food management assistant!")
    print("How can I assist you today?")
    print("Type 'exit' to end the conversation.")
    print("-" * 50)
    
    # Function to display streaming responses
    def stream_callback(chunk):
        print(chunk, end="", flush=True)

    # Initialize the conversation with a system message
    EphemeralMemory.store_message(
        thread_id=thread_id, 
        sender="system", 
        content=f"thread ID: {thread_id}"
    )

    while True:
        # Get user input
        user_message = input("\nYou: ").strip()

        # Check for exit condition
        if user_message.lower() == 'exit':
            print("\nThank you for using HACKIIIT. Goodbye!")
            break

        print("\nHACKIIIT: ", end="", flush=True)
        
        # Process the message using our orchestrator
        orchestrator.process_message(
            thread_id=thread_id,
            user_message=user_message,
            stream_callback=stream_callback
        )
        
        print()  # Add a newline after the response

if __name__ == "__main__":
    main()