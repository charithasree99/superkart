# Import the necessary libraries
import joblib                              # To load the serialized model
import pandas as pd                        # To build the input DataFrame for the model
from flask import Flask, request, jsonify  # To create the API and handle requests / responses

# Initialize the Flask application
superkart_api = Flask("SuperKart Sales Forecaster")

# Load the trained pipeline (preprocessing + model) once, when the app starts
model = joblib.load("superkart_model.joblib")

# Columns expected by the model, in the order used during training
FEATURES = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]


def prepare_input(df):
    """Keep the model columns in training order and make sure the numeric columns are numbers."""
    df = df[FEATURES].copy()
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].astype(float)
    return df


# Home / health-check route
@superkart_api.get("/")
def home():
    return "Welcome to the SuperKart Sales Forecasting API!"


# Online inference: prediction for a single product-store record sent as JSON
@superkart_api.post("/v1/predict")
def predict_sales():
    record = request.get_json(silent=True)
    if not isinstance(record, dict):
        return jsonify({"error": "Send the input features as a JSON object."}), 400

    missing = [col for col in FEATURES if col not in record]
    if missing:
        return jsonify({"error": f"Missing features: {missing}"}), 400

    try:
        input_df = prepare_input(pd.DataFrame([record]))
        prediction = float(model.predict(input_df)[0])
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    return jsonify({"Predicted_Sales": round(prediction, 2)})


# Batch inference: predictions for every row of an uploaded CSV file
@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file using the form field 'file'."}), 400

    try:
        input_df = pd.read_csv(request.files["file"])
    except Exception as e:
        return jsonify({"error": f"Could not read the CSV file: {e}"}), 400

    missing = [col for col in FEATURES if col not in input_df.columns]
    if missing:
        return jsonify({"error": f"Missing columns: {missing}"}), 400

    try:
        predictions = model.predict(prepare_input(input_df))
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    # Key = row index of the CSV, value = predicted sales for that row
    output = {str(idx): round(float(pred), 2) for idx, pred in zip(input_df.index, predictions)}
    return jsonify(output)


# Run the Flask app (used only when the file is run directly; the container uses gunicorn)
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
