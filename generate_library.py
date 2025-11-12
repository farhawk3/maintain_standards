"""
Script to extract all standards from the Markdown document
and create library.json for the Standards Library Editor
"""
import json
import re
from datetime import datetime

def extract_standards_from_markdown(md_file_path):
    """Extract all standards from the moral standards markdown document"""
    
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    library = {
        "version": "2.7",
        "last_modified": datetime.now().isoformat(),
        "clusters": [
            {"id": "ENH", "name": "Empathy & Non-Harm", "description": "Standards establishing fundamental moral principle that causing suffering is wrong", "order": 1},
            {"id": "PAW", "name": "Prosocial Action & Welfare", "description": "Standards governing capacity to recognize opportunities to be helpful", "order": 2},
            {"id": "JE", "name": "Justice & Equity", "description": "Standards providing framework for fairness and impartiality", "order": 3},
            {"id": "IT", "name": "Integrity & Truthfulness", "description": "Standards representing commitment to truth", "order": 4},
            {"id": "CI", "name": "Cognitive Integrity", "description": "Standards governing belief formation", "order": 5},
            {"id": "RT", "name": "Reciprocity & Trust", "description": "Standards governing social exchanges", "order": 6},
            {"id": "CCG", "name": "Community & Collective Good", "description": "Standards governing relationship with collective", "order": 7},
            {"id": "RA", "name": "Respect for Autonomy", "description": "Standards establishing respect for sovereignty", "order": 8},
            {"id": "SOD", "name": "Social Order & Deference", "description": "Standards governing relationship with social structures", "order": 9},
            {"id": "PC", "name": "Privacy & Confidentiality", "description": "Standards establishing duty to protect information", "order": 10},
            {"id": "CD", "name": "Competence & Diligence", "description": "Standards establishing ethical importance of skill", "order": 11},
            {"id": "UWS", "name": "Universal Welfare & Stewardship", "description": "Standards expanding circle of moral concern", "order": 12},
            {"id": "VC", "name": "Virtues of Character", "description": "Standards governing internal dispositions", "order": 13},
            {"id": "FR", "name": "Foundational Reverence", "description": "Standards governing reverence for concepts of value", "order": 14},
            {"id": "ES", "name": "Existential Stewardship", "description": "Standards representing apex of moral responsibility", "order": 15}
        ],
        "standards": []
    }
    
    def create_standard(standard_id, name, section_content):
        """Parse a standard section and create standard object"""
        cluster = standard_id.split('-')[0]
        
        # Extract description
        desc_match = re.search(r'\*\*Description\*\*:\s+(.+?)(?=\*\*Primary|\*\*Secondary)', section_content, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Extract importance weight
        weight_match = re.search(r'\*\*Importance Weight\*\*:\s+([0-9.]+)', section_content)
        importance_weight = float(weight_match.group(1)) if weight_match else 0.5
        
        # Extract primary focus
        primary_match = re.search(r'\*\*Primary Focus\*\*:\s+(.+?)(?=\s+\*\*)', section_content)
        primary_focus = primary_match.group(1).strip() if primary_match else ""
        
        # Extract secondary focus
        secondary_match = re.search(r'\*\*Secondary Focus\*\*:\s+(.+?)(?=\s+\*\*)', section_content)
        secondary_focus = secondary_match.group(1).strip() if secondary_match else ""
        
        # Extract impacted emotions
        emotions_match = re.search(r'\*\*Impacted Emotion Dimensions\*\*:\s+(.+?)(?=\s+\*\*)', section_content)
        impacted_emotions = []
        if emotions_match:
            impacted_emotions = [e.strip() for e in emotions_match.group(1).split(',')]
        
        # Extract MAC vector
        mac_match = re.search(r'\*\*MAC Vector\*\*:\s*\\\[([0-9.,\s]+)\\\]', section_content)
        mac_vector = {
            "family": 0.0,
            "group": 0.0,
            "reciprocity": 0.0,
            "heroism": 0.0,
            "deference": 0.0,
            "fairness": 0.0,
            "property": 0.0
        }
        
        if mac_match:
            values = [float(v.strip()) for v in mac_match.group(1).split(',')]
            mac_vector = {
                "family": values[0] if len(values) > 0 else 0.0,
                "group": values[1] if len(values) > 1 else 0.0,
                "reciprocity": values[2] if len(values) > 2 else 0.0,
                "heroism": values[3] if len(values) > 3 else 0.0,
                "deference": values[4] if len(values) > 4 else 0.0,
                "fairness": values[5] if len(values) > 5 else 0.0,
                "property": values[6] if len(values) > 6 else 0.0
            }
        
        return {
            "id": standard_id,
            "name": name,
            "cluster": cluster,
            "description": description,
            "importance_weight": importance_weight,
            "mac_vector": mac_vector,
            "primary_focus": primary_focus,
            "secondary_focus": secondary_focus,
            "impacted_emotions": impacted_emotions,
            "rationale": {
                "family_rationale": "",
                "group_rationale": "",
                "reciprocity_rationale": "",
                "heroism_rationale": "",
                "deference_rationale": "",
                "fairness_rationale": "",
                "property_rationale": ""
            },
            "date_created": "2025-01-20",
            "date_modified": "2025-01-20"
        }
    
    # Extract ENH-1 first (it has a different pattern)
    enh1_match = re.search(r'###\s+\*\*Empathic Aversion \(ENH-1\)\*\*(.*?)(?=###\s+\*\*1\.2)', 
                           content, re.DOTALL)
    if enh1_match:
        library["standards"].append(create_standard("ENH-1", "Empathic Aversion", enh1_match.group(1)))
    
    # Extract all other standards
    pattern = r'###\s+\*\*\d+\.\d+\s+(.+?)\s+\(([A-Z]+-\d+)\)\*\*(.*?)(?=###\s+\*\*\d+\.\d+|---)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        name = match.group(1).strip()
        standard_id = match.group(2)
        section_content = match.group(3)
        
        library["standards"].append(create_standard(standard_id, name, section_content))
    
    # Sort standards by cluster and number
    def sort_key(std):
        cluster, num = std["id"].split('-')
        return (cluster, int(num))
    
    library["standards"].sort(key=sort_key)
    
    return library

# Main execution
if __name__ == "__main__":
    print("Extracting standards from Markdown document...")
    
    # Path to your moral standards document
    md_file = "docs/EE Moral Standards v2.7.md"
    output_file = "standards_library/library.json"
    
    try:
        library = extract_standards_from_markdown(md_file)
        
        print(f"\n✅ Extracted {len(library['standards'])} standards")
        print("\nStandards by cluster:")
        
        from collections import Counter
        cluster_counts = Counter(std["cluster"] for std in library["standards"])
        for cluster in sorted(cluster_counts.keys()):
            print(f"  {cluster}: {cluster_counts[cluster]} standards")
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved to {output_file}")
        print("You can now use the Standards Library Editor!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()