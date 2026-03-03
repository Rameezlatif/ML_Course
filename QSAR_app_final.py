
import streamlit as st
import pandas as pd
import subprocess
import os
import base64
import pickle

# =============================
# Page settings
# =============================
st.set_page_config(page_title="QSAR Predictor", layout="wide")

st.title("QSAR Bioactivity Predictor")
st.write("Upload SMILES file to predict bioactivity (pIC50)")


# =============================
# File download function
# =============================
def filedownload(df):

    csv = df.to_csv(index=False)

    b64 = base64.b64encode(csv.encode()).decode()

    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Prediction</a>'

    return href


# =============================
# Delete old files
# =============================
def clean_files():

    files = [
        "molecule.smi",
        "descriptors_output.csv"
    ]

    for file in files:
        if os.path.exists(file):
            os.remove(file)


# =============================
# Descriptor calculation
# =============================
def desc_calc():

    command = [
        "java",
        "-Xms2G",
        "-Xmx2G",
        "-Djava.awt.headless=true",
        "-jar",
        "PaDEL-Descriptor/PaDEL-Descriptor.jar",
        "-removesalt",
        "-standardizenitro",
        "-fingerprints",
        "-descriptortypes",
        "PaDEL-Descriptor/PubchemFingerprinter.xml",
        "-dir",
        ".",
        "-file",
        "descriptors_output.csv"
    ]

    subprocess.run(command)


# =============================
# Build model and predict
# =============================
def build_model(desc, smiles, names):

    model = pickle.load(open("NLRP3_model.pkl", "rb"))

    prediction = model.predict(desc)

    result = pd.DataFrame({
        "Molecule Name": names,
        "SMILES": smiles,
        "pIC50": prediction
    })

    st.subheader("Prediction Results")

    st.write(result)

    st.markdown(filedownload(result), unsafe_allow_html=True)


# =============================
# Upload file
# =============================
uploaded_file = st.file_uploader("Upload SMILES file", type=["txt", "smi", "csv"])


# =============================
# Main logic
# =============================
if uploaded_file is not None:

    clean_files()

    load_data = pd.read_csv(uploaded_file, sep="\s+", header=None)

    smiles = load_data[0]

    names = load_data[1]

    st.write("Input Data")

    st.write(load_data)

    # Save SMILES file for PaDEL
    load_data.to_csv("molecule.smi", sep="\t", header=False, index=False)


    with st.spinner("Calculating descriptors..."):

        desc_calc()


    desc = pd.read_csv("descriptors_output.csv")


    # Load descriptor list
    # Load descriptor list from CSV instead of PKL
    descriptor_df = pd.read_csv("descriptor_list.csv")

    if descriptor_df.shape[1] == 1:
        descriptor_list = descriptor_df.iloc[:,0].tolist()
    else:
        descriptor_list = descriptor_df.columns.tolist()


    # Align descriptors
    desc_subset = desc.reindex(columns=descriptor_list, fill_value=0)


    with st.spinner("Predicting..."):

        build_model(desc_subset, smiles, names)


# =============================
# Instructions
# =============================
st.sidebar.header("Instructions")

st.sidebar.write("""
1. Upload SMILES file

Format:

SMILES NAME

Example:

CCO Mol1
CCC Mol2

2. Wait for prediction

3. Download results
""")


# =============================
# Check Java
# =============================
if st.sidebar.button("Check Java"):

    result = subprocess.run(["java", "-version"], capture_output=True, text=True)

    st.sidebar.text(result.stderr)


# =============================
# End
# =============================
