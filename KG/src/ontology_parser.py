import os
from owlready2 import get_ontology, Thing
from typing import List


def get_leaf_classes(owl_path: str) -> List[str]:
    """
    Parses an OWL file and automatically extracts all bottom-level class names that have no subclasses.
    This usually corresponds to the most specific categories defined in the ontology.

    Args:
        owl_path (str): Path to the .owl file.

    Returns:
        List[str]: List of leaf node class names.
    """
    if not os.path.exists(owl_path):
        print(f"Error: Ontology file not found at {owl_path}")
        return []

    onto = get_ontology(f"file://{os.path.abspath(owl_path)}").load()

    leaf_classes = []
    # Iterate through all classes defined in the ontology
    for cls in onto.classes():
        # Check if this class has subclasses (excluding itself)
        # list(cls.subclasses()) returns direct subclasses
        if not list(cls.subclasses()):
            # Exclude some very basic built-in classes from owlready2 that we don't need
            if cls.name not in ["Nothing", "Thing"]:
                leaf_classes.append(cls.name)

    return list(set(leaf_classes))


def get_leaf_properties(owl_path: str) -> List[str]:
    """
    Parses an OWL file and automatically extracts all bottom-level property names that have no sub-properties.

    Args:
        owl_path (str): Path to the .owl file.

    Returns:
        List[str]: List of leaf node property names.
    """
    if not os.path.exists(owl_path):
        print(f"Error: Ontology file not found at {owl_path}")
        return []

    onto = get_ontology(f"file://{os.path.abspath(owl_path)}").load()

    leaf_properties = []
    # Iterate through all object properties defined in the ontology
    for prop in onto.object_properties():
        # Use .descendants() to determine if a property is a leaf node.
        # If a property's descendant list has length 1, it means only itself, so no sub-properties.
        if len(list(prop.descendants())) == 1:
            # Exclude some built-in top-level and bottom-level properties we don't need
            if prop.name not in ["topObjectProperty", "bottomObjectProperty"]:
                leaf_properties.append(prop.name)

    return list(set(leaf_properties))
