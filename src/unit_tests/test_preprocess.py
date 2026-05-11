import configparser
import os
import unittest
import numpy as np
import sys

sys.path.insert(1, os.path.join(os.getcwd(), "src"))

from preprocess import DataMaker

config = configparser.ConfigParser()
config.read("config.ini")


class TestDataMaker(unittest.TestCase):
    """
    Тесты для DataMaker (предобработка данных ImageNet)
    """

    def setUp(self) -> None:
        """Инициализация перед каждым тестом"""
        self.data_maker = DataMaker()
        print(f"\n[SETUP] DataMaker создан")

    def tearDown(self) -> None:
        """Очистка после каждого теста"""
        print("[TEARDOWN] Тест завершён")

    # ========== ТЕСТЫ ДЛЯ GET_DATA ==========
    
    def test_get_data_returns_bool(self):
        """Проверка: get_data возвращает булево значение"""
        result = self.data_maker.get_data()
        self.assertIsInstance(result, bool, "get_data должна вернуть True или False")
        print(f"  → get_data вернула {result}")

    def test_get_data_creates_npy_files(self):
        """Проверка: после get_data появляются .npy файлы"""
        self.data_maker.get_data()
        
        X_exists = os.path.exists(self.data_maker.X_train_path)
        y_exists = os.path.exists(self.data_maker.y_train_path)
        
        # Если есть данные, файлы должны быть
        if len(os.listdir(self.data_maker.data_dir)) > 0:
            self.assertTrue(X_exists, f"Файл {self.data_maker.X_train_path} не создан")
            self.assertTrue(y_exists, f"Файл {self.data_maker.y_train_path} не создан")
            print(f"  → X_train.npy создан: {X_exists}")
            print(f"  → y_train.npy создан: {y_exists}")

    def test_get_data_loads_correct_shape(self):
        """Проверка: форма загруженных данных соответствует 28×28×3 = 2352"""
        self.data_maker.get_data()
        
        if os.path.exists(self.data_maker.X_train_path):
            X = np.load(self.data_maker.X_train_path)
            if len(X) > 0:
                expected_features = 28 * 28 * 3  # 2352
                self.assertEqual(X.shape[1], expected_features, 
                                f"Размер признаков {X.shape[1]}, ожидается {expected_features}")
                print(f"  → Форма данных: {X.shape} (ожидалось {expected_features} признаков)")

    def test_get_data_non_empty(self):
        """Проверка: загружается хотя бы одна картинка"""
        self.data_maker.get_data()
        
        if os.path.exists(self.data_maker.X_train_path):
            X = np.load(self.data_maker.X_train_path)
            self.assertGreater(len(X), 0, "Не загружено ни одной картинки")
            print(f"  → Загружено {len(X)} картинок")

    # ========== ТЕСТЫ ДЛЯ SPLIT_DATA ==========

    def test_split_data_returns_bool(self):
        """Проверка: split_data возвращает булево значение"""
        result = self.data_maker.split_data()
        self.assertIsInstance(result, bool, "split_data должна вернуть True или False")
        print(f"  → split_data вернула {result}")

    def test_split_data_creates_train_test_files(self):
        """Проверка: после split_data создаются train/test файлы"""
        self.data_maker.split_data()
        
        files_exist = all([
            os.path.exists(self.data_maker.X_train_path),
            os.path.exists(self.data_maker.y_train_path),
            os.path.exists(self.data_maker.X_test_path),
            os.path.exists(self.data_maker.y_test_path)
        ])
        
        self.assertTrue(files_exist, "Не все train/test файлы созданы")
        print(f"  → X_train.npy: {os.path.exists(self.data_maker.X_train_path)}")
        print(f"  → y_train.npy: {os.path.exists(self.data_maker.y_train_path)}")
        print(f"  → X_test.npy: {os.path.exists(self.data_maker.X_test_path)}")
        print(f"  → y_test.npy: {os.path.exists(self.data_maker.y_test_path)}")

    def test_split_data_correct_split_ratio(self):
        """Проверка: соотношение train/test примерно 80/20"""
        self.data_maker.split_data()
        
        if os.path.exists(self.data_maker.X_train_path) and os.path.exists(self.data_maker.X_test_path):
            X_train = np.load(self.data_maker.X_train_path)
            X_test = np.load(self.data_maker.X_test_path)
            
            total = len(X_train) + len(X_test)
            train_ratio = len(X_train) / total
            test_ratio = len(X_test) / total
            
            # Проверяем, что train ~80%, test ~20% (допуск 5%)
            self.assertAlmostEqual(train_ratio, 0.8, delta=0.05, 
                                  msg=f"Train ratio {train_ratio:.2f}, ожидается ~0.8")
            self.assertAlmostEqual(test_ratio, 0.2, delta=0.05,
                                  msg=f"Test ratio {test_ratio:.2f}, ожидается ~0.2")
            
            print(f"  → Train: {len(X_train)} ({train_ratio*100:.1f}%)")
            print(f"  → Test: {len(X_test)} ({test_ratio*100:.1f}%)")

    def test_split_data_preserves_class_distribution(self):
        """Проверка: распределение классов сохраняется после split"""
        self.data_maker.split_data()
        
        if os.path.exists(self.data_maker.y_train_path) and os.path.exists(self.data_maker.y_test_path):
            y_train = np.load(self.data_maker.y_train_path)
            y_test = np.load(self.data_maker.y_test_path)
            
            train_unique, train_counts = np.unique(y_train, return_counts=True)
            test_unique, test_counts = np.unique(y_test, return_counts=True)
            
            # Проверяем, что все классы есть и в train, и в test
            self.assertSetEqual(set(train_unique), set(test_unique),
                               "Классы в train и test не совпадают")
            
            print(f"  → Распределение в train: {dict(zip(train_unique, train_counts))}")
            print(f"  → Распределение в test: {dict(zip(test_unique, test_counts))}")

    # ========== ТЕСТЫ ДЛЯ LOAD_IMAGES_FROM_FOLDER ==========

    def test_load_images_from_folder_returns_arrays(self):
        """Проверка: load_images_from_folder возвращает списки"""
        if len(os.listdir(self.data_maker.data_dir)) > 0:
            class_name = os.listdir(self.data_maker.data_dir)[0]
            class_path = os.path.join(self.data_maker.data_dir, class_name)
            
            X, y = self.data_maker.load_images_from_folder(class_path, 0)
            
            self.assertIsInstance(X, list, "X должен быть списком")
            self.assertIsInstance(y, list, "y должен быть списком")
            print(f"  → Загружено {len(X)} картинок из {class_name}")

    def test_load_images_from_folder_correct_labels(self):
        """Проверка: лейблы соответствуют class_id"""
        if len(os.listdir(self.data_maker.data_dir)) > 0:
            class_name = os.listdir(self.data_maker.data_dir)[0]
            class_path = os.path.join(self.data_maker.data_dir, class_name)
            
            X, y = self.data_maker.load_images_from_folder(class_path, class_id=42)
            
            if len(y) > 0:
                unique_labels = set(y)
                self.assertEqual(len(unique_labels), 1, "Все лейблы должны быть одинаковыми")
                self.assertEqual(unique_labels.pop(), 42, f"Лейбл должен быть 42, а не {unique_labels}")
                print(f"  → Все {len(y)} картинок имеют правильный лейбл 42")

    # ========== ТЕСТЫ ДЛЯ КОНФИГА ==========

    def test_config_ini_created(self):
        """Проверка: config.ini создаётся после split_data"""
        self.data_maker.split_data()
        self.assertTrue(os.path.exists("config.ini"), "config.ini не создан")
        print("  → config.ini существует")

    def test_config_ini_has_data_section(self):
        """Проверка: в config.ini есть секция DATA"""
        self.data_maker.split_data()
        config.read("config.ini")
        self.assertTrue(config.has_section("DATA"), "Нет секции DATA в config.ini")
        print("  → Секция DATA найдена")

    def test_config_ini_has_split_data_section(self):
        """Проверка: в config.ini есть секция SPLIT_DATA"""
        self.data_maker.split_data()
        config.read("config.ini")
        self.assertTrue(config.has_section("SPLIT_DATA"), "Нет секции SPLIT_DATA в config.ini")
        print("  → Секция SPLIT_DATA найдена")

    # ========== ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ==========

    def test_data_dir_exists(self):
        """Проверка: папка с данными существует"""
        self.assertTrue(os.path.exists(self.data_maker.data_dir), 
                       f"Папка {self.data_maker.data_dir} не найдена")
        print(f"  → data_dir существует: {self.data_maker.data_dir}")

    def test_at_least_one_class_exists(self):
        """Проверка: есть хотя бы один класс"""
        if os.path.exists(self.data_maker.data_dir):
            classes = os.listdir(self.data_maker.data_dir)
            self.assertGreater(len(classes), 0, "Нет ни одного класса в папке data")
            print(f"  → Найдено классов: {len(classes)}")


if __name__ == "__main__":
    # Запускаем с verbosity=2 для красивого вывода
    unittest.main(verbosity=2)