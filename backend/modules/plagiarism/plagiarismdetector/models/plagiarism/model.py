import joblib
import os

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "plagiarism_logreg_model.pkl")

pipeline = joblib.load(MODEL_PATH)


