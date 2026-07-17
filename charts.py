import cv2
from ultralytics import YOLO
import time

# Загружаем модель YOLOv8n (nano - самая легкая и быстрая)
# Для лучшей точности можно использовать: yolov8s.pt, yolov8m.pt и т.д.
model = YOLO('yolov8n.pt')  # Убедитесь, что файл модели в той же папке

# Функция для установки разрешения камеры
def set_camera_resolution(cap, width, height):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Проверяем, какое разрешение установилось фактически
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if actual_width != width or actual_height != height:
        print(f"Предупреждение: запрошено разрешение {width}x{height}, но установлено {actual_width}x{actual_height}")
    
    return actual_width, actual_height

# Функция выбора разрешения
def choose_resolution():
    print("\nДоступные разрешения:")
    print("1. 640x480 (SD)")
    print("2. 800x600")
    print("3. 1024x768")
    print("4. 1280x720 (HD)")
    print("5. 1280x800")
    print("6. 1366x768")
    print("7. 1600x900")
    print("8. 1920x1080 (Full HD)")
    print("9. 2560x1440 (2K)")
    print("10. Свое разрешение")
    
    choice = input("Выберите разрешение (1-10): ").strip()
    
    resolutions = {
        '1': (640, 480),
        '2': (800, 600),
        '3': (1024, 768),
        '4': (1280, 720),
        '5': (1280, 800),
        '6': (1366, 768),
        '7': (1600, 900),
        '8': (1920, 1080),
        '9': (2560, 1440)
    }
    
    if choice in resolutions:
        return resolutions[choice]
    elif choice == '10':
        try:
            width = int(input("Введите ширину: "))
            height = int(input("Введите высоту: "))
            return (width, height)
        except ValueError:
            print("Неверный ввод. Будет использовано разрешение по умолчанию (640x480)")
            return (640, 480)
    else:
        print("Неверный выбор. Будет использовано разрешение по умолчанию (640x480)")
        return (640, 480)

# Открываем веб-камеру
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Ошибка: не удалось открыть камеру")
    exit()

# Выбор разрешения
width, height = choose_resolution()

# Устанавливаем разрешение
actual_width, actual_height = set_camera_resolution(cap, width, height)

print(f"\nКамера открыта: {actual_width}x{actual_height}")
print("Нажмите 'q' для выхода")
print("Нажмите 's' для сохранения фото с детекцией")
print("Нажмите 'r' для смены разрешения (потребуется перезапуск)")

# Переменные для расчета FPS
prev_time = time.time()
fps = 0

# Масштабирование отображения (если разрешение слишком большое)
display_scale = 1.0
if actual_width > 1280:
    display_scale = 1280 / actual_width
    print(f"Разрешение большое, будет показано с масштабом {display_scale:.2f}")

# Дополнительные настройки производительности
use_half_precision = False  # Для ускорения на слабых GPU
if actual_width * actual_height > 1280 * 720:
    use_half_precision = input("\nРазрешение высокое, использовать half-precision для ускорения? (y/n): ").lower() == 'y'

while True:
    # Захватываем кадр
    ret, frame = cap.read()
    
    if not ret:
        print("Ошибка захвата кадра")
        break
    
    # Опционально: уменьшаем кадр для детекции, чтобы ускорить обработку
    detection_frame = frame
    if actual_width > 1280:
        # Для высоких разрешений уменьшаем кадр перед детекцией для скорости
        detection_frame = cv2.resize(frame, (1280, int(1280 * actual_height / actual_width)))
    
    # Выполняем детекцию объектов
    # Для высоких разрешений можно уменьшить imgsz для скорости
    imgsz = 640 if actual_width > 1280 else None
    results = model(detection_frame, device=0, verbose=False, imgsz=imgsz)
    
    # Получаем отрисованный кадр с bounding boxes
    annotated_frame = results[0].plot()
    
    # Если детекция была на уменьшенном кадре, масштабируем обратно
    if actual_width > 1280:
        annotated_frame = cv2.resize(annotated_frame, (actual_width, actual_height))
    
    # Расчет FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    
    # Добавляем информацию на кадр
    cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.putText(annotated_frame, f"Resolution: {actual_width}x{actual_height}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Показываем количество обнаруженных объектов
    num_objects = len(results[0].boxes)
    cv2.putText(annotated_frame, f"Objects: {num_objects}", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Добавляем информацию о масштабе для детекции
    if actual_width > 1280:
        cv2.putText(annotated_frame, f"Detection scale: 1280x{int(1280 * actual_height / actual_width)}", (10, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    # Масштабируем для отображения, если нужно
    display_frame = annotated_frame
    if display_scale != 1.0:
        display_width = int(actual_width * display_scale)
        display_height = int(actual_height * display_scale)
        display_frame = cv2.resize(annotated_frame, (display_width, display_height))
    
    # Отображаем кадр
    cv2.imshow('YOLOv8 Object Detection', display_frame)
    
    # Обработка нажатий клавиш
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('s'):
        # Сохраняем кадр с детекцией в полном разрешении
        filename = f"detection_{int(time.time())}.jpg"
        cv2.imwrite(filename, annotated_frame)
        print(f"Фото сохранено как {filename} ({actual_width}x{actual_height})")
    elif key == ord('r'):
        print("\nПерезапустите программу для смены разрешения")
        break

# Освобождаем ресурсы
cap.release()
cv2.destroyAllWindows()
print("Программа завершена")