import argparse
import configparser
import os
import numpy as np
import pickle
import sys
import traceback

from logger import Logger

SHOW_LOG = True


class Predictor():

    def __init__(self) -> None:
        logger = Logger(SHOW_LOG)
        self.config = configparser.ConfigParser()
        self.log = logger.get_logger(__name__)
        self.config.read("config.ini")
        
        self.parser = argparse.ArgumentParser(description="Predictor")
        
        # Загружаем тестовые данные
        self.X_test = np.load(self.config["SPLIT_DATA"]["x_test"])
        self.y_test = np.load(self.config["SPLIT_DATA"]["y_test"])
        
        self.log.info(f"Predictor is ready. Test data shape: {self.X_test.shape}")

    def predict(self) -> bool:
        args = self.parser.parse_args()
        
        # Загружаем модель (просто из секции MODEL)
        try:
            model_path = self.config["MODEL"]["model_path"]
            classifier = pickle.load(open(model_path, "rb"))
            self.log.info(f"Model loaded from {model_path}")
        except FileNotFoundError:
            self.log.error(traceback.format_exc())
            sys.exit(1)
        
        # Проверяем точность
        try:
            score = classifier.score(self.X_test, self.y_test)
            print(f'Model accuracy: {score:.4f}')
            self.log.info(f'Model passed test with accuracy {score:.4f}')
        except Exception:
            self.log.error(traceback.format_exc())
            sys.exit(1)
        
        return True


if __name__ == "__main__":
    predictor = Predictor()
    predictor.predict()