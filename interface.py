import tkinter as tk
from tkinter import ttk
import mysql.connector
from tkinter import messagebox, scrolledtext, filedialog
import re
from datetime import datetime
from fpdf import FPDF

# Функция для выполнения запроса и отображения результата
def execute_query(query):
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="daytel4125",  # Укажите свой пароль
            database="vm_lab"   # Укажите свою базу данных
        )
        
        cursor = conn.cursor()
        cursor.execute(query)

        if query.strip().lower().startswith(("insert", "update", "delete")):
            conn.commit() # Фиксация изменений
            return "Команда успешно выполнена"

        elif query.strip().startswith("SELECT"):
            return cursor.fetchall(), [col[0] for col in cursor.description]

        elif query.strip().lower().startswith("select"):
            # Получаем названия столбцов
            columns = [col[0] for col in cursor.description]
            error_label.config(text="Команда успешно выполнена", fg="green")
            error_label.update()
            
            # Очищаем таблицу перед новым выводом
            for row in tree.get_children():
                tree.delete(row)
            
            # Обновляем столбцы в Treeview
            tree["columns"] = columns
            for col in columns:
                tree.heading(col, text=col)
            
            # Вставляем данные в таблицу
            for row in cursor.fetchall():
                tree.insert("", "end", values=row)
                
    except mysql.connector.Error as err:
        return f"Ошибка: {err}"


# Функция вставки шаблонов кода
def insert_sql_template(template):
    query_text.insert(tk.END, template)

# Функция для обработки значений перед вставкой в запрос
def format_value(value):
    # Проверка, если значение похоже на дату в формате YYYY-MM-DD
    try:
        # Пробуем преобразовать в дату, если возможно
        formatted_date = datetime.strptime(value, '%Y-%m-%d').date()
        return f"'{formatted_date}'"
    except ValueError:
        pass  # Если ошибка, значит не дата, продолжаем дальше

    # Если это число, ничего не добавляем
    if isinstance(value, int) or value == "None":
        return value
    
    # Если это не число и не дата, добавляем кавычки
    return f"'{value}'"

# Функция для создания нового окна операций
def open_operation_window(operation):
    def fetch_and_display_data():
        selected_table = table_combo.get()
        if selected_table:
            data, columns = execute_query(f"SELECT * FROM {selected_table}")
            if isinstance(data, str):
                error_label.config(text=data, fg="red")
            else:
                tree.delete(*tree.get_children())
                tree["columns"] = columns
                for col in columns:
                    tree.heading(col, text=col)
                for row in data:
                    tree.insert("", "end", values=row)

    # Функция для вставки данных
    def perform_insert():
        selected_table = table_combo.get()
        if selected_table:
            values = value_entry.get()
            
            # Разделяем введенные значения на список
            value_list = [val.strip() for val in values.split(',')]

            # Применяем форматирование для каждого значения
            formatted_values = [format_value(val) for val in value_list]

            # Формируем запрос
            query = f"INSERT INTO {selected_table} VALUES ({', '.join(formatted_values)})"
            
            message = execute_query(query)
            error_label.config(text=message, fg="green" if "успешно" in message else "red")
            error_label.update()
            fetch_and_display_data()

    def perform_update():
        selected_table = table_combo.get()
        if selected_table:
            set_clause = set_entry.get()
            condition = condition_entry.get()

            # Разбиваем set_clause на столбцы и значения
            set_parts = set_clause.split(',')
            formatted_set_parts = []
            
            for part in set_parts:
                # Разделяем на колонку и значение
                column, value = part.split('=')
                column = column.strip()  # Убираем пробелы вокруг столбца
                value = value.strip()  # Убираем пробелы вокруг значения
                
                # Форматируем значение
                formatted_value = format_value(value)
                
                # Собираем обратно
                formatted_set_parts.append(f"{column} = {formatted_value}")
            
            # Формируем новый set_clause
            formatted_set_clause = ', '.join(formatted_set_parts)
            
            formatted_condition_parts = []
            column, value = condition.split('=')
            column = column.strip()  # Убираем пробелы вокруг столбца
            value = value.strip()  # Убираем пробелы вокруг значения

            # Форматируем значение
            formatted_value = format_value(value)
            formatted_condition_parts.append(f"{column} = {formatted_value}")

            # Собираем все части условия в одно строковое выражение
            formatted_condition = ''.join(formatted_condition_parts)

            if not condition:
                error_label.config(text="Ошибка: условие WHERE не может быть пустым", fg="red")
                return

            # Формируем запрос
            query = f"UPDATE {selected_table} SET {formatted_set_clause} WHERE {formatted_condition};"

            # Выполняем запрос
            message = execute_query(query)
            
            # Отображаем сообщение об ошибке или успехе
            error_label.config(text=message, fg="green" if "успешно" in message else "red")
            error_label.update()
            
            # Обновляем данные на экране
            fetch_and_display_data()

    def perform_delete():
        selected_table = table_combo.get()
        if selected_table:
            condition = condition_entry.get()
            # Разбиваем set_clause на столбцы и значения
            formatted_condition_parts = []
            
            # Разделяем на колонку и значение
            column, value = condition.split('=')
            column = column.strip()  # Убираем пробелы вокруг столбца
            value = value.strip()  # Убираем пробелы вокруг значения
                
            # Форматируем значение
            formatted_value = format_value(value)
                
            # Собираем обратно
            formatted_condition_parts.append(f"{column} = {formatted_value}")
            formatted_condition = ''.join(formatted_condition_parts)
            
            query = f"DELETE FROM {selected_table} WHERE {formatted_condition}"
            message = execute_query(query)
            error_label.config(text=message, fg="green" if "успешно" in message else "red")
            error_label.update()
            fetch_and_display_data()

    operation_window = tk.Toplevel(root)
    operation_window.title(f"{operation} Operation")

    tk.Label(operation_window, text="Выберите таблицу:").grid(row=0, column=0, padx=5, pady=5)
    table_combo = ttk.Combobox(operation_window, values=["books", "contract", "creative_groups", "customers", "orders", "published_books", "writers"])
    table_combo.grid(row=0, column=1, padx=5, pady=5)

    tk.Button(operation_window, text="Загрузить данные", command=fetch_and_display_data).grid(row=1, column=0, columnspan=2, pady=5)

    # Виджет для вывода ошибок
    error_label = tk.Label(operation_window, text="", fg="red")
    error_label.grid(row=2, column=0, columnspan=2, pady=5)

    tree = ttk.Treeview(operation_window, show="headings")
    tree.grid(row=3, column=0, columnspan=2, pady=10, sticky="nsew")

    if operation == "INSERT":
        tk.Label(operation_window, text="Введите значения по образцу в таблице через запятую:").grid(row=5, column=0, padx=5, pady=5)
        value_entry = tk.Entry(operation_window, width=50)
        value_entry.grid(row=5, column=1, padx=5, pady=5)

        tk.Button(operation_window, text="Выполнить", command=perform_insert).grid(row=6, column=0, columnspan=2, pady=10)

    elif operation == "UPDATE":
        tk.Label(operation_window, text="Введите SET выражение (например, column=value):").grid(row=4, column=0, padx=5, pady=5)
        set_entry = tk.Entry(operation_window, width=50)
        set_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(operation_window, text="Введите условие (например, id=1):").grid(row=5, column=0, padx=5, pady=5)
        condition_entry = tk.Entry(operation_window, width=50)
        condition_entry.grid(row=5, column=1, padx=5, pady=5)

        tk.Button(operation_window, text="Выполнить", command=perform_update).grid(row=6, column=0, columnspan=2, pady=10)

    elif operation == "DELETE":
        tk.Label(operation_window, text="Введите условие (например, id=1):").grid(row=4, column=0, padx=5, pady=5)
        condition_entry = tk.Entry(operation_window, width=50)
        condition_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Button(operation_window, text="Выполнить", command=perform_delete).grid(row=5, column=0, columnspan=2, pady=10)

    error_label = tk.Label(operation_window, text="", fg="red")
    error_label.grid(row=7, column=0, columnspan=2, pady=5)

# Создание файла отчёта
def generate_pdf(data, columns, filename, year):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Устанавливаем шрифт, который поддерживает Unicode (например, DejaVuSans)
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font("DejaVu", size=8)

    # Добавляем текст перед таблицей
    pdf.cell(0, 10, "Задание 26. Проект ИЗДАТЕЛЬСКИЙ ЦЕНТР", ln=True, align='C')
    pdf.cell(0, 10, "Прибыль от продаж книг издательского центра 'Печать'", ln=True, align='C')
    pdf.cell(0, 10, f"за {year} год", ln=True, align='C')
    pdf.ln(10)  # Отступ между текстом и таблицей

    # Устанавливаем ширину столбцов
    col_widths = [60, 50, 20, 15, 15, 20]  # Ширины столбцов (в мм)

    # Добавляем заголовок таблицы
    for i, col in enumerate(columns):
        # Используем ширину из col_widths для каждого столбца
        pdf.cell(col_widths[i], 10, col, border=1, align='C')
    pdf.ln()

    # Добавляем строки таблицы
    for row in data:
        for i, item in enumerate(row):
            # Используем ширину из col_widths для каждого столбца
            pdf.cell(col_widths[i], 10, str(item), border=1)
        pdf.ln()

    pdf.output(filename)

# Уникальные года заказов
def get_years():
    query = "SELECT DISTINCT YEAR(completionDate) AS year FROM orders ORDER BY year"
    data, _ = execute_query(query)
    return [str(row[0]) for row in data] if data else []

# Диалог создания отчёта
def open_report_window():

    def generate_report():
        year = year_combo.get()
        if not year:
            messagebox.showwarning("Предупреждение", "Выберите год.")
            return

        query = f"SELECT customer as Заказчик, books.name as Книга, cost as Стоимость, price as Цена, count as Число, (price - cost) * count as Прибыль from books join orders \
                   on (books.code = orders.code) where year(completionDate) = {year} union\
                  SELECT 'Итого', '', '', '', '', sum((price - cost) * count) from books join orders on (books.code = orders.code) where year(completionDate) = {year};"
        data, columns = execute_query(query)

        if data and columns:
            # Отображаем результат в текстовом поле
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, "\t".join(columns) + "\n")
            for row in data:
                output_text.insert(tk.END, "\t".join(map(str, row)) + "\n")

            # Генерируем PDF
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            if filename:
                generate_pdf(data, columns, filename, year)
                messagebox.showinfo("Успех", f"Отчет сохранен в {filename}")

    # Создаем окно выбора года
    report_window = tk.Toplevel(root)
    report_window.title("Сгенерировать отчет")

    tk.Label(report_window, text="Выберите год:").pack(pady=5)
    years = get_years()
    year_combo = ttk.Combobox(report_window, values=years)
    year_combo.pack(pady=5)

    tk.Button(report_window, text="Сгенерировать", command=generate_report).pack(pady=10)

    output_text = tk.Text(report_window, height=15, width=70)
    output_text.pack(pady=10)

# Создание основного окна
root = tk.Tk()
root.title("Интерфейс для выполнения SQL-запросов")

# Взаимодействие ползователя с БД
btn_insert = tk.Button(root, text="ВСТАВКА", command=lambda: open_operation_window("INSERT"))
btn_insert.grid(row=2, column=0, padx=5, pady=5)

btn_update = tk.Button(root, text="ИЗМЕНЕНИЕ", command=lambda: open_operation_window("UPDATE"))
btn_update.grid(row=2, column=1, padx=5, pady=5)

btn_delete = tk.Button(root, text="УДАЛЕНИЕ", command=lambda: open_operation_window("DELETE"))
btn_delete.grid(row=2, column=2, padx=5, pady=5)

btn_otchet = tk.Button(root, text="Сгенерировать отчет", command=open_report_window)
btn_otchet.grid(row=2, column=3, padx=5, pady=5)

# Виджет для вывода ошибок
error_label = tk.Label(root, text="", fg="red")
error_label.grid(row=3, column=0, columnspan=3, pady=5)

# Создание таблицы для отображения результатов
tree = ttk.Treeview(root, show="headings")
tree.grid(row=4, column=0, columnspan=3, pady=10, sticky="nsew")

# Кнопки вывода таблиц
btn_books = tk.Button(root, text="Таблица 'Книги'", command=lambda: execute_query("select * from books"), wraplength = 200)
btn_books.grid(row=5, column=0, padx=5, pady=5)

btn_contract = tk.Button(root, text="Таблица 'Контракты'", command=lambda: execute_query("select * from contract"), wraplength = 200)
btn_contract.grid(row=5, column=1, padx=5, pady=5)

btn_creative_groups = tk.Button(root, text="Таблица 'Творческие группы'", command=lambda: execute_query("select * from creative_groups"), wraplength = 200)
btn_creative_groups.grid(row=5, column=2, padx=5, pady=5)

btn_customers = tk.Button(root, text="Таблица 'Заказчики'", command=lambda: execute_query("select * from customers"), wraplength = 200)
btn_customers.grid(row=5, column=3, padx=5, pady=5)

btn_orders = tk.Button(root, text="Таблица 'Заказы'", command=lambda: execute_query("select * from orders"), wraplength = 200)
btn_orders.grid(row=6, column=0, padx=5, pady=5)

btn_published_books = tk.Button(root, text="Таблица 'Опубликованные книги'", command=lambda: execute_query("select * from published_books"), wraplength = 200)
btn_published_books.grid(row=6, column=1, padx=5, pady=5)

btn_writers = tk.Button(root, text="Таблица 'Писатели'", command=lambda: execute_query("select * from writers"), wraplength = 200)
btn_writers.grid(row=6, column=2, padx=5, pady=5)

# Кнопки для выполнения готовых запросов
btn1 = tk.Button(root, text="Вывод писателей, фамилия которых начинается с C", command=lambda: execute_query("select surname as Фамилия, \
                 name as Имя, patronimic as Отчество from writers where surname like 'П%' order by surname"), wraplength = 150)
btn1.grid(row=7, column=0, padx=5, pady=5)

btn2 = tk.Button(root, text="Вывод авторов, написавших более 1 книги", command=lambda: execute_query("select surname as Фамилия, name as Имя, patronimic as Отчество from \
                 writers where idPassport in (select writers from published_books group by writers having count(code) > 1 order by writers)"),
                 wraplength = 150)
btn2.grid(row=7, column=1, padx=5, pady=5)

btn3 = tk.Button(root, text="Вывод писателей по уникальной творческой группе", command=lambda: execute_query("select distinct creativeGroup as Творческие_группы from writers where creativeGroup is not null"),
                 wraplength = 150)
btn3.grid(row=7, column=2, padx=5, pady=5)

btn4 = tk.Button(root, text="Вывод писателей с одинаковыми фамилиями", command=lambda: execute_query("select * from writers where surname in \
                            (select surname from writers group by surname having count(surname) > 1) order by surname"), wraplength = 150)
btn4.grid(row=8, column=0, padx=5, pady=5)

btn5 = tk.Button(root, text="Вывести писателей по номеру творческой группы", command=lambda: execute_query("select * from writers where creativeGroup like '2%'"), wraplength = 150)
btn5.grid(row=8, column=1, padx=5, pady=5)

btn6 = tk.Button(root, text="Вывод числа писателей однофамильцев", command=lambda: execute_query("select count(*) as Число_записей from writers where\
                 surname in (select surname from writers group by surname having count(surname) > 1) order by surname"), wraplength = 150)
btn6.grid(row=8, column=2, padx=5, pady=5)

btn7 = tk.Button(root, text="Вывод названий книг по дате заказов", command=lambda: execute_query("select name as Название_книги, receiptDate as Дата_заказа from \
                             books join orders on (books.code = orders.code) order by receiptDate"), wraplength = 150)
btn7.grid(row=9, column=0, padx=5, pady=5)

btn8 = tk.Button(root, text="Заказ книг представителями", command=lambda: execute_query("select books.name as Название_книги, circulation as Тираж, orders.number as Номер_заказа, agent \
                 as Представитель from books inner join orders on (books.code = orders.code) left outer join customers on (orders.customer = customers.name)"), wraplength = 150)
btn8.grid(row=9, column=1, padx=5, pady=5)

btn9 = tk.Button(root, text="Возвращаем номера", command=lambda: execute_query("select idcreative_groups as Различные_номера from creative_groups union\
                            (select idPassport from writers) union (select number from contract)"), wraplength = 150)
btn9.grid(row=9, column=2, padx=5, pady=5)

# Запуск интерфейса
root.mainloop()
