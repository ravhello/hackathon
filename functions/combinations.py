
def find_other_products_in_combinations(productIDs, file_paths):
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("FindOtherProductsInCombinations") \
        .getOrCreate()

    result = []

    # Ensure productIDs are integers
    productIDs = [int(productID) for productID in productIDs]

    if len(productIDs) > 1:
      file_paths = file_paths[1:]

    for file_path in file_paths:
        # Read the Parquet file
        df = spark.read.parquet(file_path)

        # Explode the combinations to individual rows
        exploded_df = df.withColumn("product", explode(col("Combination")))

        if len(productIDs) == 1:
            # Filter rows where the single productID is in the combination
            filtered_df = exploded_df.filter(array_contains(col("Combination"), lit(productIDs[0]))).select("Combination")

            # Extract other products
            other_products_df = filtered_df.withColumn(
                "other_products",
                array_except(col("Combination"), array([lit(productIDs[0])]))
            )
        elif len(productIDs) == 2:
            # Filter rows where both productID1 and productID2 are in the combination
            filtered_df = exploded_df.filter(
                (array_contains(col("Combination"), lit(productIDs[0]))) &
                (array_contains(col("Combination"), lit(productIDs[1])))
            ).select("Combination")

            # Extract other products
            other_products_df = filtered_df.withColumn(
                "other_products",
                array_except(col("Combination"), array([lit(productIDs[0]), lit(productIDs[1])]))
            )
        else:
            raise ValueError("Only 1 or 2 product IDs are supported.")

        # Collect the results and limit to 5 unique items
        other_products_set = set()
        for row in other_products_df.select("other_products").rdd.flatMap(lambda x: x).collect():
            for prod in row:
                if len(other_products_set) < 5:
                    other_products_set.add(prod)
                if len(other_products_set) >= 5:
                    break

        # Append the results to the result list
        result.append((file_path, list(other_products_set)))

    # Stop the Spark session
    spark.stop()

    return result

'''
THE BELOW EXAMPLE IS FOR SPARK

'''


# # Example usage
# file_paths = ['combination_2.parquet', 'combination_3.parquet', 'combination_4.parquet']
# # productIDs = [1925906658469214457]  # Replace with the actual productID(s) you want to search for
# productIDs = [1925906658469214457, 3347883944643182501]

# other_products = find_other_products_in_combinations(productIDs, file_paths)

# for file_path, products in other_products:
#     print(f"In file {file_path}, the other products in the combination with {productIDs} are: {products}")