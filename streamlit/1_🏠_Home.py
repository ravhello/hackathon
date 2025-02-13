import streamlit as st
import pandas as pd
import pickle
from scipy.sparse import lil_matrix
import sys
import pickle
from models.recommender import LightFMRecommender
from utils import load_data, show_cart_sidebar, find_country, CATEGORY_EMOJIS, COUNTRY_FLAGS

# Page configuration 
st.set_page_config(
   page_title="Sport Marketplace",
   page_icon="🏃",
   layout="wide"
)

# Style CSS
st.markdown("""
<style>
.product-card {
   background-color: white;
   border: 1px solid #e0e0e0;
   border-radius: 10px;
   padding: 1rem;
   margin: 0.5rem;
   box-shadow: 0 2px 4px rgba(0,0,0,0.1);
   transition: transform 0.2s ease, box-shadow 0.2s ease;
   height: 100%;
}
.product-card:hover {
   transform: translateY(-5px);
   box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.product-title {
   font-size: 1.1rem;
   font-weight: bold;
   margin-bottom: 0.5rem;
}
.product-category {
   font-size: 0.9rem;
   color: #666;
   margin-bottom: 0.5rem;
}
.product-price {
   font-size: 1.2rem;
   font-weight: bold;
   color: #2E7D32;
   margin-bottom: 0.5rem;
}
.stock-info {
   font-size: 0.9rem;
   color: #666;
   margin-top: 0.5rem;
}
.add-to-cart-btn {
   background-color: #1976D2;
   color: white;
   border: none;
   padding: 0.5rem;
   border-radius: 5px;
   width: 100%;
   cursor: pointer;
   margin-top: 0.5rem;
}
.add-to-cart-btn:hover {
   background-color: #1565C0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_recommender():
   try:
       with open('models/recommender.pkl', 'rb') as f:
           return pickle.load(f)
   except Exception as e:
       st.error(f"Error loading model: {e}")
       return None

recommender = load_recommender()

@st.cache_data
def load_full_data():
   return pd.read_parquet("../final_df.parquet")

def create_user_features_row(user_data):
   return pd.DataFrame({
       'ClientID': [int(user_data['ClientID'])],
       'Age': [int(user_data['Age'])],
       'ClientGender': [user_data['Gender']],
       'ClientSegment': [user_data['ClientSegment']],
       'ClientCountry': [user_data['Country']]
   })

def update_user_features(recommender, new_user_df):
   recommender.user_features_df = pd.concat([recommender.user_features_df, new_user_df], ignore_index=True)

df = load_full_data()

def show_user_header():
   if st.session_state.get('logged_in'):
       st.markdown(
           f'<div style="position: fixed; top: 0.5rem; right: 1rem; z-index: 1000;">'
           f'Welcome, {st.session_state.user_data["Email"]}'
           f'</div>',
           unsafe_allow_html=True
       )

def display_product_card(product, col, idx):  # Ajout du paramètre idx
    with col:
        st.markdown(f"""
        <div class="product-card">
            <div class="product-title">{product['FamilyLevel2']}</div>
            <div class="product-category">
                {CATEGORY_EMOJIS.get(product['Category'], '')} | {product['Universe']}
            </div>
            <div class="product-price">${product['avg_price']:.2f}</div>
            <div class="stock-info">In Stock: {int(product['Quantity'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Add to Cart 🛒", key=f"add_{product['ProductID']}_{idx}"):  # Ajout de l'index à la clé
            if 'cart' not in st.session_state:
                st.session_state.cart = []
            st.session_state.cart.append({
                'id': product['ProductID'],
                'name': product['FamilyLevel2'],
                'price': product['avg_price'],
                'quantity': 1,
                'universe': product['Universe']
            })
            st.rerun()

def main():
    show_user_header()
    show_cart_sidebar()

    st.title("🏃 Sport Marketplace")
    find_country()

    if df.empty:
        st.error("Unable to load data")
        return

    # Load stock data
    stocks_df = pd.read_csv('stocks_dataset.csv')
    
    if stocks_df.empty:
        st.error("Unable to load stock data")
        return

    if st.session_state.get('logged_in'):
        user = st.session_state.user_data
        user_id = user["ClientID"]
        user_features_df_row = create_user_features_row(user)
        update_user_features(recommender, user_features_df_row)
        
        recommended_df = recommender.recommend_for_user(user_id, num_recommendations=len(recommender.product_info_df))
        st.subheader(f"Personalized recommendations for you {COUNTRY_FLAGS.get(st.session_state.country, '')}")
    else:
        user_id = 999999
        recommended_df = recommender.recommend_for_user(user_id, num_recommendations=len(recommender.product_info_df))
        st.subheader(f"Popular products in your country {COUNTRY_FLAGS.get(st.session_state.country, '')}")

    # Convert IDs to same type
    recommender.product_info_df['ProductID'] = recommender.product_info_df['ProductID'].astype(str)
    recommended_df['ProductID'] = recommended_df['ProductID'].astype(str)
    stocks_df['ProductID'] = stocks_df['ProductID'].astype(str)

    # Merge data
    products = pd.merge(
        recommended_df,
        recommender.product_info_df,
        on="ProductID",
        how="left"
    )
    
    products = pd.merge(
        products,
        stocks_df[['ProductID', 'Quantity']],
        on='ProductID',
        how='left'
    ).drop_duplicates(subset=['ProductID']) 

    # Filter out of stock products
    products = products[products['Quantity'] > 0].copy()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        category_filter = st.selectbox("Category", ["All"] + sorted(df['Category'].unique().tolist()))
    with col2:
        universe_filter = st.selectbox("Universe", ["All"] + sorted(df['Universe'].unique().tolist()))
    with col3:
        sort_by = st.selectbox("Sort by", ["Relevance", "Price: Low to High", "Price: High to Low", "Name"])

    if category_filter != "All":
        products = products[products['Category'] == category_filter]
    if universe_filter != "All":
        products = products[products['Universe'] == universe_filter]

    if sort_by == "Price: Low to High":
        products = products.sort_values("avg_price")
    elif sort_by == "Price: High to Low":
        products = products.sort_values("avg_price", ascending=False)
    elif sort_by == "Name":
        products = products.sort_values("FamilyLevel2")

    # Limit to 18 products after filtering
    products = products.head(18)

    if not products.empty:
        num_cols = 3
        for i in range(0, len(products), num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < len(products):
                    display_product_card(products.iloc[idx], cols[j], idx)  # Ajout de l'index
    else:
        st.warning("No products available with current filters.")

if __name__ == "__main__":
   main()