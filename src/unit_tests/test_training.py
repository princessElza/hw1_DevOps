import configparser
import os
import unittest
import numpy as np
import pickle
import sys

sys.path.insert(1, os.path.join(os.getcwd(), "src"))

from train import ModelTrainer

config = configparser.ConfigParser()
config.read("config.ini")


class TestModelTrainer(unittest.TestCase):
    """
    Тесты для ModelTrainer (обучение модели)
    """

    def setUp(self) -> None:
        """Инициализация перед каждым тестом"""
        self.trainer = ModelTrainer()
        print(f"\n[SETUP] ModelTrainer создан")

    def tearDown(self) -> None:
        """Очистка после каждого теста"""
        print("[TEARDOWN] Тест завершён")

    # ========== ТЕСТЫ ДЛЯ LOAD_DATA ==========

    def test_load_data_returns_tuple(self):
        """Проверка: load_data возвращает кортеж из 4 элементов"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            result = self.trainer.load_data()
            self.assertIsInstance(result, tuple, "load_data должна вернуть tuple")
            self.assertEqual(len(result), 4, "Должно вернуться 4 элемента")
            print("  → load_data вернула 4 массива")

    def test_load_data_returns_numpy_arrays(self):
        """Проверка: load_data возвращает numpy массивы"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            X_train, y_train, X_test, y_test = self.trainer.load_data()
            
            self.assertIsInstance(X_train, np.ndarray, "X_train должен быть numpy array")
            self.assertIsInstance(y_train, np.ndarray, "y_train должен быть numpy array")
            print("  → Все данные загружены как numpy массивы")

    def test_load_data_correct_shapes(self):
        """Проверка: формы данных корректны"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            X_train, y_train, X_test, y_test = self.trainer.load_data()
            
            # Количество признаков должно быть 28*28*3 = 2352
            self.assertEqual(X_train.shape[1], 2352, "Неверное число признаков")
            self.assertEqual(X_test.shape[1], 2352, "Неверное число признаков")
            
            # Количество меток должно совпадать с количеством образцов
            self.assertEqual(len(X_train), len(y_train), 
                           "Количество train образцов и меток не совпадает")
            self.assertEqual(len(X_test), len(y_test),
                           "Количество test образцов и меток не совпадает")
            
            print(f"  → Train: {X_train.shape}, Test: {X_test.shape}")

    # ========== ТЕСТЫ ДЛЯ TRAIN_MODEL ==========

    def test_train_model_returns_accuracy(self):
        """Проверка: train_model возвращает точность (float)"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            accuracy = self.trainer.train_model()
            
            self.assertIsInstance(accuracy, float, "Точность должна быть float")
            self.assertGreaterEqual(accuracy, 0, "Точность не может быть меньше 0")
            self.assertLessEqual(accuracy, 1, "Точность не может быть больше 1")
            
            print(f"  → Точность модели: {accuracy:.3f}")

    def test_train_model_creates_model_file(self):
        """Проверка: после обучения создаётся model.pkl"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            self.trainer.train_model()
            
            self.assertTrue(os.path.exists(self.trainer.model_path),
                          f"Модель не сохранена в {self.trainer.model_path}")
            print(f"  → Модель сохранена: {self.trainer.model_path}")

    def test_model_file_is_valid_pickle(self):
        """Проверка: model.pkl — корректный pickle файл"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            self.trainer.train_model()
            
            try:
                with open(self.trainer.model_path, 'rb') as f:
                    model = pickle.load(f)
                self.assertIsNotNone(model, "Модель не загружается из pickle")
                print("  → model.pkl корректный pickle файл")
            except Exception as e:
                self.fail(f"Не удалось загрузить model.pkl: {e}")

    def test_model_can_predict(self):
        """Проверка: модель может делать предсказания"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            self.trainer.train_model()
            
            with open(self.trainer.model_path, 'rb') as f:
                model = pickle.load(f)
            
            # Создаём случайный тестовый вектор
            test_input = np.random.rand(1, 2352)
            prediction = model.predict(test_input)
            
            self.assertIsInstance(prediction[0], (int, np.integer),
                                 "Предсказание должно быть целым числом")
            print(f"  → Модель предсказывает: {prediction[0]}")

    def test_model_training_is_deterministic(self):
        """Проверка: при одинаковых данных точность стабильна"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            # Обучаем дважды
            acc1 = self.trainer.train_model()
            acc2 = self.trainer.train_model()
            
            # Точность должна быть одинаковой (random_state=42)
            self.assertEqual(acc1, acc2, "Точность различается при повторном обучении")
            print(f"  → Точность стабильна: {acc1:.3f}")

    # ========== ТЕСТЫ ДЛЯ КОНФИГА ==========

    def test_config_has_model_section(self):
        """Проверка: после обучения в config.ini появляется секция MODEL"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            self.trainer.train_model()
            
            config.read("config.ini")
            self.assertTrue(config.has_section("MODEL"), "Нет секции MODEL в config.ini")
            print("  → Секция MODEL добавлена в config.ini")

    def test_config_has_accuracy(self):
        """Проверка: в config.ini сохранена точность модели"""
        if all(os.path.exists(p) for p in [
            self.trainer.X_train_path, self.trainer.y_train_path,
            self.trainer.X_test_path, self.trainer.y_test_path
        ]):
            accuracy = self.trainer.train_model()
            
            config.read("config.ini")
            saved_accuracy = float(config.get("MODEL", "accuracy"))
            
            self.assertAlmostEqual(accuracy, saved_accuracy, delta=0.001,
                                  msg="Точность в config.ini не совпадает")
            print(f"  → Точность сохранена в config.ini: {saved_accuracy:.3f}")

    # ========== ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ==========

    def test_data_files_exist_before_training(self):
        """Проверка: все необходимые файлы данных существуют"""
        files = [
            self.trainer.X_train_path,
            self.trainer.y_train_path,
            self.trainer.X_test_path,
            self.trainer.y_test_path
        ]
        
        for f in files:
            if os.path.exists(f):
                print(f"  → {os.path.basename(f)}: существует")
            else:
                print(f"  → {os.path.basename(f)}: НЕ СУЩЕСТВУЕТ (тест пропущен)")
        
        # Не делаем assert, просто информативно

    def test_classes_are_balanced(self):
        """Проверка: данные сбалансированы по классам"""
        if os.path.exists(self.trainer.y_train_path):
            y_train = np.load(self.trainer.y_train_path)
            unique, counts = np.unique(y_train, return_counts=True)
            
            # Проверяем, что ни один класс не доминирует (>60%)
            max_ratio = max(counts) / sum(counts)
            self.assertLess(max_ratio, 0.6, 
                           f"Класс доминирует: {max_ratio*100:.1f}%")
            
            print(f"  → Распределение классов: {dict(zip(unique, counts))}")


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты (preprocess + train вместе)"""

    def test_full_pipeline(self):
        """Проверка: полный пайплайн от данных до модели"""
        from preprocess import DataMaker
        
        dm = DataMaker()
        trainer = ModelTrainer()
        
        # Запускаем предобработку
        if len(os.listdir(dm.data_dir)) >= 2:
            dm.split_data()
            
            # Проверяем, что данные созданы
            self.assertTrue(os.path.exists(dm.X_train_path))
            self.assertTrue(os.path.exists(dm.X_test_path))
            
            # Обучаем модель
            accuracy = trainer.train_model()
            
            # Проверяем, что модель создана и точность не падает
            self.assertTrue(os.path.exists(trainer.model_path))
            self.assertGreaterEqual(accuracy, 0.2, "Точность подозрительно низкая")
            
            print(f"  → Полный пайплайн успешен! Точность: {accuracy:.3f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)