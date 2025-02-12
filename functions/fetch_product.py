def fetch_product(product_IDs, df):
    if isinstance(product_IDs, (list, tuple)):
        return [fetch_single_product(pid) for pid in product_IDs]
    else:
        return fetch_single_product(product_IDs, df)

def fetch_single_product(product_ID, df):
    # Filter the DataFrame for the given ProductID
    product_info = df[df['ProductID'] == product_ID]

    # Check if the ProductID exists in the DataFrame
    if product_info.empty:
        return ("ProductID not found",)

    # Extract the relevant information
    category = product_info['Category'].values[0]
    family_level1 = product_info['FamilyLevel1'].values[0]
    family_level2 = product_info['FamilyLevel2'].values[0]

    # Return the information as a tuple
    return (category, family_level1, family_level2)


'''
Example of usage for fetch_product

'''

# top_products_during_peak = top_sold_products(3, df, start_date, end_date)
# top_products_during_peak['ProductID'] = top_products_during_peak['ProductID'].apply(lambda x: fetch_product(x, df))
# top_products_during_peak
