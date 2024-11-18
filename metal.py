import math
import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, simpledialog, ttk

# Создаем или подключаемся к базе данных
conn = sqlite3.connect('scrap_metal.db')
cursor = conn.cursor()

# Создаем таблицу для хранения данных о металлоломе
cursor.execute('''
CREATE TABLE IF NOT EXISTS metals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metal_type TEXT,
    weight REAL,
    price REAL,
    total REAL,
    date_time TEXT
)
''')
conn.commit()

class ScrapMetalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Прием Металлолома")
        
        # Доступные виды металла
        self.metal_options = ["Медь", "Калорифер", "Латунь", "Нержавейка", "Алюминий",
                              "Аккумуляторы", "Банки пивные", "Цам", "Свинец", "Медь луженая", "Чер. мет.", "Другой"]

        # Переменная для выбора количества позиций
        self.num_positions_var = tk.IntVar(value=1)
        
        # Поля для хранения информации по каждой позиции
        self.entries = []
        self.widgets = []

        # Общая сумма
        self.total_sum_var = tk.DoubleVar(value=0)

        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Поле для выбора количества позиций
        tk.Label(self.root, text="Количество позиций:").grid(row=0, column=0)
        self.num_positions_menu = ttk.Combobox(self.root, textvariable=self.num_positions_var, values=list(range(1, 11)))
        self.num_positions_menu.grid(row=0, column=1)
        self.num_positions_menu.bind("<<ComboboxSelected>>", lambda event: self.create_position_fields())
        
        # Кнопка для добавления записи
        tk.Button(self.root, text="Клиент посчитан!", command=self.add_records).grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # Кнопка для очистки базы данных
        tk.Button(self.root, text="Очистить базу данных", command=self.clear_database).grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # Кнопка для отображения последних транзакций
        tk.Button(self.root, text="Последние транзакции", command=self.show_last_transactions).grid(row=3, column=0, columnspan=2, pady=(10, 0))

        # Кнопка для отображения статистики
        tk.Button(self.root, text="Статистика", command=self.show_statistics).grid(row=4, column=0, columnspan=2, pady=(10, 0))

        # Кнопка для редактирования транзакции
        tk.Button(self.root, text="Редактировать транзакцию", command=self.edit_transaction).grid(row=5, column=0, columnspan=2, pady=(10, 0))

        # Кнопка для удаления транзакции
        tk.Button(self.root, text="Удалить транзакцию", command=self.delete_transaction).grid(row=6, column=0, columnspan=2, pady=(10, 0))

        # Изначально создаем поля для одной позиции
        self.create_position_fields()

        # Поле для общей суммы
        tk.Label(self.root, text="Общая сумма:").grid(row=7, column=0)
        tk.Entry(self.root, textvariable=self.total_sum_var, state="readonly").grid(row=7, column=1)

    def create_position_fields(self):
        # Очистка старых виджетов, если количество позиций было изменено
        for widget in self.widgets:
            widget.grid_forget()
        self.widgets.clear()

        # Создаем новые поля на основе выбранного количества позиций
        self.entries = []
        num_positions = self.num_positions_var.get()
        
        for i in range(num_positions):
            row_offset = i + 8
            
            tk.Label(self.root, text=f"Позиция {i + 1}: Вид металла").grid(row=row_offset, column=0)
            metal_var = tk.StringVar()
            metal_menu = ttk.Combobox(self.root, textvariable=metal_var, values=self.metal_options)
            metal_menu.grid(row=row_offset, column=1)
            
            weight_var = tk.DoubleVar()
            tk.Label(self.root, text="Вес (кг):").grid(row=row_offset, column=2)
            weight_entry = tk.Entry(self.root, textvariable=weight_var)
            weight_entry.grid(row=row_offset, column=3)
            
            price_var = tk.DoubleVar()
            tk.Label(self.root, text="Цена за кг:").grid(row=row_offset, column=4)
            price_entry = tk.Entry(self.root, textvariable=price_var)
            price_entry.grid(row=row_offset, column=5)
            
            total_var = tk.DoubleVar()
            tk.Label(self.root, text="Сумма:").grid(row=row_offset, column=6)
            total_entry = tk.Entry(self.root, textvariable=total_var, state="readonly")
            total_entry.grid(row=row_offset, column=7)
            
            # Обновление суммы при изменении веса или цены
            weight_entry.bind("<KeyRelease>", lambda event, w=weight_var, p=price_var, t=total_var: self.calculate_total(w, p, t))
            price_entry.bind("<KeyRelease>", lambda event, w=weight_var, p=price_var, t=total_var: self.calculate_total(w, p, t))

            # Сохраняем переменные и виджеты для каждой позиции
            self.entries.append((metal_var, weight_var, price_var, total_var))
            self.widgets.extend([metal_menu, weight_entry, price_entry, total_entry])

    def calculate_total(self, weight_var, price_var, total_var):
        # Рассчитываем сумму для конкретной позиции
        try:
            weight = weight_var.get()
            price = price_var.get()
            total = math.floor(weight * price)  # Округление вниз до целого числа
            total_var.set(total)
            self.update_total_sum()
        except tk.TclError:
            total_var.set(0)

    def update_total_sum(self):
        # Вычисляем общую сумму
        total_sum = sum(total_var.get() for _, _, _, total_var in self.entries)
        self.total_sum_var.set(total_sum)

    def add_records(self):
        # Добавляем все записи в базу данных
        date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for metal_var, weight_var, price_var, total_var in self.entries:
            metal_type = metal_var.get()
            weight = weight_var.get()
            price = price_var.get()
            total = total_var.get()
            
            if metal_type and weight > 0 and price > 0:
                cursor.execute('''
                INSERT INTO metals (metal_type, weight, price, total, date_time)
                VALUES (?, ?, ?, ?, ?)
                ''', (metal_type, weight, price, total, date_time))
        
        conn.commit()
        messagebox.showinfo("Успех", "Записи добавлены!")

        # Сбросить количество позиций
        self.num_positions_var.set(1)
        self.create_position_fields()

    def clear_database(self):
        # Запрашиваем подтверждение на очистку базы данных
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить базу данных? Это действие удалит все записи."):

            cursor.execute("DELETE FROM metals")
            conn.commit()
            messagebox.showinfo("Успех", "База данных успешно очищена!")

    def show_last_transactions(self):
        # Создаем новое окно для последних транзакций
        transactions_window = tk.Toplevel(self.root)
        transactions_window.title("Последние транзакции")

        tk.Label(transactions_window, text="ID").grid(row=0, column=0)
        tk.Label(transactions_window, text="Дата/Время").grid(row=0, column=1)
        tk.Label(transactions_window, text="Вид металла").grid(row=0, column=2)
        tk.Label(transactions_window, text="Вес (кг)").grid(row=0, column=3)
        tk.Label(transactions_window, text="Цена за кг").grid(row=0, column=4)
        tk.Label(transactions_window, text="Сумма").grid(row=0, column=5)

        cursor.execute('''
            SELECT id, metal_type, weight, price, total, date_time 
            FROM metals 
            ORDER BY id DESC 
            LIMIT 10
        ''')
        records = cursor.fetchall()

        for i, (record_id, metal_type, weight, price, total, date_time) in enumerate(records):
            tk.Label(transactions_window, text=record_id).grid(row=i + 1, column=0)
            tk.Label(transactions_window, text=date_time).grid(row=i + 1, column=1)
            tk.Label(transactions_window, text=metal_type).grid(row=i + 1, column=2)
            tk.Label(transactions_window, text=f"{weight:.2f} кг").grid(row=i + 1, column=3)
            tk.Label(transactions_window, text=f"{price:.2f}").grid(row=i + 1, column=4)
            tk.Label(transactions_window, text=f"{total:.2f}").grid(row=i + 1, column=5)

    def show_statistics(self):
        # Запрашиваем период для статистики
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        # Форматируем временные метки для отображения
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

        # Создаем новое окно для отображения статистики
        statistics_window = tk.Toplevel(self.root)
        statistics_window.title("Статистика")

        tk.Label(statistics_window, text="Начало периода:").grid(row=0, column=0)
        start_entry = tk.Entry(statistics_window)
        start_entry.insert(0, start_time_str)
        start_entry.grid(row=0, column=1)

        tk.Label(statistics_window, text="Конец периода:").grid(row=1, column=0)
        end_entry = tk.Entry(statistics_window)
        end_entry.insert(0, end_time_str)
        end_entry.grid(row=1, column=1)

        # Кнопка для получения статистики
        tk.Button(statistics_window, text="Получить статистику", command=lambda: self.fetch_statistics(start_entry.get(), end_entry.get(), statistics_window)).grid(row=2, column=0, columnspan=2)

        # Заголовки для таблицы статистики
        tk.Label(statistics_window, text="Металл").grid(row=3, column=0)
        tk.Label(statistics_window, text="Общий вес").grid(row=3, column=1)
        tk.Label(statistics_window, text="Общая сумма").grid(row=3, column=2)

    def fetch_statistics(self, start_time_str, end_time_str, statistics_window):
        # Преобразуем строки времени в объекты datetime
        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                SELECT metal_type, SUM(weight), SUM(total) 
                FROM metals 
                WHERE date_time BETWEEN ? AND ?
                GROUP BY metal_type
            ''', (start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S')))
            stats = cursor.fetchall()

            # Очистка предыдущих результатов
            for widget in statistics_window.grid_slaves():
                if widget.grid_info()["row"] > 3:
                    widget.grid_forget()

            for i, (metal_type, total_weight, total_sum) in enumerate(stats):
                tk.Label(statistics_window, text=metal_type).grid(row=i + 4, column=0)
                tk.Label(statistics_window, text=f"{total_weight:.2f} кг").grid(row=i + 4, column=1)
                tk.Label(statistics_window, text=f"{total_sum:.2f}").grid(row=i + 4, column=2)

            if not stats:
                messagebox.showinfo("Информация", "Нет данных за указанный период.")

        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите даты и время в корректном формате (ГГГГ-ММ-ДД ЧЧ:ММ:СС).")

    def edit_transaction(self):
        # Запрашиваем ID транзакции для редактирования
        transaction_id = simpledialog.askinteger("Редактирование", "Введите ID транзакции для редактирования:")
        if not transaction_id:
            return
        
        # Получаем запись с указанным ID
        cursor.execute('SELECT metal_type, weight, price, total FROM metals WHERE id = ?', (transaction_id,))
        record = cursor.fetchone()

        if record:
            # Создаем окно редактирования
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Редактирование транзакции")

            metal_var = tk.StringVar(value=record[0])
            weight_var = tk.DoubleVar(value=record[1])
            price_var = tk.DoubleVar(value=record[2])
            total_var = tk.DoubleVar(value=record[3])

            tk.Label(edit_window, text="Вид металла").grid(row=0, column=0)
            metal_menu = ttk.Combobox(edit_window, textvariable=metal_var, values=self.metal_options)
            metal_menu.grid(row=0, column=1)

            tk.Label(edit_window, text="Вес (кг)").grid(row=1, column=0)
            weight_entry = tk.Entry(edit_window, textvariable=weight_var)
            weight_entry.grid(row=1, column=1)

            tk.Label(edit_window, text="Цена за кг").grid(row=2, column=0)
            price_entry = tk.Entry(edit_window, textvariable=price_var)
            price_entry.grid(row=2, column=1)

            tk.Label(edit_window, text="Сумма").grid(row=3, column=0)
            total_entry = tk.Entry(edit_window, textvariable=total_var, state="readonly")
            total_entry.grid(row=3, column=1)

            # Обновление суммы при изменении веса или цены
            weight_entry.bind("<KeyRelease>", lambda event: self.calculate_total(weight_var, price_var, total_var))
            price_entry.bind("<KeyRelease>", lambda event: self.calculate_total(weight_var, price_var, total_var))

            # Кнопка для сохранения изменений
            save_button = tk.Button(edit_window, text="Сохранить", 
                                    command=lambda: self.save_transaction(transaction_id, metal_var, weight_var, price_var, total_var, edit_window))
            save_button.grid(row=4, column=0, columnspan=2)
        else:
            messagebox.showerror("Ошибка", "Транзакция не найдена.")

    def save_transaction(self, transaction_id, metal_var, weight_var, price_var, total_var, edit_window):
        # Получаем измененные значения
        metal_type = metal_var.get()
        weight = weight_var.get()
        price = price_var.get()
        total = total_var.get()

        # Проверка на наличие корректных данных
        if metal_type and weight > 0 and price > 0:
            # Обновляем запись в базе данных
            cursor.execute('''
                UPDATE metals 
                SET metal_type = ?, weight = ?, price = ?, total = ?, date_time = ? 
                WHERE id = ?
            ''', (metal_type, weight, price, total, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), transaction_id))
            conn.commit()

            messagebox.showinfo("Успех", "Транзакция успешно обновлена!")
            edit_window.destroy()  # Закрываем окно редактирования
        else:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля корректными значениями.")

    def delete_transaction(self):
        # Запрашиваем ID транзакции для удаления
        transaction_id = simpledialog.askinteger("Удаление", "Введите ID транзакции для удаления:")
        if transaction_id is None:
            return

        # Подтверждаем удаление
        if messagebox.askyesno("Подтверждение удаления", f"Вы уверены, что хотите удалить транзакцию с ID {transaction_id}?"):
            cursor.execute("DELETE FROM metals WHERE id = ?", (transaction_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Транзакция успешно удалена!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScrapMetalApp(root)
    root.mainloop()

