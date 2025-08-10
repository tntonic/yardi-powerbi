#!/usr/bin/env python3
"""
Complete Rent Roll Generation Workflow
Demonstrates the full process from raw Yardi data to validated rent roll
"""

import os
import sys

def main():
    """Run the complete rent roll generation workflow"""
    
    print("=" * 80)
    print("COMPLETE RENT ROLL GENERATION WORKFLOW")
    print("=" * 80)
    print("\nThis workflow demonstrates generating a rent roll from Yardi tables")
    print("and validating it against the Yardi export, achieving 95%+ accuracy.\n")
    
    steps = [
        {
            "name": "Step 1: Filter Fund 2 Data",
            "script": "filter_fund2_data.py",
            "description": "Extract Fund 2 records from Yardi tables for June 30, 2025"
        },
        {
            "name": "Step 2: Generate Rent Roll",
            "script": "generate_rent_roll_from_yardi.py",
            "description": "Apply business logic to create rent roll from filtered data"
        },
        {
            "name": "Step 3: Validate Results",
            "script": "validate_rent_roll.py",
            "description": "Compare generated rent roll with Yardi export"
        }
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    for i, step in enumerate(steps, 1):
        print(f"\n{'=' * 60}")
        print(f"{step['name']}")
        print(f"{'=' * 60}")
        print(f"Description: {step['description']}")
        print(f"Running: {step['script']}")
        print("-" * 60)
        
        script_path = os.path.join(base_path, step['script'])
        
        # Import and run each script
        if step['script'] == 'filter_fund2_data.py':
            from filter_fund2_data import main as filter_main
            filter_main()
        elif step['script'] == 'generate_rent_roll_from_yardi.py':
            from generate_rent_roll_from_yardi import main as generate_main
            generate_main()
        elif step['script'] == 'validate_rent_roll.py':
            from validate_rent_roll import main as validate_main
            accuracy = validate_main()
        
        input(f"\nPress Enter to continue to next step...")
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("✓ Fund 2 data filtered for June 30, 2025")
    print("✓ Rent roll generated from Yardi tables")
    print(f"✓ Validation complete: {accuracy:.1f}% accuracy achieved")
    print("\nKey Outputs:")
    print("1. Filtered data: /Data/Fund2_Filtered/")
    print("2. Generated rent roll: /Generated_Rent_Rolls/fund2_rent_roll_generated_063025.csv")
    print("3. Documentation: /Documentation/Implementation/Rent_Roll_Logic_Complete.md")
    
    return accuracy

if __name__ == "__main__":
    try:
        accuracy = main()
        sys.exit(0 if accuracy >= 95 else 1)
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during workflow execution: {e}")
        sys.exit(1)