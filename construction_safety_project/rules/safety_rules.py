# safety_rules.py

# This dictionary stores how many frames a person has been seen WITHOUT an item.
# Format: { person_id: { "Helmet": 0, "Glove": 0, "Vest": 0, "Boots": 0 } }
violation_counters = {}
ALERT_THRESHOLD = 20 # Only alert if missing for 20+ consecutive frames

def check_violations(person_id, current_detections):
    """
    Evaluates if a specific person (by ID) is missing gear 
    long enough to trigger a real violation.
    """
    global violation_counters
    
    if person_id not in violation_counters:
        violation_counters[person_id] = {"Helmet": 0, "Gloves": 0, "Vest": 0, "Boots": 0}
    
    missing_this_frame = []
    
    # Check each mandatory item
    for item in ["Helmet", "Gloves", "Vest", "Boots"]:
        if item not in current_detections:
            violation_counters[person_id][item] += 1
        else:
            # Reset counter if item is seen (handles occlusion)
            violation_counters[person_id][item] = 0
            
        # Only add to 'missing' if it's been gone for a while
        if violation_counters[person_id][item] > ALERT_THRESHOLD:
            missing_this_frame.append(item)
            
    return missing_this_frame