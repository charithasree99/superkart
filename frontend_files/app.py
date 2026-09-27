import io
import os

import pandas as pd
import requests
import streamlit as st

# Address of the Flask backend. Inside the Docker network the backend container is reachable by its name.
BACKEND_URL = os.getenv("BACKEND_URL", "http://superkart-backend:7860")

# Product_Type -> (Product_Id_char, Product_Type_Category), as derived from the training data
PRODUCT_TYPES = {
    "Baking Goods": ("FD", "Non Perishables"),
    "Breads": ("FD", "Perishables"),
    "Breakfast": ("FD", "Perishables"),
    "Canned": ("FD", "Non Perishables"),
    "Dairy": ("FD", "Perishables"),
    "Frozen Foods": ("FD", "Non Perishables"),
    "Fruits and Vegetables": ("FD", "Perishables"),
    "Hard Drinks": ("DR", "Non Perishables"),
    "Health and Hygiene": ("NC", "Non Perishables"),
    "Household": ("NC", "Non Perishables"),
    "Meat": ("FD", "Perishables"),
    "Others": ("NC", "Non Perishables"),
    "Seafood": ("FD", "Perishables"),
    "Snack Foods": ("FD", "Non Perishables"),
    "Soft Drinks": ("DR", "Non Perishables"),
    "Starchy Foods": ("FD", "Non Perishables"),
}

st.set_page_config(page_title="SuperKart Sales Forecaster", page_icon="🛒", layout="centered")
st.title("SuperKart Sales Forecaster")
st.write("Forecast the total sales revenue of a product in a store, for a single product or for a whole CSV file.")

tab_single, tab_batch = st.tabs(["Single prediction", "Batch prediction"])

# ------------------------------------------------------------------ online (single) prediction
with tab_single:
    with st.form("single_prediction"):
        st.subheader("Product details")
        col1, col2 = st.columns(2)
        with col1:
            product_type = st.selectbox("Product Type", list(PRODUCT_TYPES.keys()), index=5)
            product_sugar = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
            product_weight = st.number_input("Product Weight", min_value=0.0, max_value=100.0, value=12.66, step=0.01)
        with col2:
            product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=117.08, step=0.01)
            allocated_area = st.number_input("Product Allocated Area (ratio of display area)", min_value=0.0,
                                             max_value=1.0, value=0.027, step=0.001, format="%.3f")

        st.subheader("Store details")
        col3, col4 = st.columns(2)
        with col3:
            store_type = st.selectbox("Store Type", ["Supermarket Type1", "Supermarket Type2",
                                                     "Departmental Store", "Food Mart"], index=1)
            store_size = st.selectbox("Store Size", ["Small", "Medium", "High"], index=1)
        with col4:
            city_type = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"], index=1)
            store_age = st.number_input("Store Age (years)", min_value=0, max_value=100, value=16, step=1)

        submitted = st.form_submit_button("Predict sales")

    if submitted:
        product_id_char, product_type_category = PRODUCT_TYPES[product_type]
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar,
            "Product_Allocated_Area": allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": city_type,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": int(store_age),
            "Product_Type_Category": product_type_category,
        }
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if response.status_code == 200:
                st.success(f"Predicted Product_Store_Sales_Total: {response.json()['Predicted_Sales']:,.2f}")
            else:
                st.error(f"API error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the prediction API at {BACKEND_URL}: {e}")
        with st.expander("Payload sent to the API"):
            st.json(payload)

# ------------------------------------------------------------------ batch prediction
with tab_batch:
    st.write("Upload a CSV file with the columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
             "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, Store_Age_Years, "
             "Product_Type_Category.")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        input_df = pd.read_csv(io.BytesIO(file_bytes))
        st.write("Preview of the uploaded data:")
        st.dataframe(input_df.head())

        if st.button("Predict batch"):
            try:
                response = requests.post(f"{BACKEND_URL}/v1/predictbatch",
                                         files={"file": (uploaded_file.name, file_bytes, "text/csv")}, timeout=120)
                if response.status_code == 200:
                    predictions = response.json()
                    result_df = input_df.copy()
                    result_df["Predicted_Sales"] = [predictions[str(i)] for i in input_df.index]
                    st.success(f"Predictions generated for {len(result_df)} rows.")
                    st.dataframe(result_df)
                    st.download_button("Download predictions as CSV", result_df.to_csv(index=False).encode("utf-8"),
                                       file_name="superkart_predictions.csv", mime="text/csv")
                else:
                    st.error(f"API error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the prediction API at {BACKEND_URL}: {e}")
