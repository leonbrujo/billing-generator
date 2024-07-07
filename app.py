import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, redirect, url_for

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
    with open(config_file, 'w') as file):
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
        consider_dates = request.form.get('consider_dates') == 'on'
        if consider_dates:
            upper_unit_date = request.form.get('upper_unit_start_date')
            lower_unit_date = request.form.get('lower_unit_start_date')
            if upper_unit_date:
                config['upper_unit_start_date'] = upper_unit_date
            if lower_unit_date:
                config['lower_unit_start_date'] = lower_unit_date
            save_config(config)

        date_range = request.form.get('date_range').split(' to ')
        from_date = date_range[0]
        to_date = date_range[1]
        
        service_choice = int(request.form.get('service_choice'))
        if service_choice == 3:
            water_amount = float(request.form.get('water_amount'))
            waste_amount = float(request.form.get('waste_amount'))
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
            due_date = request.form.get('due_date')
            upper_amount, lower_amount = calculate_proportions(amount, from_date, to_date, config['upper_unit_start_date'], config['lower_unit_start_date'], consider_dates)
            service_name = ["Toronto Hydro", "Enbridge GAS", "Toronto Water & Solid Waste Management Services"][service_choice - 1]
            text = generate_text(service_name, amount, upper_amount, lower_amount, from_date, to_date, due_date)
        
        return render_template_string(template, text=text, config=config, datetime=datetime, timedelta=timedelta)
    
    return render_template_string(template, config=config, datetime=datetime, timedelta=timedelta)

# Template HTML
template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Billing Generator</title>
    <!-- Flatpickr CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        form {
            display: grid;
            gap: 20px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .form-group label {
            margin-bottom: 5px;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .form-group input[type="checkbox"] {
            width: auto;
        }
        .toggle-button {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 25px;
        }
        .toggle-button input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 25px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 17px;
            width: 17px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #007bff;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        .form-group button {
            padding: 10px 20px;
            border: none;
            background-color: #007bff;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        .form-group button:hover {
            background-color: #0056b3;
        }
        .generated-text {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .generated-text textarea {
            width: 100%;
            max-width: 700px;
        }
        #date_fields {
            display: none;
        }
        @media (max-width: 600px) {
            .container {
                padding: 10px;
            }
            .form-group {
                gap: 10px;
            }
            .form-group input,
            .form-group select,
            .form-group textarea {
                padding: 8px;
            }
            .form-group button {
                padding: 8px 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Billing Generator</h1>
        <form method="post">
            <div class="form-group">
                <label for="consider_dates">Consider rental start dates for calculation:</label>
                <label class="toggle-button">
                    <input type="checkbox" id="consider_dates" name="consider_dates" onclick="toggleDateFields()">
                    <span class="slider"></span>
                </label>
            </div>
            <div id="date_fields">
                <div class="form-group">
                    <label for="upper_unit_start_date">Upper Unit start date:</label>
                    <input type="text" id="upper_unit_start_date" name="upper_unit_start_date" value="{{ config['upper_unit_start_date'] }}" class="datepicker">
                </div>
                <div class="form-group">
                    <label for="lower_unit_start_date">Lower Unit start date:</label>
                    <input type="text" id="lower_unit_start_date" name="lower_unit_start_date" value="{{ config['lower_unit_start_date'] }}" class="datepicker">
                </div>
            </div>
            <div class="form-group">
                <label for="service_choice">Select the service:</label>
                <select id="service_choice" name="service_choice" onchange="toggleWaterSolidWasteDetails()">
                    <option value="1">Toronto Hydro</option>
                    <option value="2">Enbridge GAS</option>
                    <option value="3">Toronto Water & Solid Waste Management Services</option>
                </select>
            </div>
            <div class="form-group">
                <label for="amount">Total amount of the bill:</label>
                <input type="number" inputmode="decimal" step="0.01" id="amount" name="amount">
            </div>
            <div class="form-group">
                <label for="date_range">Select Date Range:</label>
                <input type="text" id="date_range" name="date_range" class="daterange" placeholder="Select Date Range">
            </div>
            <div class="form-group">
                <label for="due_date">Due date:</label>
                <input type="text" id="due_date" name="due_date" class="datepicker">
            </div>
            <div id="water_solid_waste_details" style="display: none;">
                <h2>Water & Solid Waste Management Services Details</h2>
                <div class="form-group">
                    <label for="water_amount">Amount for Water/Sewer Services:</label>
                    <input type="number" inputmode="decimal" step="0.01" id="water_amount" name="water_amount">
                </div>
                <div class="form-group">
                    <label for="waste_amount">Amount for Solid Waste Management Services:</label>
                    <input type="number" inputmode="decimal" step="0.01" id="waste_amount" name="waste_amount">
                </div>
                <div class="form-group">
                    <label for="early_payment_date">Date for 'Amount Due if paid before':</label>
                    <input type="text" id="early_payment_date" name="early_payment_date" class="datepicker">
                </div>
                <div class="form-group">
                    <label for="early_payment_discount">Early payment discount:</label>
                    <input type="number" inputmode="decimal" step="0.01" id="early_payment_discount" name="early_payment_discount">
                </div>
            </div>
            <div class="form-group">
                <button type="submit">Generate Text</button>
            </div>
        </form>
        {% if text %}
        <div class="generated-text">
            <h2>Generated Text</h2>
            <textarea id="generated_text" rows="10" cols="50" readonly>{{ text }}</textarea>
            <button onclick="copyToClipboard()">Copy to Clipboard</button>
        </div>
        {% endif %}
    </div>
    
    <!-- Flatpickr JS -->
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize Flatpickr for single date selection
            flatpickr('.datepicker', {
                dateFormat: 'd/m/Y',
                allowInput: true
            });
            // Initialize Flatpickr for date range selection
            flatpickr('.daterange', {
                mode: 'range',
                dateFormat: 'd/m/Y',
                allowInput: true
            });
        });

        function toggleDateFields() {
            var checkBox = document.getElementById("consider_dates");
            var dateFields = document.getElementById("date_fields");
            if (checkBox.checked == true){
                dateFields.style.display = "block";
            } else {
                dateFields.style.display = "none";
            }
        }

        function toggleWaterSolidWasteDetails() {
            var serviceChoice = document.getElementById("service_choice").value;
            var waterSolidWasteDetails = document.getElementById("water_solid_waste_details");
            if (serviceChoice == "3") {
                waterSolidWasteDetails.style.display = "block";
            } else {
                waterSolidWasteDetails.style.display = "none";
            }
        }

        function copyToClipboard() {
            var copyText = document.getElementById("generated_text");
            copyText.select();
            document.execCommand("copy");
            alert("Copied the text: " + copyText.value);
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
