import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import json
from dotenv import load_dotenv


# Cargar variables desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configura una clave secreta para gestionar las sesiones
app.secret_key = os.getenv('SECRET_KEY') 

# Obtener la contraseña desde el .env
PROFESOR_PASSWORD = os.getenv('PROFESOR_PASSWORD')

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',  # Cambia esto si es necesario
        user='root',  # Cambia esto a tu usuario
        password='9874123asd',  # Cambia esto a tu contraseña
        database='ingles'  # Cambia esto a tu base de datos
    )
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT DISTINCT tipo_palabra FROM palabras')  # Cambiado a tipo_palabra
    tipos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', tipos=tipos)

@app.route('/<tipo>')
def listar_palabras(tipo):
    print(f"Tipo recibido: {tipo}")
    
    # Lista de tipos válidos (ajustada a lo que tienes en la base de datos)
    tipos_validos = ['sustantivos', 'verbos', 'adjetivos', 'adverbios', 'conectores', 'expresiones', 'otros']
    
    # Verificar si el tipo es válido
    if tipo not in tipos_validos:
        print(f"Tipos válidos: {tipos_validos}")  # Imprimir tipos válidos para depuración
        return f"Tipo no válido. Tipos válidos son: {tipos_validos}", 404  # Manejo de tipos no válidos
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ejecutar la consulta con el tipo
    cursor.execute('SELECT * FROM palabras WHERE tipo_palabra = %s', (tipo,))
    palabras = cursor.fetchall()
    print(palabras)
    
    cursor.close()
    conn.close()
    
    # Pasar las palabras al template
    return render_template('listar_palabras.html', palabras=palabras, tipo=tipo)


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/palabra/<int:palabra_id>', methods=['GET', 'POST'])
def detalles_palabra(palabra_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM palabras WHERE id_palabra = %s', (palabra_id,))
    palabra = cursor.fetchone()

    if not palabra:
        cursor.close()
        conn.close()
        return "Palabra no encontrada", 404

    # Obtener traducciones y oraciones relacionadas
    cursor.execute('SELECT * FROM traducciones WHERE id_palabra = %s', (palabra_id,))
    traducciones = cursor.fetchall()

    cursor.execute('SELECT * FROM oraciones WHERE id_palabra = %s', (palabra_id,))
    oraciones = cursor.fetchall()

    cursor.close()  # Asegúrate de cerrar el cursor aquí
    conn.close()    # Cierra la conexión después de todas las consultas

    return render_template('detalles_palabra.html', palabra=palabra, traducciones=traducciones, oraciones=oraciones)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/profesor', methods=['GET', 'POST'])
def profesor():
    message = None  # Variable para almacenar el mensaje de éxito o error
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            palabra = (request.form.get('palabra')).lower()
            tipo_palabra = (request.form.get('tipo_palabra')).lower()
            imagen = (request.form.get('imagen')).lower()

            # Verifica que todos los campos estén presentes
            if not palabra or not tipo_palabra:
                raise ValueError("La palabra y el tipo de palabra son obligatorios.")
            
            # Inserta la nueva palabra en la base de datos
            cursor.execute('INSERT INTO palabras (palabra, tipo_palabra, imagen) VALUES (%s, %s, %s)', (palabra, tipo_palabra, imagen))
            conn.commit()
            message = f'Palabra "{palabra}" creada exitosamente.'
        except Exception as e:
            message = f'No se pudo cargar la nueva palabra: {str(e)}'
        finally:
            cursor.close()
            conn.close()

    return render_template('profesor.html', message=message)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/editar_palabra/<int:palabra_id>', methods=['GET', 'POST'])
def editar_palabra(palabra_id):
    conn = get_db_connection()  
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Eliminar traducción si se solicita
        if request.form.get('eliminar_traduccion'):
            id_traduccion = request.form['eliminar_traduccion']
            print(f'ID Traducción a eliminar: {id_traduccion}')  # Para depuración
            cursor.execute('DELETE FROM traducciones WHERE id_traduccion = %s', (id_traduccion,))
            conn.commit()

        # Eliminar oración si se solicita
        if request.form.get('eliminar_oracion'):
            id_oracion = request.form['eliminar_oracion']
            print(f'ID Oración a eliminar: {id_oracion}')  # Para depuración
            cursor.execute('DELETE FROM oraciones WHERE id_oracion = %s', (id_oracion,))
            conn.commit()

        # Actualizar la palabra
        palabra = (request.form.get('palabra')).lower()
        tipo_palabra = request.form.get('tipo_palabra').lower()
        imagen = request.form.get('imagen').lower()

        cursor.execute('UPDATE palabras SET palabra = %s, tipo_palabra = %s, imagen = %s WHERE id_palabra = %s',
                        (palabra, tipo_palabra, imagen, palabra_id))
        conn.commit()

        # Manejo de nuevas traducciones
        nueva_traduccion = (request.form.get('nueva_traduccion')).lower()
        if nueva_traduccion:
            cursor.execute('INSERT INTO traducciones (id_palabra, traduccion) VALUES (%s, %s)', (palabra_id, nueva_traduccion))
            conn.commit()

        # Manejo de nuevas oraciones
        nueva_oracion_ingles = ((request.form.get('nueva_oracion_ingles')).lower()).capitalize()
        nueva_oracion_espaniol = ((request.form.get('nueva_oracion_espaniol')).lower()).capitalize()
        if nueva_oracion_ingles and nueva_oracion_espaniol:
            cursor.execute('INSERT INTO oraciones (id_palabra, oracion_ingles, oracion_espaniol) VALUES (%s, %s, %s)',
                            (palabra_id, nueva_oracion_ingles, nueva_oracion_espaniol))
            conn.commit()

        cursor.close()
        conn.close()
        
        return redirect(url_for('detalles_palabra', palabra_id=palabra_id))

    # Consultar la palabra y sus traducciones y oraciones
    cursor.execute('SELECT * FROM palabras WHERE id_palabra = %s', (palabra_id,))
    palabra = cursor.fetchone()
    cursor.execute('SELECT * FROM traducciones WHERE id_palabra = %s', (palabra_id,))
    traducciones = cursor.fetchall()
    cursor.execute('SELECT * FROM oraciones WHERE id_palabra = %s', (palabra_id,))
    oraciones = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('editar_palabra.html', palabra=palabra, traducciones=traducciones, oraciones=oraciones)


#?????????????????????????????????????????????????????????????????????????????

if __name__ == '__main__':
    app.run(debug=True)

