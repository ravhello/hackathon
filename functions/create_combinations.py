def combination_items(n=2, df=df):
    product_combinations = []

    # Create combinations for each client
    for group in df.groupby('ClientID')['ProductID'].apply(list):
        if len(group) >= n:
            product_combinations.extend(combinations(sorted(group), n))

    # Step 3: Create a DataFrame with the product combinations
    df_combinations = pd.DataFrame(product_combinations, columns=[f'ProductID_{i+1}' for i in range(n)])

    # Step 4: Count occurrences of each combination
    product_combination_counts = df_combinations.value_counts().reset_index(name='CombinationCount')

    # Step 5: Merge with products DataFrame to get product names for each ProductID
    for i in range(n):
        product_combination_counts = product_combination_counts.merge(
            df[['ProductID', 'Category']],
            left_on=f'ProductID_{i+1}', right_on='ProductID', how='left'
        ).rename(columns={'Category': f'ProductName_{i+1}'}).drop('ProductID', axis=1)

    # Step 6: Sort by CombinationCount
    sorted_product_combinations = product_combination_counts.sort_values(by='CombinationCount', ascending=False, ignore_index=True)

    # Step 7: Create the combination tuple for FamilyLevel2 columns
    sorted_product_combinations['Combination'] = sorted_product_combinations.iloc[:, :n].apply(tuple, axis=1)

    # Step 8: Filter out relevant columns for plotting (Combination and CombinationCount)
    combination_counts = sorted_product_combinations[['Combination', 'CombinationCount']]

    return combination_counts

def plot_combinations(df):
    # Create the plot with tuples of FamilyLevel2 as x-axis
    plt.figure(figsize=(12, 6))
    
    # Create a barplot
    sns.barplot(x='Combination', y='CombinationCount', data=df, palette='Blues_d')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha="right")

    # Set the plot labels and title
    plt.xlabel('Product Combinations (FamilyLevel2_x, FamilyLevel2_y)')
    plt.ylabel('Combination Count')
    plt.title('Most Frequent Product Combinations')
    plt.tight_layout()
    
    # Show the plot
    plt.show()


