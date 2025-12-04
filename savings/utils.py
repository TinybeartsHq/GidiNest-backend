# savings/utils.py
"""
Utility functions for savings goal calculations and templates
"""
from decimal import Decimal
from typing import Dict, Any


# Cost estimation matrices
COST_ESTIMATES = {
    'hospital_plan': {
        'basic': {'min': 50000, 'max': 150000, 'default': 100000},
        'private': {'min': 200000, 'max': 500000, 'default': 350000},
        'premium': {'min': 600000, 'max': 1500000, 'default': 1000000},
    },
    'baby_essentials': {
        'minimalist': 100000,
        'comfort': 250000,
        'deluxe': 500000,
    },
    'location_multiplier': {
        'Lagos': 1.3,
        'Abuja': 1.2,
        'Port Harcourt': 1.1,
        'Ibadan': 1.0,
        'Kano': 0.95,
        'Enugu': 1.0,
        'default': 1.0,
    }
}


# Goal templates configuration
GOAL_TEMPLATES = {
    'hospital_delivery': {
        'name': 'Hospital Delivery Fund',
        'description': 'Save for your hospital delivery costs',
        'icon': 'hospital-building',
        'category': 'medical',
        'priority': 1,
        'requires': ['hospital_plan', 'location'],
    },
    'baby_essentials': {
        'name': 'Baby Essentials',
        'description': 'Everything your baby needs in the first months',
        'icon': 'baby-carriage',
        'category': 'essentials',
        'priority': 2,
        'requires': ['baby_essentials_preference'],
    },
    'emergency_fund': {
        'name': 'Emergency Medical Fund',
        'description': 'Buffer for unexpected medical expenses',
        'icon': 'shield-check',
        'category': 'emergency',
        'priority': 3,
        'requires': [],
        'fixed_amount': 150000,
    },
    'postpartum_care': {
        'name': 'Postpartum Care',
        'description': 'Recovery and postpartum care expenses',
        'icon': 'heart-plus',
        'category': 'recovery',
        'priority': 4,
        'requires': [],
        'fixed_amount': 100000,
    },
    'baby_clothing': {
        'name': 'Baby Clothing',
        'description': 'First year clothing essentials',
        'icon': 'tshirt',
        'category': 'essentials',
        'priority': 5,
        'requires': [],
        'fixed_amount': 75000,
    },
    'maternity_items': {
        'name': 'Maternity Items',
        'description': 'Maternity clothing and comfort items',
        'icon': 'shopping-bag',
        'category': 'maternity',
        'priority': 6,
        'requires': [],
        'fixed_amount': 50000,
    },
}


def calculate_hospital_delivery_cost(hospital_plan: str, location: str = None) -> Decimal:
    """
    Calculate estimated hospital delivery cost based on plan and location

    Args:
        hospital_plan: One of 'basic', 'private', 'premium'
        location: City/state name for location multiplier

    Returns:
        Decimal: Calculated cost estimate
    """
    plan_costs = COST_ESTIMATES['hospital_plan'].get(hospital_plan, COST_ESTIMATES['hospital_plan']['basic'])
    base_cost = plan_costs['default']

    # Apply location multiplier
    location_key = location if location in COST_ESTIMATES['location_multiplier'] else 'default'
    multiplier = COST_ESTIMATES['location_multiplier'][location_key]

    final_cost = Decimal(str(base_cost * multiplier))
    return final_cost.quantize(Decimal('1'))  # Round to nearest whole number


def calculate_baby_essentials_cost(baby_essentials_preference: str) -> Decimal:
    """
    Calculate baby essentials cost based on preference

    Args:
        baby_essentials_preference: One of 'minimalist', 'comfort', 'deluxe'

    Returns:
        Decimal: Cost estimate
    """
    cost = COST_ESTIMATES['baby_essentials'].get(
        baby_essentials_preference,
        COST_ESTIMATES['baby_essentials']['comfort']
    )
    return Decimal(str(cost))


def calculate_goal_amount(template_id: str, onboarding_context: Dict[str, Any]) -> Decimal:
    """
    Calculate goal amount based on template and onboarding context

    Args:
        template_id: ID of the goal template
        onboarding_context: Dict containing onboarding data (hospital_plan, location, etc.)

    Returns:
        Decimal: Calculated goal amount
    """
    template = GOAL_TEMPLATES.get(template_id)

    if not template:
        return Decimal('0')

    # Check if template has fixed amount
    if 'fixed_amount' in template:
        return Decimal(str(template['fixed_amount']))

    # Calculate based on template type
    if template_id == 'hospital_delivery':
        hospital_plan = onboarding_context.get('hospital_plan', 'basic')
        location = onboarding_context.get('location')
        return calculate_hospital_delivery_cost(hospital_plan, location)

    elif template_id == 'baby_essentials':
        preference = onboarding_context.get('baby_essentials_preference', 'comfort')
        return calculate_baby_essentials_cost(preference)

    # Default to 0 if can't calculate
    return Decimal('0')


def get_goal_template_info(template_id: str) -> Dict[str, Any]:
    """
    Get full template information

    Args:
        template_id: ID of the goal template

    Returns:
        Dict: Template configuration
    """
    return GOAL_TEMPLATES.get(template_id, {})


def get_all_templates() -> Dict[str, Dict[str, Any]]:
    """
    Get all available goal templates

    Returns:
        Dict: All templates
    """
    return GOAL_TEMPLATES


def get_recommended_templates(journey_type: str) -> list:
    """
    Get recommended templates based on journey type

    Args:
        journey_type: One of 'pregnant', 'new_mom', 'trying'

    Returns:
        list: List of recommended template IDs
    """
    if journey_type == 'pregnant':
        return ['hospital_delivery', 'baby_essentials', 'emergency_fund', 'maternity_items', 'postpartum_care']
    elif journey_type == 'new_mom':
        return ['baby_essentials', 'baby_clothing', 'emergency_fund', 'postpartum_care']
    elif journey_type == 'trying':
        return ['hospital_delivery', 'baby_essentials', 'emergency_fund']
    else:
        return ['emergency_fund', 'baby_essentials']
