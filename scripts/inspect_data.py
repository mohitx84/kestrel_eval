import os
import pandas as pd
import numpy as np

os.makedirs('scripts', exist_ok=True)

train = pd.read_csv('data/raw/train.csv')
test = pd.read_csv('data/raw/test_unlabelled.csv')
res = pd.read_csv('data/raw/resolution_log.csv')
teams = pd.read_csv('data/raw/teams.csv')
sub = pd.read_csv('data/raw/sample_submission.csv')

alias_map = {
    'Installations': 'Installs & Demo',
    'Installs & Demo': 'Installs & Demo',
    'Consumables': 'Filters & Consumables',
    'Filters & Consumables': 'Filters & Consumables',
    'Repairs': 'Repairs',
    'Billing': 'Billing',
    'Returns & Replacement': 'Returns & Replacement',
    'Warranty Claims': 'Warranty Claims',
    'Product Advice': 'Product Advice'
}

m = pd.merge(train, res, on='request_id')
m['first_canonical'] = m['first_team'].map(alias_map)
m['final_canonical'] = m['final_team'].map(alias_map)

print('=== 1. DATASET SHAPES ===')
print(f'Train shape: {train.shape}')
print(f'Test shape: {test.shape}')
print(f'Resolution log shape: {res.shape}')
print(f'Sample submission shape: {sub.shape}')

print('\n=== 2. TRANSFERS SUMMARY ===')
print(m['transfers'].value_counts().sort_index())
print(f"Mean transfers: {m['transfers'].mean():.3f}")
zero_count = (m['transfers'] == 0).sum()
transfer_count = (m['transfers'] > 0).sum()
print(f"Zero transfers: {zero_count} ({zero_count/len(m):.2%})")
print(f"One or more transfers: {transfer_count} ({transfer_count/len(m):.2%})")

print('\n=== 3. AGREEMENT BETWEEN FIRST AND FINAL TEAM ===')
match_canonical = (m['first_canonical'] == m['final_canonical']).sum()
print(f"Canonical match count: {match_canonical} / {len(m)} ({match_canonical/len(m):.2%})")
disagree_count = len(m) - match_canonical
print(f"Disagreed count: {disagree_count} ({disagree_count/len(m):.2%})")

print('\n=== 4. TRANSFERS AND DISAGREEMENT BY INITIAL TEAM ===')
agg_list = []
for team, group in m.groupby('first_canonical'):
    total = len(group)
    transferred = (group['transfers'] > 0).sum()
    disagreed = (group['first_canonical'] != group['final_canonical']).sum()
    agg_list.append({
        'first_team': team,
        'total': total,
        'transferred': transferred,
        'transfer_pct': f"{transferred/total:.1%}",
        'disagreed': disagreed,
        'disagree_pct': f"{disagreed/total:.1%}",
        'avg_transfers': round(group['transfers'].mean(), 2)
    })
df_agg = pd.DataFrame(agg_list).sort_values(by='total', ascending=False)
print(df_agg.to_string(index=False))

print('\n=== 5. CROSSTAB: FIRST CANONICAL VS FINAL CANONICAL ===')
ct = pd.crosstab(m['first_canonical'], m['final_canonical'], margins=True)
print(ct.to_string())

print('\n=== 6. OPERATIONAL COST OF TRANSFERS (Policy §4) ===')
# Each transfer costs Rs 305 handling.
# Misrouted request also generates extra customer contact at Rs 260.
total_transfers = m['transfers'].sum()
handling_cost = total_transfers * 305
misrouted_requests = (m['transfers'] > 0).sum()
extra_contact_cost = misrouted_requests * 260
total_routing_waste_cost = handling_cost + extra_contact_cost

print(f"Total transfers in historical dataset: {total_transfers}")
print(f"Transfer handling cost (Rs 305/transfer): Rs {handling_cost:,.2f}")
print(f"Misrouted requests (transfers > 0): {misrouted_requests}")
print(f"Extra customer contact cost (Rs 260/misrouted): Rs {extra_contact_cost:,.2f}")
print(f"Total historical routing cost penalty: Rs {total_routing_waste_cost:,.2f}")
# Train period is 15 months (2025-04 to 2026-06)
annualized_cost = (total_routing_waste_cost / 15) * 12
print(f"Annualized transfer/misroute operational cost: Rs {annualized_cost:,.2f} per year")
