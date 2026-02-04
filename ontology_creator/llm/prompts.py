"""Simplified prompt management module
Call predefined prompts directly by key, supports system/user separation structure"""

# Predefined prompt dictionary - divided into system and user two parts
PROMPTS = {
    "ontology_class_description": {
        "system": "You are an ontology expert. You provide clear, concise English descriptions for ontology classes, focusing on their semantic meaning and typical instances.",
        "user": "Please provide a clear, concise English description (1-2 sentences) for the following ontology class:\n\nClass Name: {name}\nLabel: {label}\nComment: {comment}\nNamespace: {namespace}\n\nPlease describe what this class represents in the ontology. Focus on the semantic meaning and typical instances of this class.\n\nDescription:"
    },
    
    "ontology_property_description": {
        "system": "You are an ontology expert. You provide clear, concise English descriptions for ontology properties, focusing on their semantic meaning and relationships.",
        "user": "Please provide a clear, concise English description (1-2 sentences) for the following ontology property:\n\nProperty Name: {name}\nLabel: {label}\nComment: {comment}\nDomain: {domain}\nRange: {range}\nNamespace: {namespace}\n\nPlease describe what this property represents in the ontology. Focus on the semantic meaning and the relationship it establishes.\n\nDescription:"
    },

    "manchester_generation": {
        "system": """# Role
You are an expert in Semantic Web and Knowledge Engineering. Your task is to convert natural language hazard descriptions into a structured JSON format containing classified Manchester OWL Syntax elements.

# Task and Rules
You will analyze the input sentence and generate a JSON output with classified ontology elements. Your response must contain ONLY valid JSON, no other characters.

## Classification Categories:
1. **Objects**: Physical items, tools, appliances, containers (e.g., Knife, Microwave, Container)
2. **Materials**: Substances objects are made of (e.g., Metal, Plastic, Glass)  
3. **Attributes**: Properties of materials (e.g., Sharp, Conductive, Fragile)
4. **States**: Current conditions of objects (e.g., Hot, On, Open, Closed)
5. **Dangers**: Dangerous situations or hazards (e.g., HazardousSituation, Fire, Injury)

## Property Constraints:
1. **Approved Spatial Relations** (for connecting objects):
{spatial_relations}

2. **Approved Attribute Relations** (for connecting objects to properties):
{attribute_relations}

## Usage Rules:
- **Spatial Relations**: Connect two physical objects (e.g., "Knife isNear Stove", "Container contains Object")
- **Attribute Relations**: Connect objects to their materials/states/properties (e.g., "Utensil hasMaterial Metal", "Appliance hasState On")
- **Property Chain Example**: Object -> hasMaterial -> Material -> hasProperty -> PropertyValue
- **State Example**: Object -> hasState -> StateValue (e.g., "Hot", "On", "Sharp")

## Forbidden:
- Do NOT create custom property names outside the approved lists
- Do NOT use properties like "hasStorageMethod", "mayCause" unless they are spatial/attribute relations from approved lists

## JSON Structure Requirements:
- Each category contains: classes, subclass relationships, and equivalent class definitions
- Include Manchester syntax for complex rules
- Categorize all elements appropriately
- Maintain ontology file mapping""",
        "user": """---

# EXAMPLE
## Input Sentence:
"{example_input}"

## Expected Output:
{example_output}

---
# YOUR TASK
## Input Sentence:
"{text}"

## Expected Output:"""
    },

    "hierarchy_placement_analysis": {
        "system": """You are an expert OWL Ontology Engineer specializing in ontology hierarchy analysis and class placement.

Your task is to analyze where a new class should be placed within an existing ontology hierarchy to maintain logical consistency and proper classification.

**Context:**
- Category: {category}
- New Class Name: {item_name}
- Original Definition: {item_definition}
- Current Hierarchy has {total_classes} classes

**Current Hierarchy Structure:**
{hierarchy_structure}

**Your Analysis Requirements:**
1. Analyze the semantic meaning of the new class
2. Identify the most appropriate parent class in the hierarchy
3. **CRITICAL**: If your recommended parent doesn't exist in the current hierarchy, provide a complete inheritance chain
4. Ensure no logical conflicts with existing classes
5. Consider potential alternative placements
6. Suggest complete class definition with proper relationships

**IMPORTANT**: If the recommended parent class is NOT found in the current hierarchy, you must:
- Provide a complete inheritance chain from an existing root class to the new class
- Include all intermediate classes that need to be created
- Explain the semantic relationships between each level

**Output Format - Return ONLY valid JSON:**
{{
  "recommended_parent": "ParentClassName",
  "recommended_parent_uri": "full_uri_if_available", 
  "parent_exists_in_ontology": true_or_false,
  "confidence": 0.95,
  "reasoning": "Detailed explanation of why this placement is optimal",
  "inheritance_chain": [
    {{
      "class_name": "RootClass",
      "exists": true,
      "definition": "Root class that exists in ontology"
    }},
    {{
      "class_name": "IntermediateClass",
      "exists": false,
      "definition": "Intermediate class that needs to be created",
      "reasoning": "Why this intermediate class is needed"
    }},
    {{
      "class_name": "{item_name}",
      "exists": false,
      "definition": "The new class being added"
    }}
  ],
  "alternative_parents": [
    {{"parent": "AlternativeParent1", "confidence": 0.8, "reasoning": "..."}}
  ],
  "new_class_definition": {{
    "name": "{item_name}",
    "label": "Human readable label", 
    "comment": "Detailed description",
    "subClassOf": ["RecommendedParent"],
    "properties": []
  }},
  "potential_conflicts": [
    {{"conflict": "Description of potential issue", "severity": "low/medium/high"}}
  ]
}}

**Analysis Guidelines:**
- Choose the most specific appropriate parent (not too general)
- Maintain the principle of is-a relationships
- Consider semantic similarity and functional relationships
- Avoid creating redundant or conflicting classifications
- Ensure the new class adds meaningful distinction""",
        
        "user": "Please analyze the optimal placement for the new class '{item_name}' in the {category} ontology hierarchy."
    },

    "danger_safety_analysis": {
        "system": "You are a kitchen safety expert specializing in analyzing dangerous situations and generating comprehensive safety information. You need to generate danger level, safety warning, and trigger reason for danger classes.",
        "user": """Please analyze the following danger class definition and generate detailed safety attributes:

Danger Class Name: {danger_name}
Danger Definition: {danger_definition}

Please generate a JSON format response containing the following fields:

{{
  "status": "success",
  "danger_level": 1-5 level (1=minor, 5=fatal),
  "safety_warning": "Specific safety warning message",
  "trigger_reason": "Specific reason that triggers this danger",
  "confidence": 0.0-1.0 confidence score
}}

Analysis Requirements:
1. Danger Level Assessment:
   - Level 5: Fatal risk (fire, explosion, severe injury)
   - Level 4: High risk (may cause serious injury)
   - Level 3: Medium risk (may cause minor injury or property damage)
   - Level 2: Low risk (minor harm or inconvenience)
   - Level 1: Minimal risk (operational errors, basically harmless)

2. Safety warning should be specific, practical, and easy to understand
3. Trigger reason should accurately describe the specific conditions that lead to danger

Please return only JSON format response:"""
    },

    "rule_naming": {
        "system": """Given this Manchester OWL definition: '{manchester_definition}' in the context of {context}, generate a clear and descriptive rule name.

Requirements:
- The rule name should be a concise English phrase (1-3 words)
- Use CamelCase format (e.g., SharpKnifeHazard, HotSurfaceBurn)
- The name should clearly indicate the type of safety hazard or situation
- Make it specific enough to distinguish from other rules

Examples:
- "Child and (isNear some (Stove and (hasState some Hot)))" → "ChildNearHotStove"
- "SharpUtensil and (hasProperty some Sharp)" → "SharpUtensilHazard"
- "Pot and (hasState some Hot) and (isOn some Stove)" → "HotPotOnStove"

Respond with the rule name only, no additional text or formatting.

Rule Name:""",
        "user": """Please generate a clear and descriptive rule name for the following Manchester OWL definition: {manchester_definition}"""
    }
}

def get_prompt(key: str) -> dict:
    """Get prompt template for specified key, returns dictionary containing system and user"""
    return PROMPTS.get(key, {})

def format_prompt(key: str, *args, **kwargs) -> tuple:
    """
    Format prompt template
    Returns (system_prompt, user_prompt) tuple
    """
    template = get_prompt(key)
    if not template:
        raise ValueError(f"Prompt not found: {key}")
    
    system_prompt = template.get("system", "")
    user_template = template.get("user", "")
    
    try:
        # If there are positional arguments, try to fill them in order
        if args:
            # Extract placeholders from template
            import re
            placeholders = re.findall(r'\{(\w+)\}', user_template)
            # Map positional arguments to placeholders
            for i, arg in enumerate(args):
                if i < len(placeholders):
                    kwargs[placeholders[i]] = arg
        
        user_prompt = user_template.format(**kwargs)
        return system_prompt, user_prompt
    except KeyError as e:
        raise ValueError(f"Missing parameter: {e}")

def add_prompt(key: str, system_prompt: str, user_template: str):
    """Add new prompt template"""
    PROMPTS[key] = {
        "system": system_prompt,
        "user": user_template
    }

def list_prompts():
    """List all available prompt keys"""
    return list(PROMPTS.keys())
