# Universal B2B Lead Generation Adaptation Guide

## Transform R27 for ANY B2B Service

This guide shows how to adapt the system from "digital marketing leads" to generate leads for ANY B2B service (solar, insurance, HVAC, security, payroll, etc.).

## Quick Setup for New Industries

### Step 1: Add Your Industry Config

Edit `src/industry_configs.py` and add your industry:

```python
@staticmethod
def _solar_sales_config():
    return {
        'name': 'Solar Panel Installation',
        'scoring_rules': {
            # What makes a GOOD lead for solar?
            'large_building': {'points': 3, 'description': 'Large roof area or parking lot'},
            'energy_intensive': {'points': 3, 'description': 'Warehouse, manufacturing, cold storage'},
            'old_facility': {'points': 2, 'description': 'Building 20+ years (inefficient)'},
            'no_solar_visible': {'points': 2, 'description': 'No existing solar panels'},
            'daytime_business': {'points': 2, 'description': 'Peak hours match sun hours'}
        },
        'email_focus': 'solar energy savings and tax incentives',
        'value_propositions': [
            'Reduce energy costs by 50-80%',
            'Lock in rates before utility increases',
            '26% federal tax credit available now'
        ]
    }
```

### Step 2: Run with Your Search Terms

```bash
# For Solar Leads
python main.py "warehouses in Phoenix" --industry solar_sales --limit 50
python main.py "manufacturing facilities in Los Angeles" --industry solar_sales --limit 50

# For Insurance Leads  
python main.py "contractors in Miami" --industry business_insurance --limit 50
python main.py "medical offices in Houston" --industry business_insurance --limit 50
```

## Complete Industry Templates

### 🌞 Solar Installation Companies

```python
'scoring_rules': {
    'large_flat_roof': {'points': 4, 'description': 'Ideal for panel installation'},
    'high_electric_usage': {'points': 3, 'description': 'Data center, cold storage, manufacturing'},
    'owns_building': {'points': 3, 'description': 'Not a rented space'},
    'parking_lot': {'points': 2, 'description': 'Ground mount potential'},
    'green_competitor': {'points': 2, 'description': 'Competitors have gone solar'}
}
```

**Best searches:** "warehouses", "distribution centers", "manufacturing plants", "office buildings", "schools"

### 🏥 Insurance Brokers

```python
'scoring_rules': {
    'high_risk_industry': {'points': 4, 'description': 'Construction, transport, medical'},
    'new_business': {'points': 3, 'description': 'Under 2 years old, needs coverage'},
    'growing_fast': {'points': 3, 'description': 'Many employees, expanding'},
    'multiple_locations': {'points': 2, 'description': 'Complex insurance needs'},
    'professional_service': {'points': 2, 'description': 'Needs E&O insurance'}
}
```

**Best searches:** "contractors", "trucking companies", "medical practices", "tech startups", "law firms"

### 🔧 HVAC Services

```python
'scoring_rules': {
    'old_building': {'points': 4, 'description': 'HVAC likely needs replacement'},
    'large_facility': {'points': 3, 'description': 'Complex HVAC needs'},
    'complaints_about_comfort': {'points': 3, 'description': 'Reviews mention temperature'},
    'restaurant_food_service': {'points': 2, 'description': 'Critical HVAC needs'},
    'medical_facility': {'points': 2, 'description': 'Requires precise climate control'}
}
```

**Best searches:** "old office buildings", "restaurants", "medical facilities", "schools", "hotels"

### 💼 Payroll/HR Services

```python
'scoring_rules': {
    'employee_count_growing': {'points': 4, 'description': '10-50 employees, scaling'},
    'no_hr_department': {'points': 3, 'description': 'Small business, owner-run'},
    'high_turnover_industry': {'points': 3, 'description': 'Restaurant, retail, hospitality'},
    'multiple_locations': {'points': 2, 'description': 'Complex payroll needs'},
    'compliance_heavy': {'points': 2, 'description': 'Healthcare, finance industry'}
}
```

**Best searches:** "growing startups", "restaurants", "retail chains", "medical practices", "construction companies"

### 🔒 Security Systems

```python
'scoring_rules': {
    'high_value_inventory': {'points': 4, 'description': 'Jewelry, electronics, pharmacy'},
    'cash_business': {'points': 3, 'description': 'Dispensary, check cashing, casino'},
    'previous_incidents': {'points': 3, 'description': 'Reviews mention theft/security'},
    'no_visible_cameras': {'points': 2, 'description': 'No security visible in photos'},
    '24_hour_operation': {'points': 2, 'description': 'Overnight security needs'}
}
```

**Best searches:** "jewelry stores", "dispensaries", "pharmacies", "electronics stores", "warehouses"

### 📦 Shipping/Logistics Services

```python
'scoring_rules': {
    'ecommerce_business': {'points': 4, 'description': 'Online store needing fulfillment'},
    'manufactures_products': {'points': 3, 'description': 'Needs distribution'},
    'seasonal_business': {'points': 3, 'description': 'Needs flexible logistics'},
    'ships_nationwide': {'points': 2, 'description': 'Complex shipping needs'},
    'growing_fast': {'points': 2, 'description': 'Outgrowing current solution'}
}
```

**Best searches:** "online retailers", "manufacturers", "wholesale distributors", "subscription box companies"

## The Key Changes

### 1. **Scoring Criteria**
Change from "needs better website" to "needs our specific service":
- Solar: Score based on building size, energy usage, roof type
- Insurance: Score based on risk factors, business type, growth
- HVAC: Score based on building age, complaints, facility type

### 2. **Search Queries**
Instead of searching generically, search for your ideal customer:
- Solar: Search for energy-intensive businesses
- Insurance: Search for high-risk industries
- Payroll: Search for growing companies

### 3. **Email Messaging**
The AI automatically adapts emails based on:
- The scoring reasons
- The value propositions you define
- The specific pain points of that industry

## Quick Start Example - Solar Company

```bash
# 1. Add solar config to industry_configs.py (use template above)

# 2. Search for ideal solar customers
python main.py "warehouses in Phoenix Arizona" --industry solar_sales --limit 25

# 3. System will:
#    - Find warehouses (large roofs, high energy use)
#    - Score them based on solar potential
#    - Generate emails about energy savings
#    - Output CSV with scored leads
```

## Tips for Success

1. **Think Like Your Client**: What makes their IDEAL customer?
2. **Search Strategically**: Don't search "businesses", search for specific types
3. **Multiple Searches**: Run different searches for different ideal customer profiles
4. **Test and Refine**: Adjust scoring rules based on what converts

## Remember

The system finds businesses → scores them based on YOUR criteria → writes personalized emails about YOUR service.

It's not about "weak online presence" - it's about finding businesses that need whatever YOU'RE selling!