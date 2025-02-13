import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

CATEGORY_EMOJIS = {
    'Football': 'Football ⚽',
    'Tennis': 'Tennis 🎾',
    'Basketball': 'Basketball 🏀',
    'Badminton': 'Badminton 🏸',
    'Handball': 'Handball 🤾',
    'Rugby': 'Rugby 🏉',
    'Hockey': 'Hockey 🏑',
    'Cycling': 'Cycling 🚴',
    'Baseball': 'Baseball ⚾',
    'Beach': 'Beach 🏖️',
    'Softball': 'Softball 🥎',
    'Cricket': 'Cricket 🏏',
    'Volleyball': 'Volleyball 🏐',
    'Golf': 'Golf ⛳',
    'Running': 'Running 🏃',
    'Skiing': 'Skiing ⛷️',
}

COUNTRY_FLAGS = {
    "FRA": "🇫🇷",
    "DEU": "🇩🇪",
    "ESP": "🇪🇸",
    "ITA": "🇮🇹",
    "GBR": "🇬🇧",
    "USA": "🇺🇸",
    "AUS": "🇦🇺",
    "CAN": "🇨🇦",
    "NLD": "🇳🇱",
    "BEL": "🇧🇪",
    "CHE": "🇨🇭",
    "AUT": "🇦🇹",
    "POL": "🇵🇱",
    "SWE": "🇸🇪",
    "CHN": "🇨🇳",
    "JPN": "🇯🇵",
    "KOR": "🇰🇷",
    "IND": "🇮🇳",
    "HKG": "🇭🇰",
    "SIG": "🇸🇬"
}

def find_country(mode=None):
    if 'country' not in st.session_state:
        st.session_state.country = 'FRA'
    if mode == "reset":
        st.session_state.country = 'FRA'
        st.rerun()
    return st.session_state.country
            

@st.cache_data
def load_data():
    try:
        if "df" not in st.session_state:
            st.session_state.df = pd.read_parquet('../final_df.parquet')
        return st.session_state.df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()




def get_frequently_bought_together(df, product_ids, n_recommendations=5):
    if df.empty or not product_ids:
        return pd.DataFrame()
        
    # Group transactions by ClientID and TransactionDate to get transaction groups
    df['TransactionGroup'] = df.groupby(['ClientID', 'TransactionDate']).ngroup()
    
    # Get transactions containing any of the cart products
    relevant_transactions = df[df['ProductID'].isin(product_ids)]
    
    if relevant_transactions.empty:
        return pd.DataFrame()
    
    # Get all products from these transactions except the ones already in cart
    related_products = df[
        (df['TransactionGroup'].isin(relevant_transactions['TransactionGroup'])) &
        (~df['ProductID'].isin(product_ids))
    ]
    
    if related_products.empty:
        return pd.DataFrame()
    
    # Group by product and calculate frequency
    product_frequency = related_products.groupby('ProductID').agg({
        'Quantity_sold': 'sum',
        'avg_price': 'first',
        'Universe': 'first',
        'Category': 'first',
        'FamilyLevel1': 'first',
        'FamilyLevel2': 'first'
    }).reset_index()
    
    # Normalize frequency scores
    scaler = MinMaxScaler()
    product_frequency['frequency_score'] = scaler.fit_transform(
        product_frequency[['Quantity_sold']]
    )
    
    return product_frequency.nlargest(n_recommendations, 'frequency_score')

def show_cart_sidebar():
    with st.sidebar:
        st.title("🛒 My Cart")
        
        if 'cart' not in st.session_state:
            st.session_state.cart = []
        
        if not st.session_state.cart:
            st.write("Your cart is empty!")
            total = 0
        else:
            total = 0
            for item in st.session_state.cart:
                with st.container():
                    st.write("---")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**{item['name']}**")
                        st.write(f"${item['price']:.2f}")
                    with col2:
                        if st.button("🗑️", key=f"remove_{item['id']}"):
                            st.session_state.cart.remove(item)
                            st.rerun()
                    total += item['price']
            
            st.write("---")
            st.write(f"**Total: ${total:.2f}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear", key="clear_cart"):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Checkout", key="checkout"):
                    if not st.session_state.get('logged_in', False):
                        st.error("Please login first")
                    else:
                        st.switch_page("pages/2_🛒_Cart.py")
