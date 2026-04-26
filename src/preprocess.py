import os
import numpy as np
from skimage.io import imread
from skimage.transform import resize
from sklearn.model_selection import train_test_split
import configparser
import sys
import traceback

from logger import Logger

TEST_SIZE = 0.2
SHOW_LOG = True


class DataMaker():

    def __init__(self) -> None:
        '''Создаёт логгер, определяет пути к папкам и файлам'''
        logger = Logger(SHOW_LOG)
        self.config = configparser.ConfigParser()
        self.log = logger.get_logger(__name__)
        self.project_path = os.path.join(os.getcwd(), "data")
        self.data_dir = os.path.join(self.project_path, "imagenet_tiny")  # ← папка с картинками
        self.X_train_path = os.path.join(self.project_path, "X_train.npy")
        self.y_train_path = os.path.join(self.project_path, "y_train.npy")
        self.X_test_path = os.path.join(self.project_path, "X_test.npy")
        self.y_test_path = os.path.join(self.project_path, "y_test.npy")
        self.log.info("DataMaker for ImageNet is ready")

    def load_images_from_folder(self, folder_path: str, class_id: int):
        """Загружает все картинки из папки класса (без вложенной папки images)"""
        X = []
        y = []
    
        if not os.path.exists(folder_path):
            self.log.error(f"Папка не найдена: {folder_path}")
            return X, y
    
        for img_file in os.listdir(folder_path):
            if img_file.lower().endswith(('.jpeg', '.jpg')):
                img_path = os.path.join(folder_path, img_file)
                try:
                    img = imread(img_path)
                    img = resize(img, (28, 28))
                    X.append(img.flatten())
                    y.append(class_id)
                except Exception as e:
                    self.log.error(f"Ошибка загрузки {img_path}: {e}")
    
        self.log.info(f"  Загружено {len(X)} картинок для класса {class_id}")
        return X, y

    def get_data(self) -> bool:
        """Проходит по всем классам в imagenet_tiny, собирает все картинки, сохраняет в X_train.npy и y_train.npy"""
        X_all = []
        y_all = []
        
        for class_id, class_name in enumerate(os.listdir(self.data_dir)):
            class_path = os.path.join(self.data_dir, class_name)
            self.log.info(f"Загрузка класса {class_name} (id={class_id})")
            
            X_class, y_class = self.load_images_from_folder(class_path, class_id)
            X_all.extend(X_class)
            y_all.extend(y_class)
        
        if len(X_all) == 0:
            self.log.error("Не загружено ни одной картинки")
            return False
        
        # Сохраняем как .npy
        np.save(self.X_train_path, np.array(X_all))
        np.save(self.y_train_path, np.array(y_all))
        
        self.log.info(f"Всего загружено {len(X_all)} картинок")
        self.log.info(f"Размер одного изображения: {len(X_all[0])} пикселей")
        
        self.config["DATA"] = {
            'X_data': self.X_train_path,
            'y_data': self.y_train_path
        }
        
        return os.path.isfile(self.X_train_path) and os.path.isfile(self.y_train_path)

    def split_data(self, test_size=TEST_SIZE) -> bool:
        """Делит данные на обучающую (80%) и тестовую (20%), сохраняет отдельно, записывает пути в config.ini"""
        self.get_data()
        
        try:
            X = np.load(self.X_train_path)
            y = np.load(self.y_train_path)
        except FileNotFoundError:
            self.log.error(traceback.format_exc())
            sys.exit(1)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        np.save(self.X_train_path, X_train)
        np.save(self.y_train_path, y_train)
        np.save(self.X_test_path, X_test)
        np.save(self.y_test_path, y_test)
        
        self.config["SPLIT_DATA"] = {
            'X_train': self.X_train_path,
            'y_train': self.y_train_path,
            'X_test': self.X_test_path,
            'y_test': self.y_test_path
        }
        
        self.log.info(f"Train data: {X_train.shape}, Test data: {X_test.shape}")
        
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
        
        return os.path.isfile(self.X_train_path) and \
               os.path.isfile(self.y_train_path) and \
               os.path.isfile(self.X_test_path) and \
               os.path.isfile(self.y_test_path)


if __name__ == "__main__":
    data_maker = DataMaker()
    data_maker.split_data()
