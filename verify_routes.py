from importlib import import_module
app = import_module('app').application
for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
    print(f"{sorted(rule.methods)} {rule.rule} -> {rule.endpoint}")
