import os
import re
import io
import base64
import random
import string
import sympy
import mysql.connector
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime, date
from decimal import Decimal
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, Response, redirect, url_for, flash
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO

load_dotenv()

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.getenv("SECRET_KEY")

# MySQL config
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DB")

# Connect using mysql.connector
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

product_list = [
    "4-NO2", "2-NO2", "3-NO2", "2-Cl", "3-Cl", "4-Cl", "2-Br", "3-Br",
    "4-Br", "2-OH", "4-OH", "4-OMe", "H", "4-Me", "4-OH-3-OMe", "3 4 5-OMe3",
    "4-N N-Me2", "4-CN", "2-Thiophene carboxaldehyde", "5-Br-2-thiocarboxaldehyde",
    "Indole-3-carboxaldehyde", "Furfuraldehyde", "1-Naphthaldehyde", "Cuminaldehyde",
    "Cyclohexanone", "Cyclopentanone", "Ethyl methyl ketone", "Acetone", "Isatin",
    "Benzaldehyde", "3 4 5(OCH3)", "N N-Dimethyl", "2-Thiophene", "Vanilin", "3 4 5(OME)3"
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/ulogin', methods=['GET', 'POST'])
def ulogin():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form.get('username')
        password = request.form.get('password')

        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            session['loggedin'] = True
            session['username'] = username
            return redirect(url_for('admin'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM userlog WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        cursor.close()
        conn.close()

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            return redirect(url_for('calculate'))
        else:
            msg = 'Incorrect username / password!'

    return render_template('userlogin.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM userlog WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO userlog VALUES (NULL, %s, %s, %s)', (username, password, email))
            conn.commit()
            msg = 'You have successfully registered! Now You Can Login...'
        cursor.close()
        conn.close()
    elif request.method == 'POST':
        msg = 'Please fill out the form!'

    return render_template('userlogin2.html', msg=msg)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        return render_template('forgot_password.html', email=email)
    return render_template('forgot_password.html')

@app.route('/for_pass', methods=['POST'])
def for_pass():
    msg = ''
    email = request.form.get('email')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE userlog SET password = %s WHERE email = %s', (password, email))
    conn.commit()
    cursor.close()
    conn.close()
    msg = 'Password reset successfully. You can now log in with your new password.'

    return render_template('forgot_password2.html', email=email, password=password, msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('ulogin'))

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM molecules")
    molecules = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', molecules=molecules)

@app.route('/add_molecule', methods=['POST'])
def add_molecule():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO molecules(name) VALUES (%s)', (name,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Molecule added successfully')
        return redirect(url_for('admin'))

@app.route('/delete/<mname>', methods=['POST', 'GET'])
def delete_molecule(mname):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM molecules WHERE name = %s', (mname,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Molecule Removed Successfully')
    return redirect(url_for('admin'))

@app.route('/abc')
def abc():
    print("HELLO")
    return render_template('404.html')

@app.route('/contact')
def contact():
    print("HELLO")
    return render_template('contact.html')

    
def get_product_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT name FROM molecules"  
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]



@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    product_list = get_product_list()
    emy = session.get('emy')
    ae = session.get('ae')
    aef = session.get('aef')
    ce = session.get('ce')
    rme = session.get('rme')
    oe = session.get('oe')
    pmi = session.get('pmi')
    mi = session.get('mi')
    mp = session.get('mp')
    e_factor = session.get('e_factor')
    si = session.get('si')
    wi = session.get('wi')
    ton = session.get('ton')
    tof = session.get('tof')
    user = session.get('username')
    msg = ' '
    

    if request.method == 'POST':
        product_name = request.form.get('product_name')
        user = session.get('username')

        if not product_name:
            msg = "First Choose The Product Name"
            return render_template('html', product_list=product_list, msg=msg)


        # Get values from the form
        mass_of_product = request.form.get('mass_of_product')
        mass_of_non_benign_reactants = request.form.get('mass_of_non_benign_reactants')
        
        molecular_weight_of_product = request.form.get('molecular_weight_of_product')
        total_molecular_weight_of_reactants = request.form.get('total_molecular_weight_of_reactants')
        
        yeild = request.form.get('yeild')
        amount_of_carbon = request.form.get('amount_of_carbon')
        total_carbon_reactants = request.form.get('total_carbon_reactants')
        
        mass_of_isolated_product = request.form.get('mass_of_isolated_product')
        total_mass_of_reactants = request.form.get('total_mass_of_reactants')
        
        total_mass_of_all_solvents_during_reaction = request.form.get('total_mass_of_all_solvents_during_reaction')
        total_mass_used = request.form.get('total_mass_used')
        mass_of_raw_material = request.form.get('mass_of_raw_material')
        
        total_mass_of_solvent = request.form.get('total_mass_of_solvent')
        #print(total_mass_of_solvent)
        total_mass_of_water = request.form.get('total_mass_of_water')
        
        mass_of_desrired_product = request.form.get('mass_of_desrired_product') 
        amount_of_catalyst = request.form.get('amount_of_catalyst')
        time = request.form.get('time')
        
        

        # Check if any value is None or empty
        if any(val is None or val == '' for val in (mass_of_product, mass_of_non_benign_reactants, molecular_weight_of_product, total_molecular_weight_of_reactants, yeild, amount_of_carbon, total_carbon_reactants, mass_of_isolated_product, 
        total_mass_of_reactants, total_mass_of_all_solvents_during_reaction, total_mass_used, mass_of_raw_material, total_mass_of_solvent, total_mass_of_water, mass_of_desrired_product, amount_of_catalyst, time)):
            msg = 'Please fill all the inputs'
            return render_template('html', product_list=product_list, msg = msg)

        

        # Use eval to evaluate mathematical expressions
        mass_of_product_eval = eval(mass_of_product) if mass_of_product else None
        mass_of_non_benign_reactants_eval = eval(mass_of_non_benign_reactants) if mass_of_non_benign_reactants else None
        molecular_weight_of_product_eval = eval(molecular_weight_of_product) if molecular_weight_of_product else None
        
        total_molecular_weight_of_reactants_eval = eval(total_molecular_weight_of_reactants) if total_molecular_weight_of_reactants else None
        yeild_eval = eval(yeild) if yeild else None
        amount_of_carbon_eval = eval(amount_of_carbon) if amount_of_carbon else None
        
        total_carbon_reactants_eval = eval(total_carbon_reactants) if total_carbon_reactants else None
        mass_of_isolated_product_eval = eval(mass_of_isolated_product) if mass_of_isolated_product else None
        total_mass_of_reactants_eval = eval(total_mass_of_reactants) if total_mass_of_reactants else None
        
        total_mass_of_all_solvents_during_reaction_eval = eval(total_mass_of_all_solvents_during_reaction) if total_mass_of_all_solvents_during_reaction else None
        total_mass_used_eval = eval(total_mass_used) if total_mass_used else None
        mass_of_raw_material_eval = eval(mass_of_raw_material) if mass_of_raw_material else None
        
        total_mass_of_solvent_eval = eval(total_mass_of_solvent) if total_mass_of_solvent else None
        total_mass_of_water_eval = eval(total_mass_of_water) if total_mass_of_water else None
        mass_of_desrired_product_eval = eval(mass_of_desrired_product) if mass_of_desrired_product else None
        
        amount_of_catalyst_eval = eval(amount_of_catalyst) if amount_of_catalyst else None
        time_eval = eval(time) if time else None


        # Check if the evaluated values are not None
        #if mass_of_product_eval is None or mass_of_non_benign_reactants_eval is None:
            #return render_template('html', product_list=product_list)

        # CONVERT THE VALUES TO FLOAT
        mass_of_product = float(mass_of_product_eval)
        mass_of_non_benign_reactants = float(mass_of_non_benign_reactants_eval)
        molecular_weight_of_product = float(molecular_weight_of_product_eval)
        
        total_molecular_weight_of_reactants = float(total_molecular_weight_of_reactants_eval)
        yeild = float(yeild_eval)
        amount_of_carbon = float(amount_of_carbon_eval)
        
        total_carbon_reactants = float(total_carbon_reactants_eval)
        mass_of_isolated_product = float(mass_of_isolated_product_eval)
        total_mass_of_reactants = float(total_mass_of_reactants_eval)
        
        total_mass_of_all_solvents_during_reaction = float(total_mass_of_all_solvents_during_reaction_eval)
        total_mass_used = float(total_mass_used_eval)
        mass_of_raw_material = float(mass_of_raw_material_eval)
        
        total_mass_of_solvent = float(total_mass_of_solvent_eval)
        total_mass_of_water = float(total_mass_of_water_eval)
        mass_of_desrired_product = float(mass_of_desrired_product_eval)
        
        amount_of_catalyst = float(amount_of_catalyst_eval)
        time = float(time_eval)


        # FUNCTION CALLING
        emy = calculate_emy(mass_of_product, mass_of_non_benign_reactants)
        ae = calculate_ae(molecular_weight_of_product, total_molecular_weight_of_reactants)
        aef = calculate_aef(yeild, ae)
        
        ce = calculate_ce(amount_of_carbon, total_carbon_reactants)
        rme = calculate_rme(mass_of_isolated_product, total_mass_of_reactants)
        oe = calculate_oe(ae, rme)
        
        pmi = calculate_pmi(total_mass_of_all_solvents_during_reaction, mass_of_product)
        mi = calculate_mi(total_mass_used, mass_of_product)
        mp = calculate_mp(mi)
        
        e_factor = calculate_e_factor(mass_of_raw_material, mass_of_product)
        si = calculate_si(total_mass_of_solvent, mass_of_product)
        wi = calculate_wi(total_mass_of_water, mass_of_product)
        
        ton = calculate_ton(mass_of_desrired_product,amount_of_catalyst)
        tof = calculate_tof(ton, time)
        
        emy = float(emy)
        ae = float(ae)
        aef = float(aef)
        ce = float(ce)
        rme = float(rme)
        oe = float(oe)
        pmi = float(pmi)
        mi = float(mi)
        mp = float(mp)
        e_factor = float(e_factor)
        si = float(si)
        wi = float(wi)
        ton = float(ton)
        tof = float(tof)
        print("total_mass_of_solvent:",type(total_mass_of_solvent))
       
        print("mass_of_product :",mass_of_product)
        print("si :",type(si))
        conn = get_db_connection()
        cursor = conn.cursor()
        
        
        # SAVE TO THE REPORT TABLE
        
        query = "INSERT INTO report(product_name,  emy, ae, aef, ce, rme, oe, pmi, mi, mp, e_factor, si, wi, ton, tof, yeild, time, user) VALUES (%s,  ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3), ROUND(%s, 3),%s, %s, %s)"
        val = (product_name, emy, ae, aef, ce, rme, oe, pmi, mi, mp, e_factor, si, wi, ton, tof, yeild, time, user)
        cursor.execute(query, val)
       
        mysql.conn.commit()
        cursor.close()
        conn.close()

        
        return render_template('html', emy=emy, ae=ae, aef=aef, ce=ce, rme=rme, oe=oe, pmi=pmi, mi=mi, mp=mp, e_factor=e_factor, si=si, wi=wi, ton=ton, tof=tof, product_list=product_list, 
                               product_name=product_name,
                               mass_of_product=mass_of_product,
                               mass_of_non_benign_reactants=mass_of_non_benign_reactants,
                               molecular_weight_of_product=molecular_weight_of_product,
                               total_molecular_weight_of_reactants=total_molecular_weight_of_reactants,
                               yeild=yeild,
                               amount_of_carbon=amount_of_carbon,
                               total_carbon_reactants=total_carbon_reactants,
                               mass_of_isolated_product=mass_of_isolated_product,
                               total_mass_of_reactants=total_mass_of_reactants,
                               total_mass_of_all_solvents_during_reaction=total_mass_of_all_solvents_during_reaction,
                               total_mass_used=total_mass_used,
                               mass_of_raw_material=mass_of_raw_material,
                               total_mass_of_solvent=total_mass_of_solvent,
                               total_mass_of_water=total_mass_of_water,
                               mass_of_desrired_product=mass_of_desrired_product,
                               amount_of_catalyst=amount_of_catalyst,
                               time=time)

    return render_template('html', emy=emy, ae=ae, aef=aef, ce=ce, rme=rme, oe=oe, pmi=pmi, mi=mi, mp=mp, e_factor=e_factor, si=si, wi=wi, ton=ton, tof=tof, product_list=product_list, 
                           product_name=session.get('product_name'),
                           mass_of_product=session.get('mass_of_product'),
                           mass_of_non_benign_reactants=session.get('mass_of_non_benign_reactants'),
                           molecular_weight_of_product=session.get('molecular_weight_of_product'),
                           total_molecular_weight_of_reactants=session.get('total_molecular_weight_of_reactants'),
                           yeild=session.get('yeild'),
                           amount_of_carbon=session.get('amount_of_carbon'),
                           total_carbon_reactants=session.get('total_carbon_reactants'),
                           mass_of_isolated_product=session.get('mass_of_isolated_product'),
                           total_mass_of_reactants=session.get('total_mass_of_reactants'),
                           total_mass_of_all_solvents_during_reaction=session.get('total_mass_of_all_solvents_during_reaction'),
                           total_mass_used=session.get('total_mass_used'),
                           mass_of_raw_material=session.get('mass_of_raw_material'),
                           total_mass_of_solvent=session.get('total_mass_of_solvent'),
                           total_mass_of_water=session.get('total_mass_of_water'),
                           mass_of_desrired_product=session.get('mass_of_desrired_product'),
                           amount_of_catalyst=session.get('amount_of_catalyst'),
                           time=session.get('time'))


# to calculate EMY
def calculate_emy(mass_of_product, mass_of_non_benign_reactants):
    if mass_of_product is None or mass_of_non_benign_reactants is None:
        return None
        
    mass_of_product_expr = sympy.sympify(mass_of_product)
    mass_of_non_benign_reactants_expr = sympy.sympify(mass_of_non_benign_reactants)

    if mass_of_non_benign_reactants_expr != 0:
        emy = (mass_of_product_expr / mass_of_non_benign_reactants_expr) * 100
        return emy
    else:
        return None


# to calculate AE
def calculate_ae(molecular_weight_of_product, total_molecular_weight_of_reactants):
    if molecular_weight_of_product is None or total_molecular_weight_of_reactants is None:
        return None
        
    molecular_weight_of_product_expr = sympy.sympify(molecular_weight_of_product)
    total_molecular_weight_of_reactants_expr = sympy.sympify(total_molecular_weight_of_reactants)

    if total_molecular_weight_of_reactants_expr != 0:
        ae = (molecular_weight_of_product_expr / total_molecular_weight_of_reactants_expr) * 100
        return ae
    else:
        return None
 
 
# to calculate AEF       
def calculate_aef(yeild, ae):
    if yeild is None or ae is None:
        return None
        
    yeild_expr = sympy.sympify(yeild)
    ae_expr = sympy.sympify(ae)
    
    aef = (ae_expr * yeild_expr) / 100
    return aef
 
 
# to calculate CE 
def calculate_ce(amount_of_carbon, total_carbon_reactants):
    if amount_of_carbon is None or total_carbon_reactants is None:
        return None
        
    amount_of_carbon_expr = sympy.sympify(amount_of_carbon)
    total_carbon_reactants_expr = sympy.sympify(total_carbon_reactants)
    
    if total_carbon_reactants_expr != 0:
        ce = (amount_of_carbon_expr / total_carbon_reactants_expr) * 100
        return ce
    else:
        return None
  
  
# to calculate RME  
def calculate_rme(mass_of_isolated_product, total_mass_of_reactants):
        if mass_of_isolated_product is None or total_mass_of_reactants is None:
            return None
   
        mass_of_isolated_product_expr = sympy.sympify(mass_of_isolated_product)
        total_mass_of_reactants_expr = sympy.sympify(total_mass_of_reactants)

        if total_mass_of_reactants_expr != 0:
            rme = (mass_of_isolated_product_expr / total_mass_of_reactants_expr) * 100
            return rme
        else:
            return None
 
 
# to calculate OE  
def calculate_oe(ae, rme):
        if ae is None or rme is None:
            return None
   
        ae_expr = sympy.sympify(ae)
        print("ae:",ae_expr)
        rme_expr = sympy.sympify(rme)
        print("rme:",rme_expr)

        if ae_expr != 0:
            oe = (rme_expr / ae_expr) * 100
            return oe
        else:
            return None
  
  
# to calculate PMI
def calculate_pmi(total_mass_of_all_solvents_during_reaction, mass_of_product):
        if mass_of_product is None or total_mass_of_all_solvents_during_reaction is None:
            return None
   
        total_mass_of_all_solvents_during_reaction_expr = sympy.sympify(total_mass_of_all_solvents_during_reaction)
        mass_of_product_expr = sympy.sympify(mass_of_product)

        if mass_of_product_expr != 0:
            pmi = total_mass_of_all_solvents_during_reaction_expr / mass_of_product_expr
            return pmi
        else:
            return None


# to calculate MI
def calculate_mi(total_mass_used, mass_of_product):
        if mass_of_product is None or total_mass_used is None:
            return None
   
        total_mass_used_expr = sympy.sympify(total_mass_used)
        mass_of_product_expr = sympy.sympify(mass_of_product)

        if mass_of_product_expr != 0:
            mi = total_mass_used_expr / mass_of_product_expr
            return mi
        else:
            return None         
            
            
# to calculate MP
def calculate_mp(mi):
        if mi is None:
            return None
   
        mi_expr = sympy.sympify(mi)

        if mi_expr != 0:
            mp = (1 / mi_expr) * 100
            return mp
        else:
            return None            
  
  
# to calculate EFACTOR
def calculate_e_factor(mass_of_raw_material, mass_of_product):
        if mass_of_product is None or mass_of_raw_material is None:
            return None
   
        mass_of_raw_material_expr = sympy.sympify(mass_of_raw_material)
        mass_of_product_expr = sympy.sympify(mass_of_product)

        if mass_of_product_expr != 0:
            e_factor = mass_of_raw_material_expr / mass_of_product_expr
            return e_factor
        else:
            return None   


# to calculate SI
def calculate_si(total_mass_of_solvent, mass_of_product):
        if mass_of_product is None or total_mass_of_solvent is None:
            return None
   
        total_mass_of_solvent_expr = sympy.sympify(total_mass_of_solvent)
        mass_of_product_expr = sympy.sympify(mass_of_product)

        if mass_of_product_expr != 0:
            si = total_mass_of_solvent_expr / mass_of_product_expr
            return si
        else:
            return None  


# to calculate WI  
def calculate_wi(total_mass_of_water, mass_of_product):
    if mass_of_product is None or total_mass_of_water is None:
        return None

    total_mass_of_water_expr = sympy.sympify(total_mass_of_water)
    mass_of_product_expr = sympy.sympify(mass_of_product)

    if mass_of_product_expr != 0:
        wi = total_mass_of_water_expr / mass_of_product_expr
        return float(wi)  # Return a single value, not a tuple
    else:
        return None  


# to calculate TON    
def calculate_ton(amount_of_desired_product, amount_of_catalyst):
        if amount_of_desired_product is None or amount_of_catalyst is None:
            return None
   
        amount_of_desired_product_expr = sympy.sympify(amount_of_desired_product)
        amount_of_catalyst_expr = sympy.sympify(amount_of_catalyst)

        if amount_of_catalyst_expr != 0:
            ton = amount_of_desired_product_expr / amount_of_catalyst_expr
            return ton
        else:
            return None


# to calculate TOF
def calculate_tof(ton, time):
        if ton is None or time is None:
            return None
        
        ton_expr = sympy.sympify(ton)
        time_expr = sympy.sympify(time)

        if time_expr != 0:
            tof = ton_expr / time_expr
            return tof
        else:
            return None                        
            

# REPORT
@app.route('/downreport')
def downreport():
    return render_template('report.html')
    
    
@app.route('/download/report/pdf', methods=['POST', 'GET'])
def download_report():
    # Get the title from the query parameters
    report_title = request.args.get('title', 'Green Metrics Report')

    now = date.today()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select * from report")
    result = cursor.fetchall()

    pdf = FPDF(orientation='P')
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin

    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, f"{report_title}", align='C') 
    pdf.ln(s)
    pdf.cell(page_width, 0.0, f"Report on Green Metrics Calculations", align='C')  # Changed title here
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date:- ' + str(now), align='L')

    pdf.ln(10)

    pdf.set_font("Courier", '', 10.0)
    col_width = page_width / 16  # Adjusted column width
    pdf.ln(1)
    th = pdf.font_size
    i = 1

    pdf.cell(30, th, "Product", border=1)
    pdf.cell(col_width, th, "EMY", border=1)
    pdf.cell(col_width, th, "AE", border=1)
    pdf.cell(col_width, th, "AEF", border=1)
    pdf.cell(col_width, th, "CE", border=1)
    pdf.cell(col_width, th, "RME", border=1)
    pdf.cell(col_width, th, "OE", border=1)
    pdf.cell(col_width, th, "PMI", border=1)
    pdf.cell(col_width, th, "MI", border=1)
    pdf.cell(col_width, th, "MP", border=1)
    pdf.cell(col_width, th, "EFACTOR", border=1)
    pdf.cell(col_width, th, "SI", border=1)
    pdf.cell(col_width, th, "WI", border=1)
    pdf.cell(col_width, th, "TON", border=1)
    pdf.cell(col_width, th, "TOF", border=1)
    pdf.ln(th)

    for col in result:
        pdf.cell(30, th, col[0], border=1)
        for all_value in col[3:17]:
            if all_value is not None:
                try:
                    all_value = float(all_value)
                    if all_value >= 90:
                        pdf.set_fill_color(0, 255, 0)  # Green
                    elif 80 <= all_value < 90:
                        pdf.set_fill_color(144, 238, 144)  # Light Green
                    elif 70 <= all_value < 80:
                        pdf.set_fill_color(255, 255, 0)  # Yellow
                    elif 60 <= all_value < 70:
                        pdf.set_fill_color(255, 165, 0)  # Orange
                    else:
                        pdf.set_fill_color(255, 99, 71)  # Tomato (Red)

                    pdf.cell(col_width, th, str(all_value), border=1, fill=True)
                except ValueError:
                    # Handle non-numeric values
                    pdf.cell(col_width, th, str(all_value), border=1)
            else:
                # Handle None values
                pdf.cell(col_width, th, "", border=1)  # Fill empty cell with empty string
        pdf.ln(th)

    pdf.ln(10)
    pdf.cell(th)

    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')
    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=green_metrics_report.pdf'

    return response

@app.route('/download/report_product_emy', methods=['POST', 'GET'])
def download_report_emy():
    report_title = request.args.get('title', 'Green Metrics Report')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.emy FROM report")
    print("Query executed.")
    result = cursor.fetchall()
    print("Fetched records:", result)
	
    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."
    pdf = FPDF()
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin

    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, f"Report on Green Metrics EMY Calculations", align='C')
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    current_date = date.today().strftime("%d/%m/%Y")
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)
    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    pdf.ln(1)
    th = pdf.font_size  # Define th here
    i = 1
    #pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "EMY", border=1)
    pdf.ln(th)

    for col in result:
	#pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)
        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)  # Green
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)  # Light Green
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)  # Yellow
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)  # Orange
            else:
                pdf.set_fill_color(255, 99, 71)  # Tomato (Red)

            pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
    pdf.ln(10)
    pdf.cell(th)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')
    cursor.close()
    conn.close()
    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=EMYResults.pdf'
    return response

@app.route('/download/report_product_ae', methods=['POST', 'GET'])
def download_report_ae():
    report_title = request.args.get('title', 'Green Metrics Report')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.ae FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size

    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics AE Calculations", align='C')
    pdf.ln(10)

    current_date = date.today().strftime("%d/%m/%Y")
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date: ' + current_date, align='L')
    pdf.ln(10)

    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size

    pdf.cell(20, th, "S.No", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "AE", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)

        ae_value = float(col[1])
        if ae_value >= 90:
            pdf.set_fill_color(0, 255, 0)  # Green
        elif 80 <= ae_value < 90:
            pdf.set_fill_color(144, 238, 144)  # Light Green
        elif 70 <= ae_value < 80:
            pdf.set_fill_color(255, 255, 0)  # Yellow
        elif 60 <= ae_value < 70:
            pdf.set_fill_color(255, 165, 0)  # Orange
        else:
            pdf.set_fill_color(255, 99, 71)  # Red

        pdf.cell(col_width, th, str(ae_value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')

    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=AEResults.pdf'

    return response


@app.route('/download/report_product_aef', methods=['POST', 'GET'])
def download_report_aef():
    report_title = request.args.get('title', 'Green Metrics Report')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.aef FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size

    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics AEF Calculations", align='C')
    pdf.ln(10)

    current_date = date.today().strftime("%d/%m/%Y")
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date: ' + current_date, align='L')
    pdf.ln(10)

    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size

    pdf.cell(20, th, "S.No", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "AEF", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)

        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)  # Green
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)  # Light Green
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)  # Yellow
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)  # Orange
            else:
                pdf.set_fill_color(255, 99, 71)  # Tomato Red

            pdf.cell(col_width, th, str(value), border=1, fill=True)

        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')

    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=AEFResults.pdf'

    return response


@app.route('/download/report_product_ton', methods=['POST', 'GET'])
def download_report_ton():
    report_title = request.args.get('title', 'Green Metrics Report')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.ton FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin

    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics TON Calculations", align='C')
    pdf.ln(10)

    current_date = date.today().strftime("%d/%m/%Y")
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date: ' + current_date, align='L')
    pdf.ln(10)

    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size

    pdf.cell(20, th, "S.No", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "TON", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)

        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)

            pdf.cell(col_width, th, str(value), border=1, fill=True)

        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')

    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=TONResults.pdf'
    return response

@app.route('/download/report_product_ce', methods=['POST', 'GET'])
def download_report_ce():
    report_title = request.args.get('title', 'Green Metrics Report')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.ce FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin

    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics CE Calculations", align='C')
    pdf.ln(10)

    current_date = date.today().strftime("%d/%m/%Y")
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date: ' + current_date, align='L')
    pdf.ln(10)

    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size

    pdf.cell(20, th, "S.No", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "CE", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)

        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)

            pdf.cell(col_width, th, str(value), border=1, fill=True)

        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')

    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=CEResults.pdf'
    return response

@app.route('/download/report_product_rme', methods=['POST', 'GET'])
def download_report_rme():
    report_title = request.args.get('title', 'Green Metrics Report')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.rme FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics RME Calculations", align='C')
    pdf.ln(10)

    current_date = date.today().strftime("%d/%m/%Y")
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)

    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size

    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "RME", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)
        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)
            pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')

    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=RMEResults.pdf'
    return response


@app.route('/download/report_product_wi', methods=['POST', 'GET'])
def download_report_wi():
    report_title = request.args.get('title', 'Green Metrics Report')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.wi FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, f"{report_title}", align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics WI Calculations", align='C')
    pdf.ln(10)

    current_date = date.today().strftime("%d/%m/%Y")
    pdf.set_font('Times', 'B', 12.0)
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)

    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size

    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "WI", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] if col[0] is not None else ""
        pdf.cell(col_width, th, product_name, border=1)
        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)
            pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')

    cursor.close()
    conn.close()

    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=WIResults.pdf'
    return response


@app.route('/download/report_product_oe', methods=['POST', 'GET'])
def download_report_oe():
    report_title = request.args.get('title', 'Green Metrics Report')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.oe FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, report_title, align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics OE Calculations", align='C')
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    current_date = date.today().strftime("%d/%m/%Y")
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)
    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size
    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "OE", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] or ""
        pdf.cell(col_width, th, product_name, border=1)
        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)
            pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')
    cursor.close()
    conn.close()
    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=OEResults.pdf'
    return response


@app.route('/download/report_product_pmi', methods=['POST', 'GET'])
def download_report_pmi():
    report_title = request.args.get('title', 'Green Metrics Report')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.pmi FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, report_title, align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics PMI Calculations", align='C')
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    current_date = date.today().strftime("%d/%m/%Y")
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)
    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size
    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "PMI", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] or ""
        pdf.cell(col_width, th, product_name, border=1)
        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)
            pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')
    cursor.close()
    conn.close()
    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=PMIResults.pdf'
    return response


@app.route('/download/report_product_mi', methods=['POST', 'GET'])
def download_report_mi():
    report_title = request.args.get('title', 'Green Metrics Report')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.mi FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, report_title, align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics MI Calculations", align='C')
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    current_date = date.today().strftime("%d/%m/%Y")
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)
    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size
    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "MI", border=1)
    pdf.ln(th)

    i = 1
    for col in result:
        pdf.cell(20, th, str(i), border=1)
        product_name = col[0] or ""
        pdf.cell(col_width, th, product_name, border=1)
        for value in col[1:]:
            value = float(value)
            if value >= 90:
                pdf.set_fill_color(0, 255, 0)
            elif 80 <= value < 90:
                pdf.set_fill_color(144, 238, 144)
            elif 70 <= value < 80:
                pdf.set_fill_color(255, 255, 0)
            elif 60 <= value < 70:
                pdf.set_fill_color(255, 165, 0)
            else:
                pdf.set_fill_color(255, 99, 71)
            pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf.ln(10)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- end of report -', align='C')
    cursor.close()
    conn.close()
    response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment;filename=MIResults.pdf'
    return response


@app.route('/download/report_product_mp', methods=['POST', 'GET'])
def download_report_mp():
	report_title = request.args.get('title', 'Green Metrics Report')
	conn = get_db_connection()
    cursor = conn.cursor()
	cursor.execute("SELECT report.product_name, report.mp FROM report")
	result = cursor.fetchall()

	if not result:
		cursor.close()
        conn.close()
		return "No data found for the selected product."

	pdf = FPDF()
	pdf.add_page()

	page_width = pdf.w - 2 * pdf.l_margin

	pdf.set_font('Times', 'B', 14.0)
	s = pdf.font_size
	pdf.cell(page_width, 0.0, f"{report_title}", align='C')
	pdf.ln(s)
	pdf.cell(page_width, 0.0, f"Report on Green Metrics MP Calculations", align='C')
	pdf.ln(10)
	pdf.set_font('Times', 'B', 12.0)
	current_date = date.today().strftime("%d/%m/%Y")
	pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
	pdf.ln(10)
	pdf.set_font("Courier", '', 12.0)
	col_width = page_width / 3
	pdf.ln(1)
	th = pdf.font_size  # Define th here
	i = 1

	pdf.cell(20, th, "sNo", border=1)
	pdf.cell(col_width, th, "Product", border=1)
	pdf.cell(col_width, th, "MP", border=1)
	pdf.ln(th)

	for col in result:
		pdf.cell(20, th, str(i), border=1)
		product_name = col[0] if col[0] is not None else ""
		pdf.cell(col_width, th, product_name, border=1)
		for value in col[1:]:
			value = float(value)
			if value >= 90:
				pdf.set_fill_color(0, 255, 0)  # Green
			elif 80 <= value < 90:
				pdf.set_fill_color(144, 238, 144)  # Light Green
			elif 70 <= value < 80:
				pdf.set_fill_color(255, 255, 0)  # Yellow
			elif 60 <= value < 70:
				pdf.set_fill_color(255, 165, 0)  # Orange
			else:
				pdf.set_fill_color(255, 99, 71)  # Tomato (Red)
			pdf.cell(col_width, th, str(value), border=1, fill=True)
		pdf.ln(th)
	pdf.ln(10)
	pdf.cell(th)

	pdf.set_font('Times', '', 10.0)
	pdf.cell(page_width, 0.0, '- end of report -', align='C')

	cursor.close()
    conn.close()
	response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
	response.headers['Content-Disposition'] = 'attachment;filename=MPResults.pdf'

	return response


@app.route('/download/report_product_efact', methods=['POST', 'GET'])
def download_report_efact():
	report_title = request.args.get('title', 'Green Metrics Report')
	conn = get_db_connection()
    cursor = conn.cursor()
	cursor.execute("SELECT report.product_name, report.e_factor FROM report")
	result = cursor.fetchall()

	if not result:
		cursor.close()
        conn.close()
		return "No data found for the selected product."

	pdf = FPDF()
	pdf.add_page()

	page_width = pdf.w - 2 * pdf.l_margin

	pdf.set_font('Times', 'B', 14.0)
	s = pdf.font_size
	pdf.cell(page_width, 0.0, f"{report_title}", align='C')
	pdf.ln(s)
	pdf.cell(page_width, 0.0, f"Report on Green Metrics E-Factor Calculations", align='C')
	pdf.ln(10)
	pdf.set_font('Times', 'B', 12.0)
	current_date = date.today().strftime("%d/%m/%Y")
	pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
	pdf.ln(10)
	pdf.set_font("Courier", '', 12.0)
	col_width = page_width / 3
	pdf.ln(1)
	th = pdf.font_size  # Define th here
	i = 1

	pdf.cell(20, th, "sNo", border=1)
	pdf.cell(col_width, th, "Product", border=1)
	pdf.cell(col_width, th, "E-Factor", border=1)
	pdf.ln(th)

	for col in result:
		pdf.cell(20, th, str(i), border=1)
		product_name = col[0] if col[0] is not None else ""
		pdf.cell(col_width, th, product_name, border=1)
		for value in col[1:]:
			value = float(value)
			if value >= 90:
				pdf.set_fill_color(0, 255, 0)  # Green
			elif 80 <= value < 90:
				pdf.set_fill_color(144, 238, 144)  # Light Green
			elif 70 <= value < 80:
				pdf.set_fill_color(255, 255, 0)  # Yellow
			elif 60 <= value < 70:
				pdf.set_fill_color(255, 165, 0)  # Orange
			else:
				pdf.set_fill_color(255, 99, 71)  # Tomato (Red)

			pdf.cell(col_width, th, str(value), border=1, fill=True)
		pdf.ln(th)
	pdf.ln(10)
	pdf.cell(th)

	pdf.set_font('Times', '', 10.0)
	pdf.cell(page_width, 0.0, '- end of report -', align='C')

	cursor.close()
    conn.close()
	response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
	response.headers['Content-Disposition'] = 'attachment;filename=E-FACTORResults.pdf'

	return response


@app.route('/download/report_product_si', methods=['POST', 'GET'])
def download_report_si():
	report_title = request.args.get('title', 'Green Metrics Report')
	conn = get_db_connection()
    cursor = conn.cursor()
	cursor.execute("SELECT report.product_name, report.si FROM report")
	result = cursor.fetchall()

	if not result:
		cursor.close()
        conn.close()
		return "No data found for the selected product."

	pdf = FPDF()
	pdf.add_page()

	page_width = pdf.w - 2 * pdf.l_margin

	pdf.set_font('Times', 'B', 14.0)
	s = pdf.font_size
	pdf.cell(page_width, 0.0, f"{report_title}", align='C')
	pdf.ln(s)
	pdf.cell(page_width, 0.0, f"Report on Green Metrics SI Calculations", align='C')
	pdf.ln(10)
	pdf.set_font('Times', 'B', 12.0)
	current_date = date.today().strftime("%d/%m/%Y")
	pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
	pdf.ln(10)
	pdf.set_font("Courier", '', 12.0)
	col_width = page_width / 3
	pdf.ln(1)
	th = pdf.font_size  # Define th here
	i = 1

	pdf.cell(20, th, "sNo", border=1)
	pdf.cell(col_width, th, "Product", border=1)
	pdf.cell(col_width, th, "SI", border=1)
	pdf.ln(th)

	for col in result:
		pdf.cell(20, th, str(i), border=1)
		product_name = col[0] if col[0] is not None else ""
		pdf.cell(col_width, th, product_name, border=1)
		for value in col[1:]:
			value = float(value)
			if value >= 90:
				pdf.set_fill_color(0, 255, 0)  # Green
			elif 80 <= value < 90:
				pdf.set_fill_color(144, 238, 144)  # Light Green
			elif 70 <= value < 80:
				pdf.set_fill_color(255, 255, 0)  # Yellow
			elif 60 <= value < 70:
				pdf.set_fill_color(255, 165, 0)  # Orange
			else:
				pdf.set_fill_color(255, 99, 71)  # Tomato (Red)
			pdf.cell(col_width, th, str(value), border=1, fill=True)
		pdf.ln(th)

	pdf.ln(10)
	pdf.cell(th)

	pdf.set_font('Times', '', 10.0)
	pdf.cell(page_width, 0.0, '- end of report -', align='C')

	cursor.close()
    conn.close()
	response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
	response.headers['Content-Disposition'] = 'attachment;filename=SIResults.pdf'

	return response


@app.route('/download/report_product_tof', methods=['POST', 'GET'])
def download_report_tof():
	report_title = request.args.get('title', 'Green Metrics Report')
	conn = get_db_connection()
    cursor = conn.cursor()
	cursor.execute("SELECT report.product_name, report.tof FROM report")
	result = cursor.fetchall()

	if not result:
		cursor.close()
        conn.close()
		return "No data found for the selected product."

	pdf = FPDF()
	pdf.add_page()

	page_width = pdf.w - 2 * pdf.l_margin

	pdf.set_font('Times', 'B', 14.0)
	s = pdf.font_size
	pdf.cell(page_width, 0.0, f"{report_title}", align='C')
	pdf.ln(s)
	pdf.cell(page_width, 0.0, f"Report on Green Metrics TOF Calculations", align='C')
	pdf.ln(10)
	pdf.set_font('Times', 'B', 12.0)
	current_date = date.today().strftime("%d/%m/%Y")
	pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
	pdf.ln(10)

	pdf.set_font("Courier", '', 12.0)
	col_width = page_width / 3
	pdf.ln(1)
	th = pdf.font_size  # Define th here
	i = 1

	pdf.cell(20, th, "sNo", border=1)
	pdf.cell(col_width, th, "Product", border=1)
	pdf.cell(col_width, th, "TOF", border=1)
	pdf.ln(th)

	for col in result:
		pdf.cell(20, th, str(i), border=1)
		product_name = col[0] if col[0] is not None else ""
		pdf.cell(col_width, th, product_name, border=1)
		tof_value = col[1]
		if tof_value is not None:
			try:
				tof_value = float(tof_value)
				if tof_value >= 90:
					pdf.set_fill_color(0, 255, 0)  # Green
				elif 80 <= tof_value < 90:
					pdf.set_fill_color(144, 238, 144)  # Light Green
				elif 70 <= tof_value < 80:
					pdf.set_fill_color(255, 255, 0)  # Yellow
				elif 60 <= tof_value < 70:
					pdf.set_fill_color(255, 165, 0)  # Orange
				else:
					pdf.set_fill_color(255, 99, 71)  # Tomato (Red)
				pdf.cell(col_width, th, str(tof_value), border=1, fill=True)
			except ValueError:
				pdf.cell(col_width, th, str(tof_value), border=1)
		else:
			pdf.cell(col_width, th, "", border=1)  # Fill empty cell with empty string
		i += 1
		pdf.ln(th)

	pdf.ln(10)
	pdf.cell(th)
	
	pdf.set_font('Times', '', 10.0)
	pdf.cell(page_width, 0.0, '- end of report -', align='C')

	cursor.close()
    conn.close()
	response = Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf')
	response.headers['Content-Disposition'] = 'attachment;filename=TOFResults.pdf'

	return response

@app.route('/download/report_product_efact', methods=['POST', 'GET'])
def download_report_efact():
    report_title = request.args.get('title', 'Green Metrics Report')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.e_factor FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, report_title, align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics E-Factor Calculations", align='C')
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    current_date = date.today().strftime("%d/%m/%Y")
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)
    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size
    i = 1
    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "E-Factor", border=1)
    pdf.ln(th)

    for col in result:
        pdf.cell(20, th, str(i), border=1)
        pdf.cell(col_width, th, col[0] or "", border=1)
        value = float(col[1])
        color_by_value(pdf, value)
        pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf_footer(pdf, page_width)
    cursor.close()
    conn.close()
    return make_pdf_response(pdf, "E-FACTORResults.pdf")


@app.route('/download/report_product_si', methods=['POST', 'GET'])
def download_report_si():
    report_title = request.args.get('title', 'Green Metrics Report')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT report.product_name, report.si FROM report")
    result = cursor.fetchall()

    if not result:
        cursor.close()
        conn.close()
        return "No data found for the selected product."

    pdf = FPDF()
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin
    pdf.set_font('Times', 'B', 14.0)
    s = pdf.font_size
    pdf.cell(page_width, 0.0, report_title, align='C')
    pdf.ln(s)
    pdf.cell(page_width, 0.0, "Report on Green Metrics SI Calculations", align='C')
    pdf.ln(10)
    pdf.set_font('Times', 'B', 12.0)
    current_date = date.today().strftime("%d/%m/%Y")
    pdf.cell(page_width, 0.0, 'Date:- ' + current_date, align='L')
    pdf.ln(10)
    pdf.set_font("Courier", '', 12.0)
    col_width = page_width / 3
    th = pdf.font_size
    i = 1
    pdf.cell(20, th, "sNo", border=1)
    pdf.cell(col_width, th, "Product", border=1)
    pdf.cell(col_width, th, "SI", border=1)
    pdf.ln(th)

    for col in result:
        pdf.cell(20, th, str(i), border=1)
        pdf.cell(col_width, th, col[0] or "", border=1)
        value = float(col[1])
        color_by_value(pdf, value)
        pdf.cell(col_width, th, str(value), border=1, fill=True)
        pdf.ln(th)
        i += 1

    pdf_footer(pdf, page_width)
    cursor.close()
    conn.close()
    return make_pdf_response(pdf, "SIResults.pdf")



#graphs
@app.route('/graph')
def graph():
    user = session.get('username')
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT DISTINCT product_name, emy, ae, aef, ce, rme, oe, mp, pmi, mi, e_factor, si, wi, ton, tof FROM report WHERE user = %s", (user,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if data:
        product_names = [row[0] for row in data]
        metrics = ['EMY', 'AE', 'AEF', 'CE', 'RME', 'OE', 'MP', 'PMI', 'MI', 'E-FACTOR', 'SI', 'WI', 'TON', 'TOF']
        values = {metric: [float(row[i]) for row in data] for i, metric in enumerate(metrics, start=1)}

        # Plotting graphs for each metric
        plots = {}
        for metric in metrics:
            plt.figure(figsize=(10, 6), dpi=200)  # Increase DPI for HD resolution
            plt.bar(product_names, values[metric], color='skyblue')
            plt.ylim(0, 100)
            plt.xlabel('Product Names', fontsize=12)
            plt.ylabel(f'{metric} (%)', fontsize=12)
            plt.title(f'{metric} Values for All Products', fontsize=14, fontweight='bold')
            plt.xticks(rotation=45, fontsize=8)
            plt.grid(axis='y', linestyle='--', alpha=0.5)

            # Annotate each bar with its value
            for i, value in enumerate(values[metric]):
                plt.text(i, value + 2, f'{value:.0f}%', ha='center', va='bottom', fontsize=8)

            # Save plot to BytesIO object and encode it to base64
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plots[metric] = plot_url

        return render_template('graph.html', plots=plots)
    else:
        return "No data found."
        
        

def get_dropdown_options():
    user = session.get('username')
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT product_name, yeild, time FROM report WHERE user = %s",(user,))
    data = cursor.fetchall()
    
    conn.close()
    return data

@app.route('/graph1',methods=['GET', 'POST'])
def graph1():
    if request.method == 'POST':
        
        composite_key = request.form.get('composite_key')
        print("composite_key",composite_key)
        selected_product, yeild, time = composite_key.split(',')

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute(f"SELECT * FROM report WHERE product_name = '{selected_product}' AND yeild = {yeild} AND time = {time}")
        row = cursor.fetchone()
        conn.close()

        if row:
            # Modify the metrics here
            metrics = ['EMY (%)', 'AE (%)', 'AEf (%)', 'CE (%)', 'RME (%)', 'OE (%)', 'MP (%)', 'PMI(g/g)', 'MI(g/g)', 'E-FACTOR(g/g)', 'SI(g/g)', 'WI(g/g)', 'TON', 'TOF(min-1)']
            values = [float(row[i]) for i in range(1, len(metrics) + 1)]

            plt.figure(figsize=(10, 6))
            bars = plt.bar(metrics, values, color='skyblue')
            plt.ylim(0, 100)
            plt.xlabel('Metrics')
            plt.ylabel('Values')
            plt.title(f'Metrics vs Values for Product: {selected_product}')
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            # Annotate each bar with its value
            for bar, value in zip(bars, values):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{value:.2f}', ha='center', va='bottom')

            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            plt.close()  # Close the plot to avoid memory leaks

            return render_template('graph1.html', data=get_dropdown_options(), selected_product=selected_product, plot_url=plot_url)

    return render_template('graph1.html', data=get_dropdown_options())



if __name__ == '__main__':
    app.run(debug=True)



