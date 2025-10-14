import pandas as pd
from simple_sql_qa_pocketflow import PlotMapNode

# Create dummy dataframe with latitude and longitude (Boston area)
dummy_data = {
    'location': ['Boston Common', 'Fenway Park', 'MIT', 'Harvard Square', 'Quincy Market'],
    'latitude': [42.3551, 42.3467, 42.3601, 42.3736, 42.3601],
    'longitude': [-71.0656, -71.0972, -71.0942, -71.1191, -71.0542]
}

df_test = pd.DataFrame(dummy_data)
print("Test DataFrame:")
print(df_test)
print()

# Test PlotMapNode
plot_node = PlotMapNode()

# Create a shared state dict (as PocketFlow expects)
shared = {'df': df_test}

# Run the node
prep_res = plot_node.prep(shared)
exec_res = plot_node.exec(prep_res)
plot_node.post(shared, prep_res, exec_res)

print(f"\nMap file saved: {shared.get('map_file')}")

