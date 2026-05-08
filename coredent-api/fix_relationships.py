"""Diagnostic script to find all missing back_populates relationships"""
import os, re
from collections import defaultdict

# Map: target_model -> set of relationship names needed
needed_by_model = defaultdict(set)
# Map: model -> set of relationship names it already has
has_relationships = defaultdict(set)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'app/models')):
    for f in files:
        if not f.endswith('.py') or f == '__init__.py':
            continue
        path = os.path.join(root, f)
        with open(path) as fh:
            content = fh.read()
        
        # Find all class definitions in this file
        models_in_file = re.findall(r'class (\w+)\(Base\)', content)
        
        # Find all relationships: relationship("TargetModel", back_populates="rel_name")
        for m in re.finditer(r'relationship\("(\w+)"\s*,\s*back_populates="(\w+)"', content):
            target_model = m.group(1)
            rel_name = m.group(2)
            needed_by_model[target_model].add(rel_name)
        
        # Find all relationships this model already has (just the relationship name)
        for m in re.finditer(r'(\w+)\s*=\s*relationship\(', content):
            rel_name = m.group(1)
            for model in models_in_file:
                has_relationships[model].add(rel_name)

print("=== MISSING BACK_POPULATES RELATIONSHIPS ===")
for model, needed in sorted(needed_by_model.items()):
    missing = needed - has_relationships.get(model, set())
    if missing:
        print(f"{model}: missing {missing}")

print("\n=== ALL MODELS AND THEIR RELATIONSHIPS ===")
for model in sorted(has_relationships.keys()):
    print(f"{model}: {sorted(has_relationships[model])}")
