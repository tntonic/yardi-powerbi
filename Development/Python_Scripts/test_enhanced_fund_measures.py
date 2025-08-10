#!/usr/bin/env python3
"""
Test Enhanced Fund Measures
Validates the enhanced Fund 2 and Fund 3 measures using the expanded property lists
"""

import pandas as pd
import numpy as np
from datetime import datetime

def main():
    print("="*80)
    print("TESTING ENHANCED FUND MEASURES")
    print("="*80)
    
    # Load data
    base_path = "/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data"
    
    amendments = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_amendmentsunitspropertytenant.csv")
    terminations = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_terminationtomoveoutreas.csv")
    properties = pd.read_csv(f"{base_path}/Yardi_Tables/dim_property.csv")
    charge_schedule = pd.read_csv(f"{base_path}/Yardi_Tables/dim_fp_amendmentchargeschedule.csv")
    
    # Convert dates
    for df in [amendments, terminations]:
        for col in ['amendment start date', 'amendment end date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    for col in ['acquire date', 'dispose date']:
        if col in properties.columns:
            properties[col] = pd.to_datetime(col, errors='coerce')
    
    # Enhanced Fund 2 property list (from DAX measure)
    enhanced_fund2_properties = [
        "xfl11660", "xfl3333c", "xfl333n6", "xfl3900w", "xfl420sw", "xfl4646g",
        "xfl6704n", "xfl7720p", "xflstuar", "xga1145b", "xga130j", "xga1585r",
        "xga1610s", "xga2100b", "xga265c", "xga2900j", "xga3100j", "xga3350h",
        "xga3471a", "xga3651c", "xga401wi", "xga4225", "xga4450c", "xga4507m",
        "xga4600f", "xga4601", "xga4680n", "xga5070", "xga5121b", "xga800in",
        "xga800wh", "xga9330", "xga9335i", "xgadors", "xgahire1", "xgahire2",
        "xgahire3", "xgahire4", "xgahire5", "xgahire6", "xgahire7", "xgahire8",
        "xgamc200", "xgamc220", "xgamc255", "xgamc260", "xgashaw1", "xgashaw2",
        "xgashaw3", "xgashaw4", "xgashaw5", "xgashaw6", "xil1000a", "xil1000e",
        "xil1001a", "xil1100h", "xil1111", "xil11697", "xil1200p", "xil121lo",
        "xil141be", "xil1600", "xil1600b", "xil1601", "xil1630b", "xil1688",
        "xil1701b", "xil1951", "xil1terr", "xil201ja", "xil2101", "xil222ja",
        "xil231ja", "xil240ja", "xil2500w", "xil250n", "xil2710l", "xil305e",
        "xil464no", "xil529t", "xil700h", "xil747", "xil770ar", "xil7760m",
        "xil77whe", "xil900b", "xilmitch", "xilmount", "xky4175a", "xnj1010",
        "xnj108n", "xnj10tw", "xnj121hi", "xnj121mo", "xnj125al", "xnj128ba",
        "xnj145al", "xnj14rol", "xnj14th", "xnj156al", "xnj1601s", "xnj17pol",
        "xnj1803u", "xnj1980o", "xnj19ind", "xnj19nev", "xnj200ri", "xnj2036b",
        "xnj2050h", "xnj2075h", "xnj220r", "xnj3001i", "xnj30les", "xnj313c",
        "xnj390n", "xnj400wa", "xnj40pot", "xnj420be", "xnj440be", "xnj52col",
        "xnj59cha", "xnj5thor", "xnj6000i", "xnj6900r", "xnj6925s", "xnj6965",
        "xnj70cat", "xnj740co", "xnj7550", "xnj845l", "xnj900k", "xnj9100p",
        "xnj95bau", "xnjcentr", "xnjmorri", "xnjmway0", "xnjmway3", "xnjmway5",
        "xnjmway7", "xnjmway9", "xnjmwayr", "xoh154co", "xoh382c", "xoh8655",
        "xohcolu1", "xohcolu2", "xohcolu3", "xohcolu4", "xohcomme", "xohmost",
        "xpa12111", "xpa18rai", "xpa1peae", "xpa3041m", "xpa327c", "xpa327cr",
        "xpa4200m", "xpa500ma", "xpastate", "xtn187bo", "xtn225bo", "xtn3961o",
        "xtnawg1", "xtnawg2", "xtndelp1", "xtndelp2", "xtx1050k", "xtx10704",
        "xtx111pl", "xtx1121", "xtx11839", "xtx12150", "xtx1709i", "xtx1709s",
        "xtx1721s", "xtx1919a", "xtx2125v", "xtx2445s", "xtx2616a", "xtx2655",
        "xtx310an", "xtx3662m", "xtx3857m", "xtx4201n", "xtx4666d", "xtx4679w",
        "xtx467wa", "xtx8154b", "xtxball", "xtxdrysd", "xtxglen", "xtxmorto",
        "xtxritti", "xtxwebbl",
        # High activity additions
        "xga1157", "3tx00007", "3tx00009", "3ga00010", "3tx00002", "xtx1121"
    ]
    
    # Initial Fund 3 property list
    initial_fund3_properties = [
        "3tx00010", "iga006", "3il00014", "3oh00007", 
        "3il00013", "3nc00008", "3ny00004", "3nj00028",
        "3ca00001", "3nj00027", "ioh001", "3nj00029",
        "3md00004", "3fl00020", "3tn00016"
    ]
    
    # FPR benchmarks
    benchmarks = {
        'Fund 2': {
            'Q1 2025': {'Move-Outs': 712_000, 'Gross Absorption': 198_000, 'Net Absorption': -514_000},
            'Q2 2025': {'Move-Outs': 458_000, 'Gross Absorption': 258_000, 'Net Absorption': -200_000}
        },
        'Fund 3': {
            'Q1 2025': {'Move-Outs': 111_000, 'Gross Absorption': 365_000, 'Net Absorption': 254_000},
            'Q2 2025': {'Move-Outs': 250_600, 'Gross Absorption': 112_000, 'Net Absorption': -138_600}
        }
    }
    
    print(f"Enhanced Fund 2 properties: {len(enhanced_fund2_properties)}")
    print(f"Initial Fund 3 properties: {len(initial_fund3_properties)}")
    
    def calculate_enhanced_measures(fund_properties, period_start, period_end):
        """Calculate enhanced fund measures for a given property list and period"""
        
        # SF Expired calculation
        period_terminations = terminations[
            (terminations['amendment end date'] >= period_start) &
            (terminations['amendment end date'] <= period_end) &
            (terminations['amendment status'].isin(['Activated', 'Superseded'])) &
            (terminations['amendment type'] == 'Termination') &
            (terminations['property code'].isin(fund_properties))
        ]
        
        if len(period_terminations) > 0:
            latest_terminations = period_terminations.groupby(
                ['property code', 'tenant hmy']
            ).apply(lambda x: x.loc[x['amendment sequence'].idxmax()])
            sf_expired = latest_terminations['amendment sf'].sum()
        else:
            sf_expired = 0
        
        # SF Commenced calculation
        period_new_leases = amendments[
            (amendments['amendment start date'] >= period_start) &
            (amendments['amendment start date'] <= period_end) &
            (amendments['amendment status'].isin(['Activated', 'Superseded'])) &
            (amendments['amendment type'].isin(['Original Lease', 'New Lease'])) &
            (amendments['property code'].isin(fund_properties))
        ]
        
        if len(period_new_leases) > 0:
            # Filter to amendments with rent charges
            amendments_with_charges = []
            for _, lease in period_new_leases.iterrows():
                has_charge = len(charge_schedule[
                    (charge_schedule['amendment hmy'] == lease['amendment hmy']) &
                    (charge_schedule['charge code'] == 'rent')
                ]) > 0
                if has_charge:
                    amendments_with_charges.append(lease['amendment hmy'])
            
            period_new_leases = period_new_leases[
                period_new_leases['amendment hmy'].isin(amendments_with_charges)
            ]
            
            if len(period_new_leases) > 0:
                latest_new_leases = period_new_leases.groupby(
                    ['property code', 'tenant hmy']
                ).apply(lambda x: x.loc[x['amendment sequence'].idxmax()])
                sf_commenced = latest_new_leases['amendment sf'].sum()
            else:
                sf_commenced = 0
        else:
            sf_commenced = 0
        
        return sf_expired, sf_commenced, sf_commenced - sf_expired
    
    # Test periods
    periods = {
        'Q1 2025': (pd.Timestamp('2025-01-01'), pd.Timestamp('2025-03-31')),
        'Q2 2025': (pd.Timestamp('2025-04-01'), pd.Timestamp('2025-06-30'))
    }
    
    print("\n" + "="*80)
    print("ENHANCED FUND 2 VALIDATION")
    print("="*80)
    
    for quarter, (start, end) in periods.items():
        print(f"\n{quarter}:")
        print("-" * 40)
        
        sf_expired, sf_commenced, net_absorption = calculate_enhanced_measures(
            enhanced_fund2_properties, start, end
        )
        
        benchmark = benchmarks['Fund 2'][quarter]
        
        expired_accuracy = (1 - abs(sf_expired - benchmark['Move-Outs']) / benchmark['Move-Outs']) * 100 if benchmark['Move-Outs'] > 0 else 0
        commenced_accuracy = (1 - abs(sf_commenced - benchmark['Gross Absorption']) / benchmark['Gross Absorption']) * 100 if benchmark['Gross Absorption'] > 0 else 0
        net_accuracy = (1 - abs(net_absorption - benchmark['Net Absorption']) / abs(benchmark['Net Absorption'])) * 100 if benchmark['Net Absorption'] != 0 else 0
        
        print(f"Move-Outs (SF Expired):     {sf_expired:>10,.0f} | Target: {benchmark['Move-Outs']:>10,.0f} | Accuracy: {expired_accuracy:>6.1f}%")
        print(f"Gross Absorption:           {sf_commenced:>10,.0f} | Target: {benchmark['Gross Absorption']:>10,.0f} | Accuracy: {commenced_accuracy:>6.1f}%")
        print(f"Net Absorption:             {net_absorption:>10,.0f} | Target: {benchmark['Net Absorption']:>10,.0f} | Accuracy: {net_accuracy:>6.1f}%")
    
    print("\n" + "="*80)
    print("INITIAL FUND 3 VALIDATION")
    print("="*80)
    
    for quarter, (start, end) in periods.items():
        print(f"\n{quarter}:")
        print("-" * 40)
        
        sf_expired, sf_commenced, net_absorption = calculate_enhanced_measures(
            initial_fund3_properties, start, end
        )
        
        benchmark = benchmarks['Fund 3'][quarter]
        
        expired_accuracy = (1 - abs(sf_expired - benchmark['Move-Outs']) / benchmark['Move-Outs']) * 100 if benchmark['Move-Outs'] > 0 else 0
        commenced_accuracy = (1 - abs(sf_commenced - benchmark['Gross Absorption']) / benchmark['Gross Absorption']) * 100 if benchmark['Gross Absorption'] > 0 else 0
        net_accuracy = (1 - abs(net_absorption - benchmark['Net Absorption']) / abs(benchmark['Net Absorption'])) * 100 if benchmark['Net Absorption'] != 0 else 0
        
        print(f"Move-Outs (SF Expired):     {sf_expired:>10,.0f} | Target: {benchmark['Move-Outs']:>10,.0f} | Accuracy: {expired_accuracy:>6.1f}%")
        print(f"Gross Absorption:           {sf_commenced:>10,.0f} | Target: {benchmark['Gross Absorption']:>10,.0f} | Accuracy: {commenced_accuracy:>6.1f}%")
        print(f"Net Absorption:             {net_absorption:>10,.0f} | Target: {benchmark['Net Absorption']:>10,.0f} | Accuracy: {net_accuracy:>6.1f}%")
    
    # Calculate overall accuracy
    print("\n" + "="*80)
    print("OVERALL RESULTS")
    print("="*80)
    
    fund2_accuracies = []
    fund3_accuracies = []
    
    for quarter, (start, end) in periods.items():
        # Fund 2
        sf_expired, sf_commenced, net_absorption = calculate_enhanced_measures(
            enhanced_fund2_properties, start, end
        )
        benchmark = benchmarks['Fund 2'][quarter]
        expired_acc = (1 - abs(sf_expired - benchmark['Move-Outs']) / benchmark['Move-Outs']) * 100 if benchmark['Move-Outs'] > 0 else 0
        commenced_acc = (1 - abs(sf_commenced - benchmark['Gross Absorption']) / benchmark['Gross Absorption']) * 100 if benchmark['Gross Absorption'] > 0 else 0
        net_acc = (1 - abs(net_absorption - benchmark['Net Absorption']) / abs(benchmark['Net Absorption'])) * 100 if benchmark['Net Absorption'] != 0 else 0
        fund2_accuracies.extend([expired_acc, commenced_acc, net_acc])
        
        # Fund 3
        sf_expired, sf_commenced, net_absorption = calculate_enhanced_measures(
            initial_fund3_properties, start, end
        )
        benchmark = benchmarks['Fund 3'][quarter]
        expired_acc = (1 - abs(sf_expired - benchmark['Move-Outs']) / benchmark['Move-Outs']) * 100 if benchmark['Move-Outs'] > 0 else 0
        commenced_acc = (1 - abs(sf_commenced - benchmark['Gross Absorption']) / benchmark['Gross Absorption']) * 100 if benchmark['Gross Absorption'] > 0 else 0
        net_acc = (1 - abs(net_absorption - benchmark['Net Absorption']) / abs(benchmark['Net Absorption'])) * 100 if benchmark['Net Absorption'] != 0 else 0
        fund3_accuracies.extend([expired_acc, commenced_acc, net_acc])
    
    fund2_avg_accuracy = np.mean(fund2_accuracies) if fund2_accuracies else 0
    fund3_avg_accuracy = np.mean(fund3_accuracies) if fund3_accuracies else 0
    overall_avg_accuracy = np.mean(fund2_accuracies + fund3_accuracies) if (fund2_accuracies + fund3_accuracies) else 0
    
    print(f"Enhanced Fund 2 Average Accuracy: {fund2_avg_accuracy:.1f}%")
    print(f"Initial Fund 3 Average Accuracy: {fund3_avg_accuracy:.1f}%")
    print(f"Overall Average Accuracy: {overall_avg_accuracy:.1f}%")
    print(f"Target Accuracy: 95%+")
    
    if overall_avg_accuracy >= 95:
        print("\n✅ ENHANCED MEASURES VALIDATION PASSED")
    elif fund2_avg_accuracy >= 80:
        print("\n🔶 PARTIAL SUCCESS - Fund 2 enhanced measures show significant improvement")
        print("   Fund 3 measures need further refinement")
    else:
        print("\n❌ ENHANCED MEASURES VALIDATION FAILED - Further refinement needed")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if fund2_avg_accuracy >= 80:
        print("✅ Fund 2 enhanced property list shows significant improvement")
        print("   Implement enhanced Fund 2 measures in production DAX")
    else:
        print("❌ Fund 2 enhanced property list needs further refinement")
    
    if fund3_avg_accuracy < 50:
        print("❌ Fund 3 property identification needs complete revision")
        print("   Recommend business stakeholder input for Fund 3 scope definition")
    else:
        print("🔶 Fund 3 property identification shows potential but needs refinement")

if __name__ == "__main__":
    main()