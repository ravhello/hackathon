import duckdb
from typing import List

def find_recommended_products(product_ids: List[int], file_paths: List[str], max_results: int = 5) -> List[int]:
    """Get recommended products based on input product IDs."""
    conn = duckdb.connect(":memory:")
    all_recommendations = set()

    # Skip first file if multiple product IDs
    if len(product_ids) > 1:
        file_paths = file_paths[1:]

    products_str = ','.join(str(pid) for pid in product_ids)
    
    for file_path in file_paths:
        query = f"""
            WITH matching_combinations AS (
                SELECT Combination
                FROM read_parquet('{file_path}')
                WHERE ARRAY_CONTAINS(Combination, {list(product_ids)[0]})
                {f"AND ARRAY_CONTAINS(Combination, {list(product_ids)[1]})" if len(product_ids) > 1 else ""}
            ),
            other_products AS (
                SELECT DISTINCT unnest_pid as product_id
                FROM (
                    SELECT UNNEST(Combination) as unnest_pid
                    FROM matching_combinations
                )
                WHERE unnest_pid NOT IN ({products_str})
            )
            SELECT product_id
            FROM other_products
            LIMIT {max_results}
        """
        
        result = conn.execute(query).fetchall()
        all_recommendations.update(row[0] for row in result)
        
        if len(all_recommendations) >= max_results:
            break

    conn.close()
    return list(all_recommendations)[:max_results]


'''

# Usage
file_paths = ['combination_2.parquet', 'combination_3.parquet', 'combination_4.parquet']
# product_ids = [1925906658469214457]
product_ids = [1925906658469214457, 3347883944643182501]

recommended_products = find_recommended_products(product_ids, file_paths)
print(recommended_products)

'''
