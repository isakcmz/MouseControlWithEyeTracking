import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib, os

def main():
    data_path = "../data/raw/calibration.csv"
    model_path = "../data/models/calibration_model.pkl"

    if not os.path.exists(data_path):
        print(f"❌ Kalibrasyon verisi bulunamadi: {data_path}")
        return

    # Veriyi yükle
    df = pd.read_csv(data_path)
    X = df[["eye_x","eye_y"]]
    y = df[["screen_x","screen_y"]]

    # Modeli eğit
    model = LinearRegression()
    model.fit(X, y)

    # Modeli kaydet
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

    print(f"✅ Model egitildi ve kaydedildi: {model_path}")
    print(f"R^2 skoru: {model.score(X, y):.4f}")

if __name__ == "__main__":
    main()
