import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog
import pyperclip  # Importar la biblioteca pyperclip

# Archivo de configuración
config_file = 'config.json'

# Función para cargar o inicializar la configuración
def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            try:
                config = json.load(file)
            except json.JSONDecodeError:
                config = initialize_config()
                save_config(config)
    else:
        config = initialize_config()
        save_config(config)
    return config

# Función para inicializar la configuración por defecto
def initialize_config():
    return {
        "upper_unit_start_date": "01/02/2024",
        "lower_unit_start_date": "14/02/2024"
    }

# Función para guardar la configuración
def save_config(config):
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

# Funciones para la GUI
def ask_for_dates(config):
    upper_unit_date = simpledialog.askstring("Input", f"Upper Unit start date (current: {config['upper_unit_start_date']}):", initialvalue=config['upper_unit_start_date'])
    lower_unit_date = simpledialog.askstring("Input", f"Lower Unit start date (current: {config['lower_unit_start_date']}):", initialvalue=config['lower_unit_start_date'])
    if upper_unit_date:
        config['upper_unit_start_date'] = upper_unit_date
    if lower_unit_date:
        config['lower_unit_start_date'] = lower_unit_date
    save_config(config)

def select_service():
    services = ["Toronto Hydro", "Enbridge GAS", "Toronto Water & Solid Waste Management Services"]
    service_choice = simpledialog.askinteger("Input", "Select the service:\n1. Toronto Hydro\n2. Enbridge GAS\n3. Toronto Water & Solid Waste Management Services", minvalue=1, maxvalue=3)
    return service_choice, services[service_choice - 1]

def get_service_details():
    amount = simpledialog.askfloat("Input", "Enter the total amount of the bill:")
    from_date = simpledialog.askstring("Input", f"From date (default: {datetime.today().strftime('%d/%m/%Y')}):", initialvalue=datetime.today().strftime('%d/%m/%Y'))
    to_date = simpledialog.askstring("Input", f"To date (default: {(datetime.today() + timedelta(days=30)).strftime('%d/%m/%Y')}):", initialvalue=(datetime.today() + timedelta(days=30)).strftime('%d/%m/%Y'))
    due_date = simpledialog.askstring("Input", "Enter the due date (DD/MM/YYYY):")
    return amount, from_date, to_date, due_date

def get_service_details_option_3():
    water_amount = simpledialog.askfloat("Input", "Enter the amount for Water/Sewer Services:")
    waste_amount = simpledialog.askfloat("Input", "Enter the amount for Solid Waste Management Services:")
    from_date = simpledialog.askstring("Input", f"From date (default: {datetime.today().strftime('%d/%m/%Y')}):", initialvalue=datetime.today().strftime('%d/%m/%Y'))
    to_date = simpledialog.askstring("Input", f"To date (default: {(datetime.today() + timedelta(days=30)).strftime('%d/%m/%Y')}):", initialvalue=(datetime.today() + timedelta(days=30)).strftime('%d/%m/%Y'))
    due_date = simpledialog.askstring("Input", "Enter the due date (DD/MM/YYYY):")
    early_payment_date = simpledialog.askstring("Input", "Enter the date for 'Amount Due if paid before' (DD/MM/YYYY):")
    early_payment_discount = simpledialog.askfloat("Input", "Enter the early payment discount:")
    return water_amount, waste_amount, from_date, to_date, due_date, early_payment_date, early_payment_discount

# Función para Calcular Proporciones y Verificar Fechas
def parse_date(date_string):
    for fmt in ('%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            pass
    raise ValueError(f"Date {date_string} does not match expected formats")

def calculate_proportions(amount, from_date, to_date, upper_start, lower_start, consider_dates):
    if not consider_dates:
        return round(amount / 2, 2), round(amount / 2, 2)
    
    from_date = parse_date(from_date)
    to_date = parse_date(to_date)
    upper_start = parse_date(upper_start)
    lower_start = parse_date(lower_start)
    
    total_days = (to_date - from_date).days + 1
    
    upper_days = (to_date - max(from_date, upper_start)).days + 1
    lower_days = (to_date - max(from_date, lower_start)).days + 1
    
    upper_proportion = upper_days / total_days
    lower_proportion = lower_days / total_days
    
    upper_amount = amount * upper_proportion
    lower_amount = amount * lower_proportion
    
    return round(upper_amount, 2), round(lower_amount, 2)

# Función para Generar el Texto
def generate_text(service_name, amount, upper_amount, lower_amount, from_date, to_date, due_date, upper_discount=None, lower_discount=None, early_payment_date=None, late_amount=None):
    text = f"{service_name}\n\nTotal: {amount}\nLower Unit: {lower_amount}\nUpper Unit: {upper_amount}\n\nPeriod: {from_date.upper()} TO {to_date.upper()}\n\nDUE DATE: {due_date.upper()}\n\nMake sure that the deposit is made before the due date."
    if upper_discount is not None and lower_discount is not None:
        text += f"\n\nDiscount distribution if paid early:\nLower Unit: Water - {lower_discount}\nUpper Unit: Water - {upper_discount}\n\nTotal after discount:\nLower Unit: {round(lower_amount - lower_discount, 2)}\nUpper Unit: {round(upper_amount - upper_discount, 2)}"
    if late_amount:
        text += f"\n\nIf payment is made after {due_date.upper()}, then the payment should be {late_amount} CAD"
    return text

# Función para copiar el texto al portapapeles
def copy_to_clipboard(text):
    pyperclip.copy(text)
    messagebox.showinfo("Info", "Text copied to clipboard!")

# Función Principal con GUI
def main():
    config = load_config()
    
    consider_dates = messagebox.askyesno("Input", "Do you want to consider rental start dates for calculation?")
    if consider_dates:
        ask_for_dates(config)
    
    service_choice, service_name = select_service()
    
    if service_choice == 3:
        water_amount, waste_amount, from_date, to_date, due_date, early_payment_date, early_payment_discount = get_service_details_option_3()
        total_amount = water_amount
        upper_water, lower_water = calculate_proportions(water_amount, from_date, to_date, config['upper_unit_start_date'], config['lower_unit_start_date'], consider_dates)
        
        # Calcular el descuento
        water_discount = (water_amount / (water_amount + waste_amount)) * early_payment_discount
        upper_water_discount = round(upper_water / water_amount * water_discount, 2) if water_amount != 0 else 0
        lower_water_discount = round(lower_water / water_amount * water_discount, 2) if water_amount != 0 else 0
        
        text = generate_text(service_name, total_amount, upper_water, lower_water, from_date, to_date, due_date, upper_water_discount, lower_water_discount, early_payment_date)
    else:
        amount, from_date, to_date, due_date = get_service_details()
        upper_amount, lower_amount = calculate_proportions(amount, from_date, to_date, config['upper_unit_start_date'], config['lower_unit_start_date'], consider_dates)
        text = generate_text(service_name, amount, upper_amount, lower_amount, from_date, to_date, due_date)
    
    # Crear una nueva ventana para mostrar el texto y el botón de copiar
    result_window = tk.Toplevel()
    result_window.title("Generated Text")
    text_box = tk.Text(result_window, wrap="word")
    text_box.insert("1.0", text)
    text_box.config(state="disabled")  # Hacer que el Text sea de solo lectura
    text_box.pack(padx=10, pady=10)

    copy_button = tk.Button(result_window, text="Copy to Clipboard", command=lambda: copy_to_clipboard(text))
    copy_button.pack(pady=10)

# Configurar la ventana principal de Tkinter
root = tk.Tk()
root.withdraw()  # Ocultar la ventana principal

# Ejecutar la función principal
main()
