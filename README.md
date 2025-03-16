# HACKIIIT

Assuming that i have data in a json format

The working Code are expiry.py and meal.py

<!-- APPLICATIONS :
1. You: what all things are about to expire

HACKIIIT: DEBUG: Classifier selected: freshness_agent
Here are the items that will expire within the next 7 days:

1. **Rice** - Expires in 1 day (Quantity: 100 kilograms)
2. **Chicken Breast** - Expires in 4 days (Quantity: 20 kilograms)
3. **Apples** - Expires in 5 days (Quantity: 50 kilograms)
4. **Bread** - Expires in 6 days (Quantity: 30 loaves)

Would you like some suggestions on how to use these items?

You: which item is about to expire in 1 day

HACKIIIT: DEBUG: Classifier selected: freshness_agent
The item that is about to expire in 1 day is **Rice**. You have 100 kilograms of it.

Would you like some suggestions on how to use the rice before it expires? -->


**Expiration & Freshness Monitoring Agent**

---

### **1. Inventory Status & Expiry Tracking**
- **"What items in my inventory are expiring soon?"**  
  → Fetches items that will expire within a given number of days (default: 7).  
- **"Show me items expiring in the next 3 days."**  
  → Customizable threshold for expiring items.  
- **"Do I have any expired items?"**  
  → Lists all items that have already expired.  
- **"How many days until my milk expires?"**  
  → Returns the remaining shelf life of a specific item.  





---

### **2. Usage Recommendations & Waste Prevention**
- **"What should I use first to avoid waste?"**  
  → Provides a prioritized list of items expiring soonest.    
- **"I have eggs, milk, and cheese. What can I make?"**  
  → Checks for relevant recipes using available ingredients.  

---



### **3. Meal Planning Based on Expiry Dates**
- **"Plan my meals for the next 3 days based on what’s expiring."**  
  → Generates meal suggestions to use up soon-to-expire ingredients.  
- **"Suggest breakfast ideas using ingredients that will expire soon."**  
  → Categorizes meals by time of day.  

---






 **Recipe & Meal Planning Agent**  

---

### **1. Recipe Discovery & Recommendations**  
- **"What can I cook with the ingredients I have?"**  
  → Finds recipes that match available ingredients.  
- **"Suggest a recipe using {ingredient1, ingredient2, ...}"**  
  → Searches for recipes based on selected ingredients.  
- **"Find recipes that are at least 70% match with my available ingredients."**  
  → Filters recipes by ingredient match percentage.  
- **"Can you suggest a vegetarian meal?"**  
  → Retrieves vegetarian-friendly recipes.  
- **"What can I make without {ingredient/allergen}?"**  
  → Excludes specific ingredients when searching for recipes.  
- **"Give me some meal ideas for dinner."**  
  → Provides a list of dinner options.  



---

### **2. Meal Planning**  
- **"Create a meal plan considering my allergies & diet preferences."**  
  → Generates a personalized plan based on dietary needs.  

- **"Suggest a high-protein meal plan for the week."**  
  → Focuses on protein-rich meals.  




---

### **3. Grocery Inventory Management**  
- **"What ingredients do I currently have?"**  
  → Displays a list of stored ingredients.  
- **"List all ingredients categorized by type (vegetables, dairy, etc.)."**  
  → Organizes inventory into categories.  
- **"Which ingredients are about to expire?"**  
  → Highlights items nearing expiration.  
- **"Do I have {specific ingredient} in my inventory?"**  
  → Checks for a particular ingredient.  
- **"How much {ingredient} do I have left?"**  
  → Provides quantity details.  



---

### **4. User Preferences & Dietary Restrictions**  
- **"Suggest low-carb meals."**  
  → Recommends low-carb options. 


---

### **5. Recipe Details & Cooking Instructions**  
- **"Show me the full recipe for {recipe_name}."**  
  → Fetches detailed recipe instructions.  
- **"How do I cook {recipe_name}?"**  
  → Provides step-by-step cooking directions.  
- **"What’s average the prep time & cooking time for {recipe_name}?"**  
  → Displays estimated cooking duration.  
- **"List all ingredients needed for {recipe_name}."**  
  → Shows required ingredients.  
- **"What cuisine is {recipe_name} from?"**  
  → Identifies the cuisine type.  







---

