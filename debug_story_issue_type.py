#!/usr/bin/env python3
"""Debug script to analyze Story issue type handling."""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def analyze_story_issue_type():
    """Analyze how Story issue type is handled in the codebase."""
    
    print("Story Issue Type Analysis")
    print("="*60)
    
    print("\nThe current implementation passes issue type as:")
    print('  fields["issuetype"] = {"name": issue_type}')
    print("\nThis should work correctly for 'Story' issue type.")
    
    print("\nPossible reasons for Story issue type failing:")
    print("1. Project doesn't have 'Story' as an available issue type")
    print("   - Some projects only have Task, Bug, Epic, etc.")
    print("   - Story might be disabled in the project settings")
    print("\n2. Case sensitivity issues")
    print("   - Though Jira is usually case-insensitive")
    print("   - Try 'Story', 'story', or 'User Story'")
    print("\n3. Localization")
    print("   - Non-English Jira instances might use different names")
    print("   - E.g., 'Historia' in Spanish, 'Histoire' in French")
    print("\n4. Custom issue type schemes")
    print("   - Some organizations rename or customize issue types")
    print("   - 'Story' might be renamed to 'User Story' or 'Feature'")
    
    print("\n" + "="*60)
    print("Recommended fix:")
    print("-"*40)
    
    fix_code = '''
def create_issue_with_type_validation(
    self,
    project_key: str,
    summary: str,
    issue_type: str,
    **kwargs
):
    """Create issue with issue type validation."""
    
    # Get available issue types for the project
    available_types = self.get_project_issue_types(project_key)
    type_names = [t.get("name", "").lower() for t in available_types]
    
    # Check if requested type is available (case-insensitive)
    if issue_type.lower() not in type_names:
        # Find similar types
        similar = [t for t in available_types 
                  if issue_type.lower() in t.get("name", "").lower()]
        
        if similar:
            suggestion = similar[0]["name"]
            logger.warning(f"Issue type '{issue_type}' not found. "
                         f"Using similar type: '{suggestion}'")
            issue_type = suggestion
        else:
            # List available types
            available_list = ", ".join([t.get("name") for t in available_types])
            raise ValueError(
                f"Issue type '{issue_type}' not available in project {project_key}. "
                f"Available types: {available_list}"
            )
    
    # Continue with creation...
    return self.create_issue(project_key, summary, issue_type, **kwargs)
'''
    
    print(fix_code)
    
    print("\nAlternative approach - Add a helper method:")
    print("-"*40)
    
    helper_code = '''
def normalize_issue_type(self, project_key: str, issue_type: str) -> str:
    """Normalize issue type name to match available types."""
    
    # Common mappings
    type_mappings = {
        "story": ["Story", "User Story", "Feature"],
        "task": ["Task", "Technical Task"],
        "bug": ["Bug", "Defect", "Issue"],
        "epic": ["Epic", "Initiative"],
        "subtask": ["Sub-task", "Subtask"]
    }
    
    # Get available types
    available_types = self.get_project_issue_types(project_key)
    available_names = {t.get("name"): t.get("name") 
                      for t in available_types}
    
    # Direct match (case-insensitive)
    for name in available_names:
        if name.lower() == issue_type.lower():
            return name
    
    # Try common mappings
    lower_type = issue_type.lower()
    if lower_type in type_mappings:
        for variant in type_mappings[lower_type]:
            for name in available_names:
                if name.lower() == variant.lower():
                    return name
    
    # No match found
    return issue_type  # Return original and let API handle the error
'''
    
    print(helper_code)
    
    print("\n" + "="*60)
    print("Summary:")
    print("-"*40)
    print("The current code correctly passes issue type as {'name': issue_type}.")
    print("The issue is likely project-specific configuration.")
    print("\nRecommendation: Add issue type validation/normalization")
    print("to provide better error messages and suggestions.")


if __name__ == "__main__":
    analyze_story_issue_type()