import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import configparser
from logger import Logger

SHOW_LOG = True


class ModelTrainer:

    def __init__(self) -> None:
        logger = Logger(SHOW_LOG)
        self.config = configparser.ConfigParser()
        self.log = logger.get_logger(__name__)
        self.config.read('config.ini')
        
        self.project_path = os.path.join(os.getcwd(), "data")
        self.X_train_path = os.path.join(self.project_path, "X_train.npy")
        self.y_train_path = os.path.join(self.project_path, "y_train.npy")
        self.X_test_path = os.path.join(self.project_path, "X_test.npy")
        self.y_test_path = os.path.join(self.project_path, "y_test.npy")
        self.model_path = os.path.join(os.getcwd(), "models", "model.pkl")
        
        self.log.info("ModelTrainer for ImageNet is ready")

    def load_data(self):
        """Загружает данные из .npy файлов"""
        self.log.info("Загрузка данных...")
        X_train = np.load(self.X_train_path)
        y_train = np.load(self.y_train_path)
        X_test = np.load(self.X_test_path)
        y_test = np.load(self.y_test_path)
        
        self.log.info(f"Train: {X_train.shape}, Test: {X_test.shape}")
        return X_train, y_train, X_test, y_test

    def train_model(self):
        """Обучает RandomForest и сохраняет модель"""
        X_train, y_train, X_test, y_test = self.load_data()
        
        self.log.info("Обучение RandomForestClassifier...")
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        accuracy = model.score(X_test, y_test)
        self.log.info(f"Точность модели: {accuracy:.3f}")
        
        os.makedirs('models', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)
        
        self.log.info(f"Модель сохранена: {self.model_path}")
        
        # Сохраняем точность в config.ini
        if not self.config.has_section('MODEL'):
            self.config.add_section('MODEL')
        self.config.set('MODEL', 'accuracy', str(accuracy))
        self.config.set('MODEL', 'model_path', self.model_path)
        
        with open('config.ini', 'w') as f:
            self.config.write(f)
        
        return accuracy


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_model()