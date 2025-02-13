# %%
import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# =========================================================
# 1. Data Loading & Preprocessing
#    (Same as in your VW code)
# =========================================================

data = pd.read_parquet("final_df.parquet")
clients_df = pd.read_csv("clients_dataset.csv")
stocks_df = pd.read_csv("stocks_dataset.csv")

# Sort data by date
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

# Undersample top 1000 sold products (like VW code)
top_1000_products = (
    data.groupby('ProductID')['Quantity_sold']
    .sum().sort_values(ascending=False)
    .head(1000).index
)
top_1000_products = set(top_1000_products)
data = data[data['ProductID'].isin(top_1000_products)].copy()
stocks_df = stocks_df[stocks_df['ProductID'].isin(top_1000_products)].copy()

# Map for Universe
product_universe_map = data.groupby("ProductID")["Universe"].last().to_dict()

print(f"After top-1000 undersampling:\n  - data has {len(data)} rows\n  - stocks_df has {len(stocks_df)} rows")

# =========================================================
# 2. Negative Sampling Utility
# =========================================================

def generate_negative_samples(df, n_neg=10):
    """
    Generate negative samples for implicit feedback data,
    picking up to n_neg products not bought by the user.
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

# =========================================================
# 3. PyTorch Dataset & DataLoader
# =========================================================

class FFMData(Dataset):
    """
    A custom Dataset to hold each row's features:
      - Each row is (categorical_field_values, numeric_field_values, label)
    """

    def __init__(self, df, field_index_maps, numeric_cols):
        """
        Args:
          df: DataFrame with labeled rows
          field_index_maps: dict of {field_name -> { value -> index }} 
                           for categorical encoding
          numeric_cols: list of numeric column names
        """
        self.df = df.reset_index(drop=True)
        self.field_index_maps = field_index_maps
        self.numeric_cols = numeric_cols

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # Construct categorical indices per field
        x_cat = {}
        for field, value_map in self.field_index_maps.items():
            val = row.get(field, "Unknown")
            index_val = value_map.get(val, value_map.get("__UNK__", 0))
            x_cat[field] = index_val
        
        # Numeric features as a vector
        x_num = row[self.numeric_cols].values.astype(np.float32)

        label = np.float32(row["Label"])
        return x_cat, x_num, label

def build_field_index_maps(df, cat_fields, special_unknown="__UNK__"):
    """
    Build a dictionary: field -> { value -> index }, for each categorical field.
    """
    field_index_maps = {}
    for field in cat_fields:
        unique_vals = df[field].dropna().unique().tolist()
        val_to_idx = {}
        for i, val in enumerate(unique_vals):
            val_to_idx[val] = i
        # Optionally reserve an index for unknown
        val_to_idx[special_unknown] = len(val_to_idx)
        field_index_maps[field] = val_to_idx
    return field_index_maps

# -----------------------
# Custom collate_fn for single-sample
# -----------------------
def single_sample_collate(batch):
    """
    Given a list of (x_cat, x_num, y) of length BATCH_SIZE,
    return them for a single-sample approach if BATCH_SIZE=1,
    or a small loop for multiple samples.
    """
    # In our code, we set batch_size=1, so 'batch' is [(x_cat, x_num, y)] of length 1
    x_cat, x_num, y = batch[0]
    return x_cat, x_num, y


# =========================================================
# 4. Field-Aware Factorization Machine (Simplified)
# =========================================================

class FieldAwareFM(nn.Module):
    def __init__(self, 
                 field_index_maps, 
                 numeric_cols, 
                 embed_dim=16):
        """
        A simplified FFM: 
        - One embedding table per field
        - A linear layer for numeric features
        - Summation of pairwise interactions in forward pass
        """
        super().__init__()
        self.field_names = sorted(field_index_maps.keys())  # e.g. ["ClientID", "ClientGender", ...]
        self.numeric_cols = numeric_cols

        # Build an embedding for each field
        self.embeddings = nn.ModuleDict()
        for field in self.field_names:
            vocab_size = len(field_index_maps[field])
            self.embeddings[field] = nn.Embedding(
                num_embeddings=vocab_size, 
                embedding_dim=embed_dim
            )
        
        # A simple linear transform for numeric features:
        self.num_linear = nn.Linear(len(numeric_cols), embed_dim, bias=False)

        # Optional global bias
        self.global_bias = nn.Parameter(torch.zeros(1))
        
    def forward(self, x_cat, x_num):
        """
        x_cat: dict of { field: index_in_that_field }
        x_num: numeric vector (FloatTensor of shape [n_num])
        """
        # Convert x_num to [1, n_num]
        x_num_t = x_num.unsqueeze(0)  # shape [1, n_num]
        emb_num = self.num_linear(x_num_t)  # shape [1, embed_dim]

        # For each field, get embedding
        embs = []
        for field in self.field_names:
            idx = torch.tensor([x_cat[field]], dtype=torch.long, device=x_num.device)  # shape [1]
            emb = self.embeddings[field](idx)  # shape [1, embed_dim]
            embs.append(emb)
        embs = torch.cat(embs, dim=0)  # shape [num_fields, embed_dim]

        # Summation for linear part
        linear_part = embs.sum(dim=0) + emb_num.squeeze(0)  # shape [embed_dim]

        # Pairwise interactions among embeddings
        interaction_sum = torch.zeros(1, device=x_num.device)
        n_fields = embs.size(0)
        for i in range(n_fields):
            for j in range(i+1, n_fields):
                interaction_sum += (embs[i] * embs[j]).sum()

        # Combine everything
        linear_scalar = linear_part.sum()  # shape []
        logit = self.global_bias + linear_scalar + interaction_sum
        return logit

# =========================================================
# 5. Training and Evaluation Utilities
# =========================================================

def train_ffm_model(model, loader, optimizer, device="cpu", epochs=1):
    """
    Training loop for the daily mini-batch (batch_size=1).
    """
    model.to(device)
    criterion = nn.BCEWithLogitsLoss()  # logistic
    model.train()
    for _ in range(epochs):
        for x_cat, x_num, y in loader:
            # x_cat (dict), x_num (tensor), y (float)
            x_num = x_num.to(device)
            y = y.to(device)

            logit = model(x_cat, x_num)
            loss = criterion(logit.unsqueeze(0), y.unsqueeze(0))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()


def inference_ffm_model(model, client_row, candidate_stocks, product_universe_map, field_index_maps, numeric_cols, device="cpu"):
    """
    For a single client on a particular day, rank all candidate products.
    Return top 5 (similar to your VW code).
    """
    model.to(device)
    model.eval()

    cdict = client_row.to_dict()
    scored = []

    for _, prod_row in candidate_stocks.iterrows():
        row_dict = {**cdict}
        row_dict["ProductID"] = prod_row["ProductID"]
        row_dict["Category"] = prod_row["Category"]
        row_dict["FamilyLevel1"] = prod_row["FamilyLevel1"]
        row_dict["FamilyLevel2"] = prod_row["FamilyLevel2"]
        row_dict["Brand"] = prod_row["Brand"]
        row_dict["StoreID"] = prod_row["StoreID"]
        row_dict["StoreCountry"] = prod_row["StoreCountry"]
        row_dict["Universe"] = product_universe_map.get(prod_row["ProductID"], "Unknown")
        row_dict["Label"] = 0  # dummy

        # Single-sample dataset
        df_temp = pd.DataFrame([row_dict])
        ds_temp = FFMData(df_temp, field_index_maps, numeric_cols)
        x_cat, x_num, _ = ds_temp[0]
        x_num = torch.tensor(x_num, dtype=torch.float, device=device)

        with torch.no_grad():
            logit = model(x_cat, x_num)
            score = torch.sigmoid(logit).item()
        scored.append((prod_row["ProductID"], score))

    # Sort descending by score
    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    return scored[:5]

# =========================================================
# 6. Prepare Categorical/Numeric Columns
# =========================================================

cat_fields = [
    "ClientID", "ClientGender", "ClientSegment", "ClientCountry", "OptEmail", "OptPhone",
    "ProductID", "Category", "FamilyLevel1", "FamilyLevel2", "Brand", "StoreID", "StoreCountry",
    "Universe",  # We'll store "Universe" as a categorical field
    "Weekday", "Quarter", "Season"
]
numeric_cols = [
    "Age", "product_avg_price_order", "avg_price", "DaysSinceLastTransaction",
    "CumulativeSpent", "CumulativeQuantity", "PercentageMaleProductsSoFar",
    "UniqueProductsSoFar", "AverageAmountPerTransactionSoFar", "AverageFrequencySoFar",
    "AveragePrice", "Frequency_30", "Monetary_30", "Recency_30",
    "Frequency_60", "Monetary_60", "Recency_60",
    "Frequency_90", "Monetary_90", "Recency_90",
    "Quantity_sold", "SalesNetAmountEuro", "Month"
]

all_cat_df = pd.concat([data, stocks_df], ignore_index=True)
for c in cat_fields:
    if c not in all_cat_df.columns:
        all_cat_df[c] = "Unknown"

field_index_maps = build_field_index_maps(all_cat_df, cat_fields)

# =========================================================
# 7. Initialize Model
# =========================================================

embed_dim = 16
device = "cpu"  # or "cuda" if you have a GPU
model_ffm = FieldAwareFM(field_index_maps, numeric_cols, embed_dim=embed_dim).to(device)
optimizer = optim.Adam(model_ffm.parameters(), lr=0.01)

# Warmup period
start_day = data['TransactionDate'].min().normalize()
warmup_end = start_day + pd.Timedelta(days=30)
warmup_data = data[data['TransactionDate'] < warmup_end]
if warmup_data.empty:
    raise ValueError("No data available for warm-up.")

warmup_positives = warmup_data.assign(Label=1)
warmup_negatives = generate_negative_samples(warmup_data)
warmup_full = pd.concat([warmup_positives, warmup_negatives], ignore_index=True)
warmup_full = warmup_full.sort_values("TransactionDate")
print(f"Warmup samples: {len(warmup_full)}")

warmup_dataset = FFMData(
    df=warmup_full, 
    field_index_maps=field_index_maps, 
    numeric_cols=numeric_cols
)
warmup_loader = DataLoader(
    warmup_dataset, 
    batch_size=1, 
    shuffle=True, 
    collate_fn=single_sample_collate
)

print("Starting Warmup Training...")
for epoch in range(5):
    train_ffm_model(model_ffm, warmup_loader, optimizer, device=device, epochs=1)
print("Warmup done.")

os.makedirs("models", exist_ok=True)
torch.save(model_ffm.state_dict(), "models/model_initial.pt")

# =========================================================
# 8. Day-by-Day Sliding Window + Evaluation
# =========================================================

evaluation_results = []
all_days = pd.date_range(
    start=warmup_end.normalize(),
    end=data['TransactionDate'].max().normalize(),
    freq='W'
)

current_model_file = "models/model_initial.pt"

for day in all_days:
    window_start = day - pd.Timedelta(days=159)
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

    # Load current model
    model_ffm.load_state_dict(torch.load(current_model_file))
    model_ffm.to(device)

    window_dataset = FFMData(
        df=window_full,
        field_index_maps=field_index_maps,
        numeric_cols=numeric_cols
    )
    window_loader = DataLoader(
        window_dataset, 
        batch_size=1, 
        shuffle=True, 
        collate_fn=single_sample_collate
    )

    print(f"\n[INFO] Updating model for day {day.date()}, {len(window_full)} samples")
    for epoch in range(5):
        train_ffm_model(model_ffm, window_loader, optimizer, device=device, epochs=1)

    updated_model_file = f"models/model_{day.strftime('%Y%m%d')}.pt"
    torch.save(model_ffm.state_dict(), updated_model_file)
    current_model_file = updated_model_file

    # --- EVALUATION ---
    day_rows = data[data['TransactionDate'].dt.normalize() == day]
    if day_rows.empty:
        continue
    
    client_actual = day_rows.groupby("ClientID")["ProductID"].apply(set).to_dict()
    total_clients = len(client_actual)
    correct_count = 0

    print(f"Day {day.date()}: {total_clients} clients to process.")
    model_ffm.eval()

    for idx, (client_id, bought_products) in enumerate(client_actual.items(), start=1):
        subset_client = data[(data["ClientID"] == client_id) & (data["TransactionDate"] <= day)]
        if not subset_client.empty:
            client_data = subset_client.iloc[-1].copy()
            client_data["Label"] = 1
        else:
            client_profile = clients_df[clients_df["ClientID"] == client_id]
            if client_profile.empty:
                continue
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

        cand_stocks = stocks_df[stocks_df["StoreCountry"] == client_data["ClientCountry"]]
        if cand_stocks.empty:
            continue
        
        recs = inference_ffm_model(
            model_ffm, 
            client_data, 
            cand_stocks, 
            product_universe_map,
            field_index_maps,
            numeric_cols,
            device=device
        )
        rec_product_ids = [p for (p, score) in recs]
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


