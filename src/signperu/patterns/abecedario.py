#src/signperu/patterns/abecedario.py
# Placeholder patterns file. Replace with your own patterns exported from the old project.
# The expected structure is a function get_patterns() returning a list of dicts:
# [{'letra': 'A', 'vec': [...]}, ...]

def get_patterns():
    # Example placeholder patterns (empty vectors)
    letters = 'ABCD'
    patterns = []
    for l in letters:
        patterns.append({'letra': l, 'vec': [0.0]*63})
    return patterns
