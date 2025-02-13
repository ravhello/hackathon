# %%
# %%
import pandas as pd
import numpy as np
import os
from vowpalwabbit import pyvw
from tqdm.notebook import tqdm

# -----------------------------
# 1. Load Data
# -----------------------------
data = pd.read_parquet("final_df.parquet")
clients_df = pd.read_csv("clients_dataset.csv")
stocks_df = pd.read_csv("stocks_dataset.csv")

# -----------------------------
# 2. Preprocess Data (Time-based)
# -----------------------------
data = data.sort_values("TransactionDate").reset_index(drop=True)

for col in ['Category', 'FamilyLevel1', 'FamilyLevel2', 'Brand', 'StoreCountry']:
    if col not in stocks_df.columns:
        stocks_df[col] = "Unknown"
if 'StoreID' not in stocks_df.columns:
    stocks_df['StoreID'] = "0"

data['ClientGender'].fillna('Unknown', inplace=True)
data['DaysSinceLastTransaction'].replace(0, 900, inplace=True)
data['AverageFrequencySoFar'].replace(900, 0, inplace=True)
data['Quarter'] = data['TransactionDate'].dt.quarter
data = data.loc[:, ~data.columns.str.contains('Rolling90Pct')]

# -----------------------------
# 2a. Undersampling top 1000 sold products
# -----------------------------
print("Computing top 1000 products by total quantity sold...")
top_1000_products = (
    data.groupby('ProductID')['Quantity_sold']
    .sum()
    .sort_values(ascending=False)
    .head(1000)
    .index
)
top_1000_products = set(top_1000_products)

# Filter both data and stocks_df to these top 1000 products
data = data[data['ProductID'].isin(top_1000_products)].copy()
stocks_df = stocks_df[stocks_df['ProductID'].isin(top_1000_products)].copy()

print(f"After top-1000 undersampling:\n  - data has {len(data)} rows\n  - stocks_df has {len(stocks_df)} rows")

# * (Optional) If you still want to ensure all products are purchased at least once,
#   you can keep or remove the next lines as needed:
# purchased_products = set(data['ProductID'].unique())
# stocks_df = stocks_df[stocks_df['ProductID'].isin(purchased_products)].copy()

# -----------------------------
# 3. Create a ProductID->Universe map
# -----------------------------
product_universe_map = data.groupby("ProductID")["Universe"].last().to_dict()

# -----------------------------
# 4. Utility Functions
# -----------------------------
def generate_negative_samples(df, n_neg=10):
    """
    Generate negative samples for implicit feedback data.
    Sceglie fino a n_neg prodotti, tra quelli apparsi in df, che lo user non ha acquistato.
    """
    all_products = np.array(df['ProductID'].unique())

    neg_samples = []
    grouped = df.groupby("ClientID")["ProductID"].apply(set).to_dict()
    for client_id, pos_products in grouped.items():
        available_neg = np.setdiff1d(all_products, list(pos_products))
        if len(available_neg) < n_neg:
            sampled_neg = np.random.choice(available_neg, n_neg, replace=True)
        else:
            sampled_neg = np.random.choice(available_neg, n_neg, replace=False)
        base_info = df[df["ClientID"] == client_id].iloc[-1].to_dict()
        for neg_product in sampled_neg:
            row_dict = {**base_info, "ProductID": neg_product, "Label": 0}
            neg_samples.append(row_dict)
    return pd.DataFrame(neg_samples)

def convert_to_vw(row):
    client_part = (
        f"ClientID:{row['ClientID']} "
        f"Age:{row['Age']:.2f} "
        f"Gender:{row['ClientGender']} "
        f"Segment:{row['ClientSegment']} "
        f"Country:{row['ClientCountry']} "
        f"OptEmail:{row['ClientOptINEmail']} "
        f"OptPhone:{row['ClientOptINPhone']}"
    )
    product_part = (
        f"ProductID:{row['ProductID']} "
        f"Category:{row['Category']} "
        f"FamilyLevel1:{row['FamilyLevel1']} "
        f"FamilyLevel2:{row['FamilyLevel2']} "
        f"Brand:{row['Brand']} "
        f"Universe:{row.get('Universe', 'Unknown')} "
        f"product_avg_price_order:{row['product_avg_price_order']:.2f} "
        f"avg_price:{row['avg_price']:.2f}"
    )
    store_part = (
        f"StoreID:{row['StoreID']} "
        f"Country:{row['StoreCountry']}"
    )
    interaction_part = (
        f"Quarter:{row['Quarter']} "
        f"Weekday:{row['Weekday']} "
        f"DaysSinceLastTransaction:{row['DaysSinceLastTransaction']} "
        f"CumulativeSpent:{row['CumulativeSpent']:.2f} "
        f"CumulativeQuantity:{row['CumulativeQuantity']} "
        f"PercentageMaleProductsSoFar:{row['PercentageMaleProductsSoFar']:.2f} "
        f"UniqueProductsSoFar:{row['UniqueProductsSoFar']} "
        f"AverageAmountPerTransactionSoFar:{row['AverageAmountPerTransactionSoFar']:.2f} "
        f"AverageFrequencySoFar:{row['AverageFrequencySoFar']:.2f} "
        f"AveragePrice:{row['AveragePrice']:.2f} "
        f"Frequency30:{row['Frequency_30']:.2f} "
        f"Monetary30:{row['Monetary_30']:.2f} "
        f"Recency30:{row['Recency_30']} "
        f"Frequency60:{row['Frequency_60']:.2f} "
        f"Monetary60:{row['Monetary_60']:.2f} "
        f"Recency60:{row['Recency_60']} "
        f"Frequency90:{row['Frequency_90']:.2f} "
        f"Monetary90:{row['Monetary_90']:.2f} "
        f"Recency90:{row['Recency_90']} "
        f"Quantity_sold:{row['Quantity_sold']} "
        f"SalesNetAmountEuro:{row['SalesNetAmountEuro']:.2f} "
        f"Month:{row['Month']} "
        f"Season:{row['Season']}"
    )
    vw_string = (
        f"{row['Label']} "
        f"|Client {client_part} "
        f"|Product {product_part} "
        f"|Store {store_part} "
        f"|Interaction {interaction_part}"
    )
    return vw_string

def generate_vw_file(df, file_path):
    df = df.sort_values("TransactionDate")
    df["vw_format"] = df.apply(convert_to_vw, axis=1)
    df["vw_format"].to_csv(file_path, index=False, header=False)

def generate_recommendations_day(client_id, day, n_recommendations, model_file):
    day = pd.Timestamp(day).normalize()
    subset_client = data[(data["ClientID"] == client_id) & (data["TransactionDate"] <= day)]
    
    if not subset_client.empty:
        client_data = subset_client.iloc[-1].copy()
        client_data["Label"] = 1
    else:
        client_profile = clients_df[clients_df["ClientID"] == client_id]
        if client_profile.empty:
            raise ValueError(f"ClientID {client_id} not found.")
        row_dict = client_profile.iloc[0].to_dict()
        row_dict.update({
            "Age": row_dict.get("Age", 30) if pd.notnull(row_dict.get("Age")) else 30,
            "ClientGender": row_dict.get("ClientGender", "Unknown"),
            "ClientSegment": row_dict.get("ClientSegment", "UNKNOWN"),
            "ClientCountry": row_dict.get("ClientCountry", "Unknown"),
            "Quantity_sold": 0,
            "SalesNetAmountEuro": 0.0,
            "DaysSinceLastTransaction": 900,
            "CumulativeSpent": 0.0,
            "CumulativeQuantity": 0,
            "PercentageMaleProductsSoFar": 0.0,
            "UniqueProductsSoFar": 0,
            "AverageAmountPerTransactionSoFar": 0.0,
            "AverageFrequencySoFar": 0.0,
            "AveragePrice": 0.0,
            "Frequency_30": 0.0,
            "Monetary_30": 0.0,
            "Recency_30": 30,
            "Frequency_60": 0.0,
            "Monetary_60": 0.0,
            "Recency_60": 60,
            "Frequency_90": 0.0,
            "Monetary_90": 0.0,
            "Recency_90": 90,
            "product_avg_price_order": 0.0,
            "avg_price": 0.0,
            "Weekday": day.weekday(),
            "Quarter": day.quarter,
            "Month": day.month,
            "Season": "Unknown",
            "Label": 1
        })
        client_data = pd.Series(row_dict)
    
    client_data["Weekday"] = day.weekday()
    client_data["Quarter"] = day.quarter
    client_data["Month"] = day.month
    
    # Filter the stocks to only the top 1000 (already done above) + match store country
    candidate_stocks = stocks_df[stocks_df["StoreCountry"] == client_data["ClientCountry"]]
    if candidate_stocks.empty:
        return []

    test_model = pyvw.Workspace(
        initial_regressor=model_file,
        quiet=True
    )
    
    test_instances = []
    for _, prod_row in candidate_stocks.iterrows():
        inst = client_data.to_dict()
        inst["ProductID"] = prod_row["ProductID"]
        inst["Category"] = prod_row["Category"]
        inst["FamilyLevel1"] = prod_row["FamilyLevel1"]
        inst["FamilyLevel2"] = prod_row["FamilyLevel2"]
        inst["Brand"] = prod_row["Brand"]
        inst["StoreID"] = prod_row["StoreID"]
        inst["StoreCountry"] = prod_row["StoreCountry"]
        inst["Universe"] = product_universe_map.get(prod_row["ProductID"], "Unknown")
        vw_line = convert_to_vw(pd.Series(inst))
        score = test_model.predict(vw_line)
        test_instances.append((prod_row["ProductID"], score))

    recommendations = sorted(test_instances, key=lambda x: x[1], reverse=True)[:n_recommendations]
    return recommendations

# -----------------------------
# 5. Training & Evaluation
# -----------------------------
start_day = data['TransactionDate'].min().normalize()
warmup_end = start_day + pd.Timedelta(days=30)

warmup_data = data[data['TransactionDate'] < warmup_end]
if warmup_data.empty:
    raise ValueError("No data available for warm-up.")

warmup_positives = warmup_data.assign(Label=1)
warmup_negatives = generate_negative_samples(warmup_data)
warmup_full = pd.concat([warmup_positives, warmup_negatives], ignore_index=True)
warmup_full = warmup_full.sort_values("TransactionDate")
warmup_file = "warmup_data.txt"
generate_vw_file(warmup_full, warmup_file)

model = pyvw.Workspace(
    loss_function="logistic",
    lrqfa="Client,Product,Store,Interaction",
    rank=16,
    learning_rate=0.01,
    passes=5,
    b=16,
    quiet=True,
    cache_file="vw_cache.dat"
)

with open(warmup_file, "r") as f:
    for line in tqdm(f, desc="Warmup Training"):
        model.learn(line.strip())

model.save("model_initial.vw")
current_model = "model_initial.vw"
print("Initial model trained (warm-up).")

evaluation_results = []
all_days = pd.date_range(
    start=warmup_end.normalize(),
    end=data['TransactionDate'].max().normalize(),
    freq='W'
)


# %%

for day in all_days:
    window_start = day - pd.Timedelta(days=89)
    if window_start < warmup_end:
        window_start = warmup_end

    train_subset = data[
        (data['TransactionDate'] >= window_start) &
        (data['TransactionDate'] <= day)
    ]
    if train_subset.empty:
        continue

    window_positives = train_subset.assign(Label=1)
    window_negatives = generate_negative_samples(train_subset)
    window_full = pd.concat([window_positives, window_negatives], ignore_index=True)
    window_full = window_full.sort_values("TransactionDate")

    day_train_file = f"train_{day.strftime('%Y%m%d')}.txt"
    generate_vw_file(window_full, day_train_file)

    update_model = pyvw.Workspace(
        initial_regressor=current_model,
        loss_function="logistic",
        lrqfa="Client,Product,Store,Interaction",
        learning_rate=0.01,
        passes=5,
        b=16,
        quiet=True,
        cache_file="vw_cache.dat"
    )

    with open(day_train_file, "r") as f:
        for line in tqdm(f, desc=f"Updating model for {day.date()}"):
            update_model.learn(line.strip())

    updated_model_file = f"model_{day.strftime('%Y%m%d')}.vw"
    update_model.save(updated_model_file)
    print(f"Model updated (30-day window) up to {day.date()}.")
    current_model = updated_model_file

    day_rows = data[data['TransactionDate'].dt.normalize() == day]
    if day_rows.empty:
        continue

    client_actual = day_rows.groupby("ClientID")["ProductID"].apply(set).to_dict()
    total_clients = len(client_actual)
    correct_count = 0

    print(f"Day {day.date()}: {total_clients} clients to process.")

    for idx, (client_id, bought_products) in enumerate(client_actual.items(), start=1):
        print(f" - Client {idx}/{total_clients} (ID={client_id})")
        recs = generate_recommendations_day(client_id, day, n_recommendations=5, model_file=current_model)
        rec_product_ids = [prod for prod, _ in recs]
        if set(rec_product_ids).intersection(bought_products):
            correct_count += 1

    day_accuracy = correct_count / total_clients if total_clients else np.nan
    evaluation_results.append({
        "day": day,
        "total_clients": total_clients,
        "correct": correct_count,
        "accuracy": day_accuracy
    })
    print(f"Day {day.date()} -> Accuracy: {day_accuracy:.2f}")

eval_df = pd.DataFrame(evaluation_results)
print("\nDaily evaluation results:")
print(eval_df)
overall_accuracy = eval_df["correct"].sum() / eval_df["total_clients"].sum()
print("Overall accuracy:", overall_accuracy)


