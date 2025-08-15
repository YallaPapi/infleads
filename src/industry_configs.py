"""
Industry-specific configuration profiles for lead scoring and email templates
"""

from typing import Dict, Any, List


class IndustryConfig:
    """Base configuration for industry-specific lead scoring"""
    
    @staticmethod
    def get_config(industry: str) -> Dict[str, Any]:
        """
        Get configuration for a specific industry
        
        Args:
            industry: Industry type (e.g., 'restaurant', 'dental', 'coffee_equipment')
            
        Returns:
            Configuration dictionary with scoring rules and email templates
        """
        configs = {
            'default': IndustryConfig._default_config(),
            'restaurant': IndustryConfig._restaurant_config(),
            'dental': IndustryConfig._dental_config(),
            'coffee_equipment': IndustryConfig._coffee_equipment_config(),
            'law_firm': IndustryConfig._law_firm_config(),
            'real_estate': IndustryConfig._real_estate_config(),
            'fitness': IndustryConfig._fitness_config(),
            'automotive': IndustryConfig._automotive_config(),
            'beauty_salon': IndustryConfig._beauty_salon_config(),
            'home_services': IndustryConfig._home_services_config()
        }
        
        return configs.get(industry.lower(), configs['default'])
    
    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Default R27 configuration for general businesses"""
        return {
            'name': 'Default Digital Marketing',
            'scoring_rules': {
                'no_website': {'points': 3, 'description': 'No website or broken website'},
                'low_reviews': {'points': 2, 'description': 'Rating < 3.5 or many negative reviews'},
                'few_images': {'points': 2, 'description': 'Less than 3 images on listing'},
                'no_social': {'points': 2, 'description': 'No social media presence'},
                'unclaimed': {'points': 1, 'description': 'Unclaimed Google Business listing'}
            },
            'email_focus': 'general digital marketing improvements',
            'value_propositions': [
                'Improve online visibility',
                'Attract more customers',
                'Build stronger online reputation'
            ]
        }
    
    @staticmethod
    def _restaurant_config() -> Dict[str, Any]:
        """Configuration for restaurants and food service"""
        return {
            'name': 'Restaurant & Food Service',
            'scoring_rules': {
                'no_menu': {'points': 3, 'description': 'No online menu available'},
                'no_ordering': {'points': 3, 'description': 'No online ordering system'},
                'poor_photos': {'points': 2, 'description': 'Poor quality food photos'},
                'old_reviews': {'points': 2, 'description': 'Reviews mention outdated info'},
                'no_hours': {'points': 1, 'description': 'Missing or incorrect hours'},
                'no_social': {'points': 1, 'description': 'No Instagram/Facebook presence'}
            },
            'email_focus': 'restaurant online presence and ordering capabilities',
            'value_propositions': [
                'Increase takeout/delivery orders',
                'Showcase your menu with professional photos',
                'Build loyal customer base through social media'
            ]
        }
    
    @staticmethod
    def _dental_config() -> Dict[str, Any]:
        """Configuration for dental practices"""
        return {
            'name': 'Dental Practice',
            'scoring_rules': {
                'no_booking': {'points': 3, 'description': 'No online appointment booking'},
                'no_patient_forms': {'points': 2, 'description': 'No downloadable patient forms'},
                'no_services_list': {'points': 2, 'description': 'Services not clearly listed'},
                'no_insurance_info': {'points': 2, 'description': 'Insurance info not provided'},
                'poor_reviews_response': {'points': 1, 'description': 'Not responding to reviews'},
                'no_before_after': {'points': 1, 'description': 'No before/after photos'}
            },
            'email_focus': 'dental practice patient acquisition and convenience',
            'value_propositions': [
                'Reduce no-shows with online booking',
                'Attract new patients with better online presence',
                'Streamline patient intake process'
            ]
        }
    
    @staticmethod
    def _coffee_equipment_config() -> Dict[str, Any]:
        """Configuration for B2B coffee equipment suppliers"""
        return {
            'name': 'Coffee Equipment B2B',
            'scoring_rules': {
                'no_catalog': {'points': 3, 'description': 'No product catalog or specs'},
                'no_b2b_portal': {'points': 3, 'description': 'No B2B customer portal'},
                'no_case_studies': {'points': 2, 'description': 'No case studies or testimonials'},
                'no_roi_calculator': {'points': 2, 'description': 'No ROI/cost calculator'},
                'poor_seo': {'points': 1, 'description': 'Not ranking for industry terms'},
                'no_linkedin': {'points': 1, 'description': 'Weak LinkedIn presence'}
            },
            'email_focus': 'B2B lead generation and sales enablement',
            'value_propositions': [
                'Generate qualified B2B leads',
                'Showcase ROI to potential clients',
                'Build authority in coffee industry'
            ]
        }
    
    @staticmethod
    def _law_firm_config() -> Dict[str, Any]:
        """Configuration for law firms"""
        return {
            'name': 'Law Firm',
            'scoring_rules': {
                'no_practice_areas': {'points': 3, 'description': 'Practice areas not clear'},
                'no_attorney_profiles': {'points': 2, 'description': 'No attorney bios/credentials'},
                'no_case_results': {'points': 2, 'description': 'No case results or wins'},
                'no_consultation_form': {'points': 2, 'description': 'No consultation request form'},
                'poor_content': {'points': 1, 'description': 'No legal guides or resources'},
                'no_testimonials': {'points': 1, 'description': 'No client testimonials'}
            },
            'email_focus': 'law firm credibility and client acquisition',
            'value_propositions': [
                'Build trust with potential clients',
                'Showcase expertise and wins',
                'Convert visitors into consultations'
            ]
        }
    
    @staticmethod
    def _real_estate_config() -> Dict[str, Any]:
        """Configuration for real estate agencies"""
        return {
            'name': 'Real Estate',
            'scoring_rules': {
                'no_listings': {'points': 3, 'description': 'No property listings online'},
                'no_virtual_tours': {'points': 2, 'description': 'No virtual tours or videos'},
                'no_market_data': {'points': 2, 'description': 'No market insights/data'},
                'poor_property_search': {'points': 2, 'description': 'Poor property search function'},
                'no_agent_profiles': {'points': 1, 'description': 'Agent profiles lacking'},
                'no_mortgage_calc': {'points': 1, 'description': 'No mortgage calculator'}
            },
            'email_focus': 'real estate lead generation and property showcasing',
            'value_propositions': [
                'Generate more buyer and seller leads',
                'Showcase properties with virtual tours',
                'Build agent personal brands'
            ]
        }
    
    @staticmethod
    def _fitness_config() -> Dict[str, Any]:
        """Configuration for gyms and fitness centers"""
        return {
            'name': 'Fitness & Gym',
            'scoring_rules': {
                'no_class_schedule': {'points': 3, 'description': 'No online class schedule'},
                'no_membership_info': {'points': 2, 'description': 'Pricing not transparent'},
                'no_trainer_profiles': {'points': 2, 'description': 'No trainer bios/certs'},
                'no_virtual_tour': {'points': 2, 'description': 'No facility tour/photos'},
                'no_app': {'points': 1, 'description': 'No mobile app for members'},
                'poor_social': {'points': 1, 'description': 'Weak Instagram presence'}
            },
            'email_focus': 'fitness center member acquisition and retention',
            'value_propositions': [
                'Convert more trial members',
                'Reduce member churn',
                'Build fitness community online'
            ]
        }
    
    @staticmethod
    def _automotive_config() -> Dict[str, Any]:
        """Configuration for auto repair shops"""
        return {
            'name': 'Automotive Repair',
            'scoring_rules': {
                'no_online_booking': {'points': 3, 'description': 'No online appointment booking'},
                'no_service_list': {'points': 2, 'description': 'Services and pricing unclear'},
                'no_coupons': {'points': 2, 'description': 'No online coupons/specials'},
                'no_maintenance_reminders': {'points': 2, 'description': 'No reminder system'},
                'poor_reviews_mgmt': {'points': 1, 'description': 'Not managing reviews'},
                'no_warranty_info': {'points': 1, 'description': 'Warranty info not clear'}
            },
            'email_focus': 'auto shop customer convenience and trust building',
            'value_propositions': [
                'Fill appointment slots faster',
                'Build customer loyalty',
                'Compete with dealerships'
            ]
        }
    
    @staticmethod
    def _beauty_salon_config() -> Dict[str, Any]:
        """Configuration for beauty salons and spas"""
        return {
            'name': 'Beauty & Spa',
            'scoring_rules': {
                'no_online_booking': {'points': 3, 'description': 'No online booking system'},
                'no_portfolio': {'points': 3, 'description': 'No before/after gallery'},
                'no_service_menu': {'points': 2, 'description': 'Services and prices unclear'},
                'poor_instagram': {'points': 2, 'description': 'Weak Instagram presence'},
                'no_staff_profiles': {'points': 1, 'description': 'No stylist/staff profiles'},
                'no_loyalty_program': {'points': 1, 'description': 'No loyalty program info'}
            },
            'email_focus': 'beauty salon booking optimization and social presence',
            'value_propositions': [
                'Reduce no-shows with online booking',
                'Showcase work on Instagram',
                'Build loyal clientele'
            ]
        }
    
    @staticmethod
    def _home_services_config() -> Dict[str, Any]:
        """Configuration for home service providers (plumbing, HVAC, etc.)"""
        return {
            'name': 'Home Services',
            'scoring_rules': {
                'no_instant_quote': {'points': 3, 'description': 'No instant quote form'},
                'no_emergency_info': {'points': 2, 'description': 'Emergency service unclear'},
                'no_service_areas': {'points': 2, 'description': 'Service areas not listed'},
                'no_certifications': {'points': 2, 'description': 'Certifications not shown'},
                'poor_local_seo': {'points': 1, 'description': 'Not optimized for local search'},
                'no_financing': {'points': 1, 'description': 'No financing options shown'}
            },
            'email_focus': 'home service lead generation and trust building',
            'value_propositions': [
                'Generate more emergency calls',
                'Build trust with credentials',
                'Dominate local search results'
            ]
        }
    
    @staticmethod
    def get_available_industries() -> List[str]:
        """Get list of available industry configurations"""
        return [
            'default',
            'restaurant',
            'dental',
            'coffee_equipment',
            'law_firm',
            'real_estate',
            'fitness',
            'automotive',
            'beauty_salon',
            'home_services'
        ]
    
    @staticmethod
    def get_industry_display_names() -> Dict[str, str]:
        """Get display names for industries"""
        return {
            'default': 'General Business',
            'restaurant': 'Restaurants & Food Service',
            'dental': 'Dental Practices',
            'coffee_equipment': 'B2B Equipment Suppliers',
            'law_firm': 'Law Firms',
            'real_estate': 'Real Estate Agencies',
            'fitness': 'Gyms & Fitness Centers',
            'automotive': 'Auto Repair Shops',
            'beauty_salon': 'Beauty Salons & Spas',
            'home_services': 'Home Service Providers'
        }