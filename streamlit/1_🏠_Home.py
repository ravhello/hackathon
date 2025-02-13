###################### Modernizing the UI with card instead of list ######################



import streamlit as st
import pandas as pd
from utils import load_data, show_cart_sidebar, find_country, CATEGORY_EMOJIS, COUNTRY_FLAGS
from sklearn.preprocessing import MinMaxScaler
from models.recommender import Recommender, get_personalized_recommendations, get_generic_recommendations

# Page config
st.set_page_config(
    page_title="Sport Marketplace",
    page_icon="🏃",
    layout="wide"
)

# Add custom CSS for card styling
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

div[data-testid="stHorizontalBlock"] {
    gap: 1rem;
    padding: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

def show_user_header():
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.markdown(
            f'<div style="position: fixed; top: 0.5rem; right: 1rem; z-index: 1000;">'
            f'Welcome, {st.session_state.user_data["Email"]}'
            f'</div>',
            unsafe_allow_html=True
        )

def display_product_card(product, col):
    with col:
        st.markdown(f"""
        <div class="product-card">
            <div class="product-title">{product['FamilyLevel2']}</div>
            <div class="product-category">
                {CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}
            </div>
            <div class="product-price">${product['avg_price']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Add to Cart 🛒", key=f"add_{product['ProductID']}"):
            if 'cart' not in st.session_state:
                st.session_state.cart = []
            st.session_state.cart.append({
                'id': product['ProductID'],
                'name': product['FamilyLevel2'],
                'price': product['avg_price']
            })
            st.rerun()

def main():
    show_user_header()
    show_cart_sidebar()
    
    st.title("🏃 Sport Marketplace")
    
    # Load data
    find_country()
    df = load_data()
    
    if df.empty:
        st.error("Unable to load data")
        return
    
    # Get recommendations
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        user = st.session_state.user_data
        products = get_personalized_recommendations(df, user)
        st.subheader(f"Personalized Recommendations for You {COUNTRY_FLAGS[st.session_state.country]}")
    else:
        products = get_generic_recommendations(df)
        st.subheader(f"Popular Products in your country {COUNTRY_FLAGS[st.session_state.country]}")
    
    # Display products in a grid
    if not products.empty:
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Category", ["All"] + list(df['Category'].unique()))
        with col2:
            universe = st.selectbox("Universe", ["All"] + list(df['Universe'].unique()))
        with col3:
            sort_by = st.selectbox("Sort by", ["Price: Low to High", "Price: High to Low", "Name"])
        
        # Filter products
        if category != "All":
            products = products[products['Category'] == category]
        if universe != "All":
            products = products[products['Universe'] == universe]
            
        # Sort products
        if sort_by == "Price: Low to High":
            products = products.sort_values('avg_price')
        elif sort_by == "Price: High to Low":
            products = products.sort_values('avg_price', ascending=False)
        elif sort_by == "Name":
            products = products.sort_values('FamilyLevel2')
        
        # Create product grid
        num_cols = 3
        for i in range(0, len(products), num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < len(products):
                    display_product_card(products.iloc[idx], cols[j])
    else:
        st.warning("No products available at the moment.")

if __name__ == "__main__":
    main()





#################### Adding name on top right corner ####################


# import streamlit as st
# import pandas as pd
# from utils import load_data, show_cart_sidebar, find_country, CATEGORY_EMOJIS, COUNTRY_FLAGS
# from sklearn.preprocessing import MinMaxScaler
# from models.recommender import Recommender, get_personalized_recommendations, get_generic_recommendations

# # Page config
# st.set_page_config(
#     page_title="Sport Marketplace",
#     page_icon="🏃",
#     layout="wide"
# )

# def show_user_header():
#     if 'logged_in' in st.session_state and st.session_state.logged_in:
#         # Using markdown to create a right-aligned text
#         st.markdown(
#             f'<div style="position: fixed; top: 0.5rem; right: 1rem; z-index: 1000;">'
#             f'Welcome, {st.session_state.user_data["Email"]}'
#             f'</div>',
#             unsafe_allow_html=True
#         )

# def main():
#     show_user_header()  # Add this line to show user info
#     show_cart_sidebar()
    
#     st.title("🏃 Sport Marketplace")
    
#     # Load data
#     find_country()

#     df = load_data()
    
#     if df.empty:
#         st.error("Unable to load data")
#         return
    
#     if 'logged_in' in st.session_state and st.session_state.logged_in:
#         user = st.session_state.user_data
#         st.write(f"Welcome {user['Email']}!")
#         products = get_personalized_recommendations(df, user)
#         st.subheader(f"Personalized Recommendations for You {COUNTRY_FLAGS[st.session_state.country]}")
#     else:
#         products = get_generic_recommendations(df)
#         st.subheader(f"Popular Products in your country {COUNTRY_FLAGS[st.session_state.country]}")
    
#     # Display products in a grid
#     if not products.empty:
#         # Create a container for all products
#         for idx, (_, product) in enumerate(products.iterrows()):
#             if idx % 3 == 0:
#                 cols = st.columns(3)
            
#             with cols[idx % 3]:
#                 st.write("---")
#                 st.write(f"**{product['FamilyLevel2']}**")
#                 st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
#                 st.write(f"Price: ${product['avg_price']:.2f}")
                
#                 if st.button("🛒", key=f"add_{product['ProductID']}"):
#                     if 'cart' not in st.session_state:
#                         st.session_state.cart = []
#                     st.session_state.cart.append({
#                         'id': product['ProductID'],
#                         'name': product['FamilyLevel2'],
#                         'price': product['avg_price']
#                     })
#                     st.rerun()
#     else:
#         st.warning("No products available at the moment.")

# if __name__ == "__main__":
#     main()



#################### without name on top right corner ####################


# import streamlit as st
# import pandas as pd
# from utils import load_data, show_cart_sidebar, find_country, CATEGORY_EMOJIS, COUNTRY_FLAGS
# from sklearn.preprocessing import MinMaxScaler
# from models.recommender import Recommender, get_personalized_recommendations, get_generic_recommendations

# # Page config
# st.set_page_config(
#     page_title="Sport Marketplace",
#     page_icon="🏃",
#     layout="wide"
# )

# def main():
#     show_cart_sidebar()
    
#     st.title("🏃 Sport Marketplace")
    
#     # Load data
#     find_country()

#     df = load_data()
    
#     if df.empty:
#         st.error("Unable to load data")
#         return
    
#     if 'logged_in' in st.session_state and st.session_state.logged_in:
#         user = st.session_state.user_data
#         st.write(f"Welcome {user['Email']}!")
#         products = get_personalized_recommendations(df, user)
#         st.subheader(f"Personalized Recommendations for You {COUNTRY_FLAGS[st.session_state.country]}")
#     else:
#         products = get_generic_recommendations(df)
#         st.subheader(f"Popular Products in your country {COUNTRY_FLAGS[st.session_state.country]}")
    
#     # Display products in a grid
#     if not products.empty:
#         # Create a container for all products
#         for idx, (_, product) in enumerate(products.iterrows()):
#             if idx % 3 == 0:
#                 cols = st.columns(3)
            
#             with cols[idx % 3]:
#                 st.write("---")
#                 st.write(f"**{product['FamilyLevel2']}**")
#                 st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
#                 st.write(f"Price: ${product['avg_price']:.2f}")
                
#                 if st.button("🛒", key=f"add_{product['ProductID']}"):
#                     if 'cart' not in st.session_state:
#                         st.session_state.cart = []
#                     st.session_state.cart.append({
#                         'id': product['ProductID'],
#                         'name': product['FamilyLevel2'],
#                         'price': product['avg_price']
#                     })
#                     st.rerun()
#     else:
#         st.warning("No products available at the moment.")

# if __name__ == "__main__":
#     main()
