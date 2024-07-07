import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, redirect, url_for
import pyperclip

app = Flask(__name__)

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

# Rutas de Flask
@app.route('/', methods=['GET', 'POST'])
def index():
    config = load_config()
    if request.method == 'POST':
        consider_dates = 'consider_dates' in request.form
        if consider_dates:
            upper_unit_date = request.form.get('upper_unit_start_date')
            lower_unit_date = request.form.get('lower_unit_start_date')
            if upper_unit_date:
                config['upper_unit_start_date'] = upper_unit_date
            if lower_unit_date:
                config['lower_unit_start_date'] = lower_unit_date
            save_config(config)
        
        service_choice = int(request.form.get('service_choice'))
        if service_choice == 3:
            water_amount = float(request.form.get('water_amount'))
            waste_amount = float(request.form.get('waste_amount'))
            from_date = request.form.get('from_date')
            to_date = request.form.get('to_date')
            due_date = request.form.get('due_date')
            early_payment_date = request.form.get('early_payment_date')
            early_payment_discount = float(request.form.get('early_payment_discount'))
            total_amount = water_amount
            upper_water, lower_water = calculate_proportions(water_amount, from_date, to_date, config['upper_unit_start_date'], config['lower_unit_start_date'], consider_dates)
            water_discount = (water_amount / (water_amount + waste_amount)) * early_payment_discount
            upper_water_discount = round(upper_water / water_amount * water_discount, 2) if water_amount != 0 else 0
            lower_water_discount = round(lower_water / water_amount * water_discount, 2) if water_amount != 0 else 0
            text = generate_text("Water & Solid Waste", total_amount, upper_water, lower_water, from_date, to_date, due_date, upper_water_discount, lower_water_discount, early_payment_date)
        else:
            amount = float(request.form.get('amount'))
            from_date = request.form.get('from_date')
            to_date = request.form.get('to_date')
            due_date = request.form.get('due_date')
            upper_amount, lower_amount = calculate_proportions(amount, from_date, to_date, config['upper_unit_start_date'], config['lower_unit_start_date'], consider_dates)
            service_name = ["Toronto Hydro", "Enbridge GAS", "Toronto Water & Solid Waste Management Services"][service_choice - 1]
            text = generate_text(service_name, amount, upper_amount, lower_amount, from_date, to_date, due_date)
        
        return render_template_string(template, text=text, config=config, datetime=datetime, timedelta=timedelta)
    
    return render_template_string(template, config=config, datetime=datetime, timedelta=timedelta)

@app.route('/copy', methods=['POST'])
def copy():
    text = request.form.get('text')
    pyperclip.copy(text)
    return redirect(url_for('index'))

# Template HTML
template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Billing Generator</title>
</head>
<body>
    <h1>Billing Generator</h1>
    <form method="post">
        <h2>Configuration</h2>
        <label for="consider_dates">Consider rental start dates for calculation:</label>
        <input type="checkbox" id="consider_dates" name="consider_dates">
        <br>
        <label for="upper_unit_start_date">Upper Unit start date:</label>
        <input type="text" id="upper_unit_start_date" name="upper_unit_start_date" value="{{ config['upper_unit_start_date'] }}">
        <br>
        <label for="lower_unit_start_date">Lower Unit start date:</label>
        <input type="text" id="lower_unit_start_date" name="lower_unit_start_date" value="{{ config['lower_unit_start_date'] }}">
        <br>
        <h2>Service Selection</h2>
        <label for="service_choice">Select the service:</label>
        <select id="service_choice" name="service_choice">
            <option value="1">Toronto Hydro</option>
            <option value="2">Enbridge GAS</option>
            <option value="3">Toronto Water & Solid Waste Management Services</option>
        </select>
        <br>
        <h2>Service Details</h2>
        <label for="amount">Total amount of the bill:</label>
        <input type="text" id="amount" name="amount">
        <br>
        <label for="from_date">From date:</label>
        <input type="text" id="from_date" name="from_date" value="{{ datetime.today().strftime('%d/%m/%Y') }}">
        <br>
        <label for="to_date">To date:</label>
        <input type="text" id="to_date" name="to_date" value="{{ (datetime.today() + timedelta(days=30)).strftime('%d/%m/%Y') }}">
        <br>
        <label for="due_date">Due date:</label>
        <input type="text" id="due_date" name="due_date">
        <br>
        <h2>Water & Solid Waste Management Services Details (if selected)</h2>
        <label for="water_amount">Amount for Water/Sewer Services:</label>
        <input type="text" id="water_amount" name="water_amount">
        <br>
        <label for="waste_amount">Amount for Solid Waste Management Services:</label>
        <input type="text" id="waste_amount" name="waste_amount">
        <br>
        <label for="early_payment_date">Date for 'Amount Due if paid before':</label>
        <input type="text" id="early_payment_date" name="early_payment_date">
        <br>
        <label for="early_payment_discount">Early payment discount:</label>
        <input type="text" id="early_payment_discount" name="early_payment_discount">
        <br>
        <button type="submit">Generate Text</button>
    </form>
    {% if text %}
    <h2>Generated Text</h2>
    <textarea rows="10" cols="50" readonly>{{ text }}</textarea>
    <form method="post" action="{{ url_for('copy') }}">
        <input type="hidden" name="text" value="{{ text }}">
        <button type="submit">Copy to Clipboard</button>
    </form>
    {% endif %}
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
