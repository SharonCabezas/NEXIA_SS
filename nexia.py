import pandas as pd
import os
from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import pickle
import streamlit_authenticator as stauth
from streamlit import session_state as ss
from streamlit_pdf_viewer import pdf_viewer
from datetime import datetime
from streamlit_calendar import calendar
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import base64


st.set_page_config(
    page_title='NEXIA',
    page_icon='icon.png'
)

users = pd.read_excel('usuarios.xlsx')
doctors = pd.read_excel('usuarios_doc.xlsx')

def center_image(image):
    st.image(image, use_column_width='always', output_format='auto')

def authenticate(username, password):
    user_data_patient = users.loc[users['CURP'] == username]
    if not user_data_patient.empty and user_data_patient.iloc[0]['Contraseña'] == password:
        return user_data_patient.iloc[0], 'paciente'

    user_data_doctor = doctors.loc[doctors['Cédula profesional'] == username]
    if not user_data_doctor.empty and user_data_doctor.iloc[0]['Contraseña'] == password:
        return user_data_doctor.iloc[0], 'doctor'

    return None, None

def login_page():
    image = Image.open('Logo NEXIA (1).png')
    resized_image2 = image.resize((1000, 1000))
    center_image(resized_image2)

    st.markdown(
    """
        <div style="display: flex; flex-direction: column; align-items: center;">
        <h1>Iniciar sesión</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    username = st.text_input('ID de Usuario (CURP o Cedula Profesional)')
    password = st.text_input('Contraseña', type='password')
    if st.button('Iniciar sesión'):
        user_data, user_type = authenticate(username, password)
        if user_data is not None:
            st.session_state.user_data = user_data
            st.session_state.user_type = user_type
            st.success('Inicio de sesión exitosa')
            return True
        else:
            st.error('Credenciales incorrectas')
    return False

if not st.session_state.get('authenticated', False):
    if not login_page():
        st.stop()
    else:
        st.session_state.authenticated = True
        st.experimental_rerun()

image_sidebar = Image.open('Logo NEXIA (1).png')
st.sidebar.image(image_sidebar)

user_data = st.session_state.get('user_data', None)
user_type = st.session_state.get('user_type', None)

with st.sidebar:
    if user_type == 'paciente':
        selected = option_menu(
            menu_title=None,
            options=['Perfil', 'Cita', 'Medicamentos', 'Vacunas', 'Alergias', 'Exámenes de laboratorio', 'Ruta quirúrgica', 'Imágenes médicas', 'Registro de síntomas', 'Diagnósticos médicos', 'Buscar doctores'],
            icons=['person', 'book', 'capsule', 'droplet', 'flower1', 'clipboard2-pulse-fill', 'heart-pulse', 'card-image', 'check2-circle', 'activity','person-lines-fill'],
            orientation='vertical',
            menu_icon=None,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": '#84D9C1'},
            }
        )

    elif user_type == 'doctor':
        selected = option_menu(
            menu_title=None,
            options=['Doctor', 'Pacientes', 'Citas' , 'Buscar doctor'],
            icons=['person', 'file-medical', 'calendar','person-lines-fill'],
            orientation='vertical',
            menu_icon=None,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": '#84D9C1'},
            }
        )

if selected == 'Buscar doctores':
  usuarios_doc = pd.read_excel("usuarios_doc.xlsx")

  def display_doctor_info(doctor_info, image_path):
    nombre = doctor_info['Nombre(s)']
    ap_paterno = doctor_info['Apellido paterno']
    ap_materno = doctor_info['Apellido materno']
    doc_rol = doctor_info['Rol del usuario']
    especialidad = doctor_info['Especialidad']
    subespecialidad = doctor_info['Sub-especialidad']
    clues = doctor_info['Clave única de establecimiento de salud']
    celular = doctor_info['Celular']
    id = doctor_info['ID']

    st.subheader(f'{nombre} {ap_paterno} {ap_materno}')

    col1, col2, col3 = st.columns(3)

    with col2:
      st.metric('Rol de usuario', doc_rol)
      st.metric("Especialidad", especialidad)
      st.metric("Sub-especialidad", subespecialidad)

    with col3:
      st.metric('ID', id)
      st.metric("CLUES", clues)
      st.metric("Celular", celular)

    try:
      image = Image.open(image_path)
      col1.image(image, caption=f'Dr. {nombre} {ap_paterno} {ap_materno}')
    except FileNotFoundError:
      col1.write('No hay imagen registrada.')

  st.title("Buscar Doctores")
  st.subheader('Especialidad o ID')
  especialidades = usuarios_doc['Especialidad'].unique()

  st.info("Busque el doctor por su especialidad o por su ID.")

  col1, col2 = st.columns(2)

  with col1:
        especialidad_select = st.selectbox("Seleccione una especialidad:", especialidades)

  with col2:
        id_text = st.text_input("Ingrese el ID del doctor (opcional):")


  if id_text:
        filtered_doctors = usuarios_doc[usuarios_doc['ID'].astype(str) == id_text]
  else:
        filtered_doctors = usuarios_doc[usuarios_doc['Especialidad'] == especialidad_select]

  if not filtered_doctors.empty:
        for index, doctor_info in filtered_doctors.iterrows():
            doctor_id = doctor_info['ID']
            image_path = f'{doctor_id}.jpeg'
            display_doctor_info(doctor_info, image_path)
  else:
        st.error("No se encontraron doctores con la especialidad y/o ID seleccionados.")


def insert_cita_to_excel(nombre, nombrec, especialidad, date, cita,motivo,hospital):
    file_path = "BD Citas.csv"

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=['Doctor','Paciente','Especialidad', 'Fecha', 'Cita','Motivo Cita','Hospital' ,'Estado'])

    new_data = pd.DataFrame([[nombre, nombrec, especialidad, date,cita, motivo, hospital, 'Pendiente']],
                            columns=['Doctor','Paciente','Especialidad', 'Fecha', 'Cita','Motivo Cita','Hospital' , 'Estado'])

    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(file_path, index=False)

def get_citas_from_excel(nombre_medico):
    file_path = "BD Citas.csv"

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        citas = df[df['Doctor'] == nombre_medico]
        return citas
    else:
        df=pd.DataFrame(columns=['Doctor','Paciente','Especialidad', 'Fecha','Cita', 'Motivo Cita','Hospital' , 'Estado'])
        return df

def update_cita_estado(citas, index, new_state):
    citas.loc[index, 'Estado'] = new_state
    citas.to_csv('BD Citas.csv', index=False)

if selected == 'Cita':
    st.title('Agendar citas')
    st.header('Formulario de Agendar Cita')
    Paciente = f"{user_data['Nombre(s)']} {user_data['Apellido paterno']} {user_data['Apellido materno']}"
    cita = pd.read_csv("BD Citas.csv")
    dfcita = cita.loc[cita["Paciente"] == Paciente]
    st.dataframe(dfcita)
    Doctor = st.selectbox("Médico: ", [f"{n} {ap} {am}" for n, ap, am in zip(doctors['Nombre(s)'], doctors['Apellido paterno'], doctors['Apellido materno'])])

    with st.form("Cita"):
        Imagen,Texto,Forms= st.columns(3)
        with Imagen:
            doctors['Nombre Completo'] = doctors['Nombre(s)'] + ' ' + doctors['Apellido paterno'] + ' ' + doctors['Apellido materno']
            doctor_id = doctors.loc[doctors['Nombre Completo'] == Doctor, 'ID'].values[0]
            ima=doctor_id+".jpeg"
            st.image(ima)
        with Texto:
            st.write(Doctor)
            doctors['Nombre Completo'] = doctors['Nombre(s)'] + ' ' + doctors['Apellido paterno'] + ' ' + doctors['Apellido materno']
            doctor_esp = doctors.loc[doctors['Nombre Completo'] == Doctor, 'Especialidad'].values[0]
            st.write(doctor_esp)
            filtered_hospitals = doctors.loc[doctors['Nombre Completo'] == Doctor, 'Clave única de establecimiento de salud'].unique()
            Hospital = st.selectbox("Hospital: ", filtered_hospitals)
        with Forms:
            date = st.date_input("Fecha", value=pd.Timestamp.today())
            CITA = st.selectbox("Motivo de cita: ", ['Primera cita', 'Seguimiento'])
            Motivo=st.text_input("Ingrese el motivo de la cita")

        submitted = st.form_submit_button("Agendar cita")
        if submitted:
            st.session_state['Doctor'] = Doctor
            st.session_state['Paciente'] = Paciente
            st.session_state['DATE'] = date
            st.session_state['CITA'] = CITA
            st.session_state['Motivo'] = Motivo
            st.session_state['Hospital'] = Hospital
            st.session_state['cita_agendada'] = True

            insert_cita_to_excel(Doctor, Paciente,doctor_esp,date,CITA, Motivo,Hospital)
            if CITA == 'Primera cita':
                st.success("¡Gracias por agendar su primera cita😀​, espere a que el doctor confirme o rechace la solicitud!")
                cita = pd.read_csv("BD Citas.csv")
                dfcita = cita.loc[cita["Paciente"] == Paciente]
                st.dataframe(dfcita)
            if CITA == 'Seguimiento':
                st.success("¡Gracias por volver😀​, espere a que el doctor confirme o rechace la solicitud!")
                cita = pd.read_csv("BD Citas.csv")
                dfcita = cita.loc[cita["Paciente"] == Paciente]
                st.dataframe(dfcita)

if selected == 'Citas' and user_type == 'doctor':
    st.title('Citas Agendadas')
    st.info('Haga doble click si quiere aceptar o rechazar la cita.')
    NOMBRE_MEDICO = f"{user_data['Nombre(s)']} {user_data['Apellido paterno']} {user_data['Apellido materno']}"
    citas = get_citas_from_excel(NOMBRE_MEDICO)

    if not citas.empty:
        st.subheader(f"Citas para {NOMBRE_MEDICO}")

        st.dataframe(citas)
        for index, cita in citas.iterrows():
            estado = cita['Estado']
            if estado == 'Pendiente':
                accepted = st.button(f"Aceptar Cita {index + 1}")
                rejected = st.button(f"Rechazar Cita {index + 1}")
                if accepted:
                    update_cita_estado(citas, index, 'Aceptada')
                elif rejected:
                    update_cita_estado(citas, index, 'Rechazada')
            else:
                st.success(f"Estado: {estado}")

if selected == 'Perfil':
    usuarios_pacientes = pd.read_excel("usuarios.xlsx")
    selected = st.session_state.get('selected',None)
    st.title(f'Perfil')
    patient_data = st.session_state.get('user_data',None)

    if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:

        nombre = patient_info['Nombre(s)'].iloc[0]
        ap_paterno = patient_info['Apellido paterno'].iloc[0]
        ap_materno = patient_info['Apellido materno'].iloc[0]
        id = patient_info['ID'].iloc[0]

        st.subheader(f'Bienvenido, {nombre} {ap_paterno} {ap_materno}')

        col1, col2, col3 = st.columns(3)

        with col2.container():
                col2.metric('ID', user_data['ID'])
                col2.metric("Edad", user_data['Edad'])
                col2.metric("Tipo de sangre", user_data['Tipo de sangre'])
                col2.metric("Altura", user_data['Altura'])
                col2.metric("Peso", user_data['Peso'])

        with col3.container():
            col3.metric('Género', user_data['Género'])
            col3.metric('Alergias', user_data['Alergias'])
            col3.metric('Medicación actual', user_data['Medicación actual'])
            col3.metric('Donante de organos', user_data['Donante de organos'])
            col3.metric('Contacto de emergencia', user_data['Contacto de emergencia'])

        try:
            path = f'{id}.jpeg'
            print("Ruta de la imagen:", path)
            image = Image.open(path)
            col1.image(image, caption=f'Paciente')

        except FileNotFoundError:
            col1.write('No hay imagen registrada.')

      st.subheader('Más información:')
      st.info('Haz clic en los desplegables para ver la información correspondiente.')
      with st.expander("Nombre completo"):
        st.write(f'Nombre(s): {user_data["Nombre(s)"]}')
        st.write(f'Apellido paterno: {user_data["Apellido paterno"]}')
        st.write(f'Apellido materno: {user_data["Apellido materno"]}')
        st.write(f'Género: {user_data["Género"]}')
        st.write(f'Día de nacimiento: {user_data["Día de nacimiento"]}')
        st.write(f'Mes de nacimiento: {user_data["Mes de nacimiento"]}')
        st.write(f'Año de nacimiento: {user_data["Año de nacimiento"]}')

      with st.expander("Datos generales"):
        st.write(f'Ocupación: {user_data["Ocupación"]}')
        st.write(f'Estado civil: {user_data["Estado civil"]}')
        st.write(f'Grupo étnico: {user_data["Grupo étnico"]}')
        st.write(f'Religión: {user_data["Religión"]}')
        st.write(f'Vivienda: {user_data["Vivienda"]}')

      with st.expander("Domicilio"):
        st.write(f'Calle: {user_data["Calle"]}')
        st.write(f'Número ext: {user_data["Número ext"]}')
        st.write(f'Número int: {user_data["Número int"]}')
        st.write(f'Estado: {user_data["Estado"]}')
        st.write(f'Municipio: {user_data["Municipio"]}')
        st.write(f'Colonia: {user_data["Colonia"]}')
        st.write(f'Código postal: {user_data["Código postal"]}')
        st.write(f'Correo: {user_data["Correo"]}')
        st.write(f'Celular: {user_data["Celular"]}')
        st.write(f'Teléfono: {user_data["Teléfono"]}')
                        
if selected == 'Exámenes de laboratorio':
    usuarios_pacientes = pd.read_excel("usuarios.xlsx")
    patient_data = st.session_state.get('user_data', None)
    
    def get_exam_from_csv(id):
        file_path = "examenes_laboratorio.csv"

        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            citas = df[df['ID del paciente'] == id]
            return citas
        else:
            df = pd.DataFrame(columns=['ID del paciente', 'ID del doctor', 'Título del examen', 'Breve descripción'])
            return df

    if patient_data is not None:
        patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
        if not patient_info.empty:
            nombre = patient_info['Nombre(s)'].iloc[0]
            ap_paterno = patient_info['Apellido paterno'].iloc[0]
            ap_materno = patient_info['Apellido materno'].iloc[0]
            id_paciente = patient_info['ID'].iloc[0]

            st.title(f'Exámenes de laboratorio')
            st.subheader(f'{nombre} {ap_paterno} {ap_materno} {id_paciente}')
            st.subheader("Registro de Exámenes")
            df = get_exam_from_csv(id_paciente)
            st.write(df)

            def mostrar_archivos_pdf(id_paciente):
                st.subheader("Archivos")
                st.info('Selecciona el archivo a descargar:')
                patient_folder = f"{id_paciente}_examenes"

                if not os.path.exists(patient_folder):
                    st.error("No hay archivos PDF disponibles para descargar.")
                    return

                pdf_files = [f for f in os.listdir(patient_folder) if f.endswith('.pdf')]
                if pdf_files:
                    for pdf in pdf_files:
                        file_path = os.path.join(patient_folder, pdf)
                        with open(file_path, "rb") as f:
                            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                        download_link = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{pdf}">Descargar {pdf}</a>'
                        st.markdown(download_link, unsafe_allow_html=True)
                else:
                    st.error("No hay archivos PDF disponibles para descargar.")

            mostrar_archivos_pdf(id_paciente)


def load_med(patient_id):
    file_path = f'{patient_id}_medicamentos.csv'
    try:
        med_df = pd.read_csv(file_path)
        if 'Tratamiento_Terminado' not in med_df.columns:
            med_df['Tratamiento_Terminado'] = False
    except FileNotFoundError:
        med_df = pd.DataFrame(columns=['Medicamento', 'Concentracion', 'Fecha', 'ID Doctor', 'Nombre Doctor', 'Fecha_Inicio', 'Fecha_Fin','Instrucción','Tratamiento_Terminado'])
    return med_df

def update_treatment_status(patient_id, med_df):
    file_path = f'{patient_id}_medicamentos.csv'
    med_df.to_csv(file_path, index=False)
    st.success("El estado del tratamiento ha sido actualizado.")

if user_type == 'paciente':
    if selected == 'Medicamentos':
        usuarios_pacientes = pd.read_excel("usuarios.xlsx")
        selected = st.session_state.get('selected', None)
        patient_data = st.session_state.get('user_data', None)

        if patient_data is not None:
            patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
            if not patient_info.empty:
                nombre = patient_info['Nombre(s)'].iloc[0]
                ap_paterno = patient_info['Apellido paterno'].iloc[0]
                ap_materno = patient_info['Apellido materno'].iloc[0]
                id = patient_info['ID'].iloc[0]

        st.title(f'Medicamentos')
        st.subheader(f'{nombre} {ap_paterno} {ap_materno} {id}')

        patient_id = user_data['ID']

        med_df = load_med(patient_id)

        if not med_df.empty:
            st.subheader('Historial de medicamentos:')

            gb = GridOptionsBuilder.from_dataframe(med_df)
            gb.configure_column("Tratamiento_Terminado", editable=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                med_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True
            )

            updated_med_df = grid_response['data']

            if not med_df.equals(updated_med_df):
                update_treatment_status(patient_id, updated_med_df)

        else:
            st.warning("No se han registrado medicamentos para este paciente.")


def save_diag(diagnostico, patient_id, doctor_id, fecha):
        diag_df = load_diag(patient_id)

        doctor_info = doctors.loc[doctors['ID'] == doctor_id, ['Nombre(s)', 'Apellido paterno', 'Apellido materno']].values
        if doctor_info.size == 0:
            nombre_completo = "No se encontró al doctor con ese ID"
        else:
            nombre_completo = f"{doctor_info[0][0]} {doctor_info[0][1]} {doctor_info[0][2]}"

        new_diag = pd.DataFrame({
            'Diagnóstico': [diagnostico],
            'Paciente': [patient_id],
            'Fecha': [fecha],
            'ID Doctor': [doctor_id],
            'Nombre Doctor': [nombre_completo],
            'Curado': [False]
        })

        diag_df = pd.concat([diag_df, new_diag], ignore_index=True)
        file_path = f'{patient_id}_diagnosticos.csv'
        diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha guardado el diagnóstico del paciente {patient_id} en '{file_path}'")

def load_diag(patient_id):
        file_path = f'{patient_id}_diagnosticos.csv'
        try:
            diag_df = pd.read_csv(file_path)
            if 'Curado' not in diag_df.columns:
                diag_df['Curado'] = False
            if 'Nombre Doctor' not in diag_df.columns:
                diag_df['Nombre Doctor'] = ''
        except FileNotFoundError:
            diag_df = pd.DataFrame(columns=['Diagnóstico', 'Fecha', 'Paciente', 'ID Doctor', 'Nombre Doctor', 'Curado'])
        return diag_df

def update_treatment_status(patient_id, updated_diag_df):
        file_path = f'{patient_id}_diagnosticos.csv'
        updated_diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha actualizado el estado del tratamiento del paciente {patient_id}")

if selected == 'Diagnósticos médicos':
      usuarios_pacientes = pd.read_excel("usuarios.xlsx")
      selected = st.session_state.get('selected',None)
      patient_data = st.session_state.get('user_data',None)

      if patient_data is not None:
        patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
        if not patient_info.empty:

          nombre = patient_info['Nombre(s)'].iloc[0]
          ap_paterno = patient_info['Apellido paterno'].iloc[0]
          ap_materno = patient_info['Apellido materno'].iloc[0]
          id = patient_info['ID'].iloc[0]

      st.title(f'Diagnósticos médicos,')
      st.subheader(f'{nombre} {ap_paterno} {ap_materno} {id}')

      st.write(f"""
      La tabla a continuación muestra información importante sobre tus diagnósticos recientes.

      Si tienes alguna pregunta o inquietud, no dudes en comunicarte con tu médico.

      ¡Gracias por confiar en nosotros con tu cuidado médico!
      """)

      patient_id = user_data['ID']

      diag_df = load_diag(patient_id)
      if not diag_df.empty:
            st.subheader('Diagnósticos actuales:')
            st.write(diag_df)
      else:
            st.error("No se han registrado diagnósticos para este paciente.")




if selected == 'Imágenes médicas':
      usuarios_pacientes = pd.read_excel("usuarios.xlsx")
      selected = st.session_state.get('selected',None)
      patient_data = st.session_state.get('user_data',None)

      if patient_data is not None:
          patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
          if not patient_info.empty:

            nombre = patient_info['Nombre(s)'].iloc[0]
            ap_paterno = patient_info['Apellido paterno'].iloc[0]
            ap_materno = patient_info['Apellido materno'].iloc[0]
            id = patient_info['ID'].iloc[0]

      st.title(f'Imágenes médicas,')
      st.subheader(f'{nombre} {ap_paterno} {ap_materno} {id}')

      st.write("Dado el tiempo limitado disponible para el proyecto y la falta de experiencia en TI en la aplicación de NEXIA, no se implementará un programa para la lectura de imágenes médicas en esta fase.\n\nSin embargo, es importante considerar la implementación de esta funcionalidad en el futuro para que la aplicación pueda ser una herramienta completa y eficaz en su campo.\n\nA continuación, se presentarán algunas imágenes que ilustran cómo debería verse esta funcionalidad cuando se integre en la aplicación con los avances tecnológicos actuales.")

      VIDEO_URL = "https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME"
      st.video(VIDEO_URL)

      st.write('Creador: TIME')
      st.write('How AI Could Change the Future of Medicine')
      st.write('URL: https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME')

      with st.expander('Noticias'):
          st.write('A continuación, se presentarán diversas noticias sobre la implementación de sistemas de imágenes médicas en aplicaciones similares a NEXIA, demostrando que es una posibilidad viable.')
          st.write(" - Caja pone en marcha proyecto Redimed para digitalizar servicios de radiología [Link](https://www.ccss.sa.cr/noticia?v=caja-pone-en-marcha-proyecto-redimed-para-digitalizar-servicios-de-radiologia)")
          st.write(' - CCSS registrará las radiografías para que estén a disposición de todos los médicos [Link](https://amprensa.com/2022/11/ccss-registrara-las-radiografias-para-que-esten-a-disposicion-de-todos-los-medicos/)')
          st.write(' - Mejores aplicaciones DICOM para móvil (Android and iOS)[Link](https://www.imaios.com/es/recursos/blog/mejor-aplicacion-dicom-movil)')

def obtener_informacion_vacunas(patient_id):
    pacientes = pd.read_excel('usuarios.xlsx')
    dosis = pd.read_excel('dosis.xlsx')
    vacunas = pd.read_excel('vacunas.xlsx')

    dosis_paciente = dosis[dosis['ID'] == patient_id]

    vacunas_paciente = vacunas[vacunas['ID_vacuna'].isin(dosis_paciente['ID_vacuna'])]

    informacion_paciente = pd.merge(vacunas_paciente, dosis_paciente, on='ID_vacuna')

    informacion_paciente = informacion_paciente[['Nombre', 'Descripción', 'Lote', 'Fecha de aplicación']]

    return informacion_paciente

if selected == 'Vacunas':
    usuarios_pacientes = pd.read_excel("usuarios.xlsx")
    selected = st.session_state.get('selected',None)
    patient_data = st.session_state.get('user_data',None)

    if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:

        nombre = patient_info['Nombre(s)'].iloc[0]
        ap_paterno = patient_info['Apellido paterno'].iloc[0]
        ap_materno = patient_info['Apellido materno'].iloc[0]
        id = patient_info['ID'].iloc[0]

    st.title(f'Vacunas,')
    st.subheader(f'{nombre} {ap_paterno} {ap_materno} {id}')

    st.write(f"""

              En esta sección, puedes encontrar detalles sobre tu historial de vacunación. A continuación se muestra información sobre las vacunas que has recibido, incluyendo el nombre de la vacuna, una breve descripción, el número de lote y la fecha de aplicación.

              Es importante mantener un registro actualizado de tus vacunas para garantizar una buena salud y prevenir enfermedades. Si tienes alguna pregunta sobre tus vacunas o necesitas más información, no dudes en comunicarte con tu médico.

              ¡Gracias por mantener tu historial de vacunación al día y cuidar de tu salud!
              """)

    st.write('Información de vacunas del paciente:')

    patient_id = st.session_state.get('user_data', {}).get('ID', None)

    if patient_id is not None:
        informacion_paciente = obtener_informacion_vacunas(patient_id)

        st.info("Por favor, seleccione una vacuna para ver la información.")

        for index, vacuna in informacion_paciente.iterrows():
            with st.expander(f"Vacuna: {vacuna['Nombre']}"):
                st.write(f"Nombre: {vacuna['Nombre']}")
                st.write(f"Descripción: {vacuna['Descripción']}")
                st.write(f"Lote: {vacuna['Lote']}")
                st.write(f"Fecha de aplicación: {vacuna['Fecha de aplicación']}")

    else:
        st.write("No se ha encontrado información del paciente.")

if selected == 'Alergias':
  def display_patient_allergies(patient_id):
          allergies_data = load_allergies(patient_id)
          if not allergies_data.empty:
              st.subheader("Alergias del paciente")
              st.write(allergies_data)
          else:
              st.warning("No hay datos de alergias para mostrar.")

  def load_allergies(patient_id):
          try:
              allergies_df = pd.read_csv(f"{patient_id}_alergias.csv")
          except FileNotFoundError:
              allergies_df = pd.DataFrame(columns=["Alergias"])
          return allergies_df

  def save_patient_allergies(selected_allergies, patient_id):
      allergies_df = pd.DataFrame({"Alergias": list(selected_allergies)})
      file_path = f"{patient_id}_alergias.csv"
      allergies_df.to_csv(file_path, index=False)
      st.success(f"Se han guardado tus alergias en '{file_path}'")

  st.title('Registro de Alergias')

  pacientes = pd.read_excel("usuarios.xlsx")
  patient_id = st.session_state.get('user_data', {}).get('ID', None)

  if patient_id:
      st.info('Selecciona las alergias que padeces:')
      alergias = pd.read_excel("alergias.xlsx")

      opciones_alergias = alergias['Alergias'].dropna().unique()

      if 'selected_allergies' not in st.session_state:
          st.session_state.selected_allergies = set()

      selected_allergies = st.multiselect(
          'Selecciona tus alergias:',
          opciones_alergias,
          default=list(st.session_state.selected_allergies)
      )

      st.session_state.selected_allergies = set(selected_allergies)

      st.info('Ingresa las alergias escritas una por una.')
      nueva_alergia_personalizada = st.text_input("Si tu alergia no está en la lista, por favor añádela aquí:", placeholder='Ingresa la alergia aquí')
      
      if nueva_alergia_personalizada and nueva_alergia_personalizada not in st.session_state.selected_allergies:
          st.session_state.selected_allergies.add(nueva_alergia_personalizada)

      if st.button("Guardar alergias"):
          save_patient_allergies(st.session_state.selected_allergies, patient_id)

      display_patient_allergies(patient_id)


def load_symptoms_data(patient_id):
    try:
        symptoms_data = pd.read_csv(f"{patient_id}_symptoms_data.csv", usecols=["Fecha", "Síntomas"])
    except FileNotFoundError:
        symptoms_data = pd.DataFrame(columns=["Fecha", "Síntomas"])
    return symptoms_data

def add_symptoms(patient_id, date, symptom, symptoms_data):
    new_row = {"Fecha": date, "Síntomas": ", ".join(symptom)}
    new_df = pd.DataFrame([new_row], columns=["Fecha", "Síntomas"])  # Especificar las columnas deseadas
    symptoms_data = pd.concat([symptoms_data, new_df], ignore_index=True)
    symptoms_data.to_csv(f"{patient_id}_symptoms_data.csv", index=False)
    return symptoms_data

if selected == 'Registro de síntomas':
    st.title(f'Regístro de síntomas,')
    usuarios_pacientes = pd.read_excel("usuarios.xlsx")
    selected = st.session_state.get('selected',None)
    patient_data = st.session_state.get('user_data',None)

    if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:

        nombre = patient_info['Nombre(s)'].iloc[0]
        ap_paterno = patient_info['Apellido paterno'].iloc[0]
        ap_materno = patient_info['Apellido materno'].iloc[0]
        id = patient_info['ID'].iloc[0]

    st.subheader(f'{nombre} {ap_paterno} {ap_materno} {id}')

    symptoms_list = ["Fiebre", "Tos", "Dolor de garganta", "Congestión nasal", "Dificultad para respirar", "Fatiga", "Dolor de cabeza", "Náuseas", "Dolor muscular", "Pérdida del gusto u olfato"]

    st.subheader('Registrar síntomas:')
    symptoms_data = load_symptoms_data(id)

    st.info("Por favor, seleccione sus síntomas diarios:")

    with st.form(key='symptoms_form'):
        date = st.date_input("Fecha", value=pd.Timestamp.today())
        selected_symptoms =  st.multiselect("Síntomas", symptoms_list)
        submit_button = st.form_submit_button(label='Guardar')

    if submit_button:
        symptoms_data = add_symptoms(id,date, selected_symptoms, symptoms_data)
        st.success("¡Síntomas guardados exitosamente para el día {}!".format(date))

    st.subheader("Historial de síntomas")
    st.write(symptoms_data)
    
if selected == 'Doctor':
    usuarios_doc = pd.read_excel("usuarios_doc.xlsx")
    selected = st.session_state.get('selected', None)
    st.title("Información de Doctor")
    doctor_data = st.session_state.get('user_data', None)
    if doctor_data is not None:
        doctor_info = usuarios_doc.loc[usuarios_doc['ID'] == doctor_data['ID']]
        if not doctor_info.empty:
            nombre = doctor_info['Nombre(s)'].iloc[0]
            ap_paterno = doctor_info['Apellido paterno'].iloc[0]
            ap_materno = doctor_info['Apellido materno'].iloc[0]
            doc_rol = doctor_info['Rol del usuario'].iloc[0]
            especialidad = doctor_info['Especialidad'].iloc[0]
            subespecialidad = doctor_info['Sub-especialidad'].iloc[0]
            clues = doctor_info['Clave única de establecimiento de salud'].iloc[0]
            celular = doctor_info['Celular'].iloc[0]
            id = doctor_info['ID'].iloc[0]

            st.subheader(f'Bienvenido, Dr. {nombre} {ap_paterno} {ap_materno}')
            col1,col2,col3 = st.columns(3)

            with col2.container():
                col2.metric('Rol de usuario', doc_rol)
                col2.metric("Especialidad", especialidad)
                col2.metric("Sub-especialidad", subespecialidad)

            with col3.container():
                col3.metric('ID', id)
                col3.metric("CLUES", clues)
                col3.metric("Celular", celular)

            try:
                path = f'{id}.jpeg'
                print("Ruta de la imagen:", path)
                image = Image.open(path)
                col1.image(image, caption=f'Dr. {nombre}')
            except FileNotFoundError:
                col1.write('No hay imagen registrada.')


if selected == 'Buscar doctor':
    usuarios_doc = pd.read_excel("usuarios_doc.xlsx")

    def display_doctor_info(doctor_info, image_path):
        nombre = doctor_info['Nombre(s)']
        ap_paterno = doctor_info['Apellido paterno']
        ap_materno = doctor_info['Apellido materno']
        doc_rol = doctor_info['Rol del usuario']
        especialidad = doctor_info['Especialidad']
        subespecialidad = doctor_info['Sub-especialidad']
        clues = doctor_info['Clave única de establecimiento de salud']
        celular = doctor_info['Celular']
        id = doctor_info['ID']

        st.subheader(f'{nombre} {ap_paterno} {ap_materno}')

        col1, col2, col3 = st.columns(3)

        with col2:
            st.metric('Rol de usuario', doc_rol)
            st.metric("Especialidad", especialidad)
            st.metric("Sub-especialidad", subespecialidad)

        with col3:
            st.metric('ID', id)
            st.metric("CLUES", clues)
            st.metric("Celular", celular)

        try:
            image = Image.open(image_path)
            col1.image(image, caption=f'Dr. {nombre} {ap_paterno} {ap_materno}')
        except FileNotFoundError:
            col1.write('No hay imagen registrada.')

    st.title("Buscar Doctores")
    st.subheader('Especialidad o ID')
    especialidades = usuarios_doc['Especialidad'].unique()

    st.info("Busque el doctor por su especialidad o por su ID.")

    col1, col2 = st.columns(2)

    with col1:
        especialidad_select = st.selectbox("Seleccione una especialidad:", especialidades)

    with col2:
        id_text = st.text_input("Ingrese el ID del doctor (opcional):")


    if id_text:
        filtered_doctors = usuarios_doc[usuarios_doc['ID'].astype(str) == id_text]
    else:
        filtered_doctors = usuarios_doc[usuarios_doc['Especialidad'] == especialidad_select]

    if not filtered_doctors.empty:
        for index, doctor_info in filtered_doctors.iterrows():
            doctor_id = doctor_info['ID']
            image_path = f'{doctor_id}.jpeg'
            display_doctor_info(doctor_info, image_path)
    else:
        st.error("No se encontraron doctores con la especialidad y/o ID seleccionados.")

def display_patient_data_by_id(patient_id):
    symptoms_data = load_symptoms_data(patient_id)
    if not symptoms_data.empty:
        st.subheader("Historial de síntomas")
        st.write(symptoms_data[["Fecha", "Síntomas"]])
    else:
        st.write("No hay datos de síntomas para mostrar.")


def insert_cirugia_to_excel(paciente, nombre,cirugia, descripcion, id_doctor, doctor, especialidad, fecha, estado):
      file_path = "cirugias.csv"

      if os.path.exists(file_path):
          df = pd.read_csv(file_path)
      else:
          df = pd.DataFrame(columns=['Paciente','Nombre','Cirugía','Descripción', 'ID Doctor', 'Doctor', 'Especialidad', 'Fecha', 'Estado'])

      new_data = pd.DataFrame([[paciente, nombre,cirugia, descripcion, id_doctor, doctor, especialidad, fecha, estado]],
                              columns=['Paciente','Nombre','Cirugía', 'Descripción', 'ID Doctor', 'Doctor', 'Especialidad', 'Fecha', 'Estado'])

      df = pd.concat([df, new_data], ignore_index=True)
      df.to_csv(file_path, index=False)

def display_patient_allergies(patient_id):
    allergies_data = load_allergies(patient_id)
    if not allergies_data.empty:
        st.subheader("Alergias del paciente")
        st.write(allergies_data)
    else:
        st.write("No hay datos de alergias para mostrar.")

def load_allergies(patient_id):
      try:
          allergies_df = pd.read_csv(f"{patient_id}_alergias.csv")
      except FileNotFoundError:
          allergies_df = pd.DataFrame(columns=["Alergias"])
      return allergies_df

if selected == 'Pacientes':
    pacientes = pd.read_excel('usuarios.xlsx')
    st.title("Información de Paciente")

    search_by_id = st.checkbox('Buscar por ID')
    ingresado_id = st.text_input('Ingresar ID del paciente:', '')
    matches1 = pacientes[pacientes['ID'] == ingresado_id]
    
    if not matches1.empty:
        paciente_seleccionado1 = matches1.iloc[0]
        id_paciente_seleccionado = paciente_seleccionado1['ID']

        paciente_seleccionado1 = matches1.iloc[0]
        name = paciente_seleccionado1['Nombre(s)']
        ap_materno = paciente_seleccionado1['Apellido materno']
        ap_paterno = paciente_seleccionado1['Apellido paterno']
        altura = str(paciente_seleccionado1['Altura'])
        peso = str(paciente_seleccionado1['Peso'])
        nacimiento = str(paciente_seleccionado1['Día de nacimiento']) + '/' + \
            str(paciente_seleccionado1['Mes de nacimiento']) + '/' + \
            str(paciente_seleccionado1['Año de nacimiento'])
        ocupacion = paciente_seleccionado1['Ocupación']
        edad = paciente_seleccionado1['Edad']
        padecimiento = paciente_seleccionado1['Padecimientos']
        sangre = paciente_seleccionado1['Tipo de sangre']
        alergias = paciente_seleccionado1['Alergias']
        medicacion = paciente_seleccionado1['Medicación actual']
        organos = paciente_seleccionado1['Donante de organos']
        genero = paciente_seleccionado1['Género']
        estado_civil = paciente_seleccionado1['Estado civil']
        grupo = paciente_seleccionado1['Grupo étnico']
        religion = paciente_seleccionado1['Religión']
        vivienda = paciente_seleccionado1['Vivienda']
        calle = paciente_seleccionado1['Calle']
        num_ext = paciente_seleccionado1['Número ext']
        num_int = paciente_seleccionado1['Número int']
        Estado = paciente_seleccionado1['Estado']
        municipio = paciente_seleccionado1['Municipio']
        colonia = paciente_seleccionado1['Colonia']
        cod_postal = paciente_seleccionado1['Código postal']
        correo = paciente_seleccionado1['Correo']
        celular = paciente_seleccionado1['Celular']
        tel = paciente_seleccionado1['Teléfono']
        contact_emerg = paciente_seleccionado1['Contacto de emergencia']
        id = paciente_seleccionado1['ID']

        st.subheader(f"{name} {ap_paterno} {ap_materno} {id}")

        col1, col2, col3, col4 = st.columns(4)

        with col2.container():
            col2.metric('Fecha de Nacimiento', nacimiento)
            col2.metric("Ocupación", ocupacion)
            col2.metric("Estado Civil", estado_civil)
            col2.metric("Género", genero)

        with col3.container():
            col3.metric("Altura", altura)
            col3.metric("Peso", peso)
            col3.metric("Edad", edad)
            col3.metric("Tipo de sangre", sangre)

        with col4.container():
            col4.metric("Donante de órganos", organos)
            col4.metric('Padecimiento', padecimiento)
            col4.metric("Alergias", alergias)
            col4.metric('Medicación actual', medicacion)

        try:
          path = f'{id}.jpeg'
          print("Ruta de la imagen:", path)
          image = Image.open(path)
          col1.image(image, caption=f'Paciente {name} {ap_paterno} {ap_materno}')

        except FileNotFoundError:
            col1.write('No hay imagen registrada.')

        with st.expander("Datos generales"):
            st.write(f'Grupo étnico: {grupo}')
            st.write(f'Religión: {religion}')
            st.write(f'Vivienda: {vivienda}')

        with st.expander("Domicilio"):
            st.write(f'Calle: {calle}')
            st.write(f'Número ext: {num_ext}')
            st.write(f'Número int: {num_int}')
            st.write(f'Estado: {Estado}')
            st.write(f'Municipio: {municipio}')
            st.write(f'Colonia: {colonia}')
            st.write(f'Código postal: {cod_postal}')

        with st.expander('Contacto'):
            st.write(f'Correo: {correo}')
            st.write(f'Celular: {celular}')
            st.write(f'Teléfono: {tel}')
            st.write(f'Contacto de emergencia: {contact_emerg}')
    else:
        st.write("No se encontraron coincidencias.")

    

    selected = option_menu(
          menu_title= None,
          options = ['Medicamentos', 'Exámenes de laboratorio','Vacunas','Alergias','Ruta quirúrgica','Imágenes médicas','Diagnósticos médicos','Regístro de síntomas','Notas adicionales','Historial familiar'],
          icons = ['capsule-pill', 'droplet','clipboard2-pulse-fill','flower1','heart-pulse','card-image','hospital','activity','clipboard','journal-text'],
          orientation = 'horizontal',
          menu_icon = None,
          styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": '#84D9C1'},
          }
    )

    if selected == 'Imágenes médicas':
      st.title('Imágenes médicas')
      st.write("Dado el tiempo limitado disponible para el proyecto y la falta de experiencia en TI en la aplicación de NEXIA, no se implementará un programa para la lectura de imágenes médicas en esta fase.\n\nSin embargo, es importante considerar la implementación de esta funcionalidad en el futuro para que la aplicación pueda ser una herramienta completa y eficaz en su campo.\n\nA continuación, se presentarán algunas imágenes que ilustran cómo debería verse esta funcionalidad cuando se integre en la aplicación con los avances tecnológicos actuales.")

      VIDEO_URL = "https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME"
      st.video(VIDEO_URL)

      st.write('Creador: TIME')
      st.write('How AI Could Change the Future of Medicine')
      st.write('URL: https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME')

      with st.expander('Noticias'):
          st.write('A continuación, se presentarán diversas noticias sobre la implementación de sistemas de imágenes médicas en aplicaciones similares a NEXIA, demostrando que es una posibilidad viable.')
          st.write(" - Caja pone en marcha proyecto Redimed para digitalizar servicios de radiología [Link](https://www.ccss.sa.cr/noticia?v=caja-pone-en-marcha-proyecto-redimed-para-digitalizar-servicios-de-radiologia)")
          st.write(' - CCSS registrará las radiografías para que estén a disposición de todos los médicos [Link](https://amprensa.com/2022/11/ccss-registrara-las-radiografias-para-que-esten-a-disposicion-de-todos-los-medicos/)')
          st.write(' - Mejores aplicaciones DICOM para móvil (Android and iOS)[Link](https://www.imaios.com/es/recursos/blog/mejor-aplicacion-dicom-movil)')

    if selected == 'Regístro de síntomas':
        display_patient_data_by_id(id)

    if selected == 'Alergias':
        def display_patient_allergies(id):
          allergies_data = load_allergies(id)
          if not allergies_data.empty:
              st.subheader("Alergias")
              st.write(allergies_data)
          else:
              st.error("No hay datos de alergias para mostrar.")
        
        def load_allergies(patient_id):
          try:
              allergies_df = pd.read_csv(f"{patient_id}_alergias.csv")
          except FileNotFoundError:
              allergies_df = pd.DataFrame(columns=["Alergias"])
          return allergies_df
        
        st.title('Alergias del Paciente')
        
        usuarios_pacientes = pd.read_excel("usuarios.xlsx")
        
        if id:
          display_patient_allergies(id)
        
    if selected == 'Vacunas':
        st.title('Vacunas')
        st.write('Información de vacunas del paciente:')
        if id is not None:
            informacion_paciente = obtener_informacion_vacunas(id)
            st.info("Por favor, seleccione una vacuna para ver la información.")
            for index, vacuna in informacion_paciente.iterrows():
                with st.expander(f"Vacuna: {vacuna['Nombre']}"):
                    st.write(f"Nombre: {vacuna['Nombre']}")
                    st.write(f"Descripción: {vacuna['Descripción']}")
                    st.write(f"Lote: {vacuna['Lote']}")
                    st.write(f"Fecha de aplicación: {vacuna['Fecha de aplicación']}")
        else:
            st.write("No se ha seleccionado ningún paciente.")

    def save_diag(diagnostico, patient_id, doctor_id, fecha):
        diag_df = load_diag(patient_id)

        doctor_info = doctors.loc[doctors['ID'] == doctor_id, ['Nombre(s)', 'Apellido paterno', 'Apellido materno']].values
        if doctor_info.size == 0:
            nombre_completo = "No se encontró al doctor con ese ID"
        else:
            nombre_completo = f"{doctor_info[0][0]} {doctor_info[0][1]} {doctor_info[0][2]}"

        new_diag = pd.DataFrame({
            'Diagnóstico': [diagnostico],
            'Paciente': [patient_id],
            'Fecha': [fecha],
            'ID Doctor': [doctor_id],
            'Nombre Doctor': [nombre_completo],
            'Curado': [False]
        })

        diag_df = pd.concat([diag_df, new_diag], ignore_index=True)
        file_path = f'{patient_id}_diagnosticos.csv'
        diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha guardado el diagnóstico del paciente {patient_id} en '{file_path}'")

    def load_diag(patient_id):
        file_path = f'{patient_id}_diagnosticos.csv'
        try:
            diag_df = pd.read_csv(file_path)
            if 'Curado' not in diag_df.columns:
                diag_df['Curado'] = False
            if 'Nombre Doctor' not in diag_df.columns:
                diag_df['Nombre Doctor'] = ''
        except FileNotFoundError:
            diag_df = pd.DataFrame(columns=['Diagnóstico', 'Fecha', 'Paciente', 'ID Doctor', 'Nombre Doctor', 'Curado'])
        return diag_df

    def update_treatment_status(patient_id, updated_diag_df):
        file_path = f'{patient_id}_diagnosticos.csv'
        updated_diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha actualizado el estado del tratamiento del paciente {patient_id}")

    if selected == 'Diagnósticos médicos':
        st.title('Diagnósticos del paciente')

        if id:
            diag_df = load_diag(id)

            if not diag_df.empty:
                st.subheader('Historial de diagnósticos del paciente')

                gb = GridOptionsBuilder.from_dataframe(diag_df)
                gb.configure_column("Curado", editable=True)
                grid_options = gb.build()

                grid_response = AgGrid(
                    diag_df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=True
                )

                updated_diag_df = grid_response['data']

                if not diag_df.equals(updated_diag_df):
                    update_treatment_status(id, updated_diag_df)
            else:
                st.warning('No se han registrado diagnósticos para este paciente.')

            diag = pd.read_excel('CIE-10_DIAGNOSTICOS_ACTABR2024.xlsx')
            selected_diag = st.selectbox('Seleccione el diagnóstico:', diag['NOMBRE'].unique(), key='diagnostico_select')
            doctor_id = st.text_input('Ingrese el ID del Doctor:', key='doctor_id_input')
            fecha = datetime.now().strftime("%Y-%m-%d")

            if st.button('Generar diagnóstico', key='generate_diagnosis_button'):
                if selected_diag and id and doctor_id:
                    save_diag(selected_diag, id, doctor_id, fecha)
                else:
                    st.error('Por favor, complete todos los campos.')


    
    def save_medic(medicamento, concentracion, patient_id, doctor_id, start_date, end_date, instruc):
       med_df = load_med(patient_id)
       doctor_info = doctors.loc[doctors['ID'] == doctor_id, ['Nombre(s)', 'Apellido paterno', 'Apellido materno']].values
       if doctor_info.size == 0:
            nombre_completo = "No se encontró al doctor con ese ID"
       else:
            nombre_completo = f"{doctor_info[0][0]} {doctor_info[0][1]} {doctor_info[0][2]}"

            new_med = pd.DataFrame({
                'Medicamento': [medicamento],
                'Concentración': [concentracion],
                'Fecha': [datetime.now().strftime("%Y-%m-%d")],
                'Instrucción': [instruc],
                'ID Doctor': [doctor_id],
                'Nombre Doctor': [nombre_completo],
                'Fecha_Inicio': [start_date],
                'Fecha_Fin': [end_date],
                'Tratamiento_Terminado': [False]
            })
            med_df = pd.concat([med_df, new_med], ignore_index=True)
            file_path = f'{patient_id}_medicamentos.csv'
            med_df.to_csv(file_path, index=False)
            st.success(f"Se ha guardado el medicamento del paciente {patient_id} en '{file_path}'")

    def load_med(patient_id):
        file_path = f'{patient_id}_medicamentos.csv'
        try:
            med_df = pd.read_csv(file_path)
            if 'Tratamiento_Terminado' not in med_df.columns:
                med_df['Tratamiento_Terminado'] = False
        except FileNotFoundError:
            med_df = pd.DataFrame(columns=['Medicamento', 'Concentración', 'Fecha', 'ID Doctor', 'Nombre Doctor', 'Fecha_Inicio', 'Fecha_Fin','Instrucción','Tratamiento_Terminado'])
        return med_df

    if selected == 'Medicamentos':
        st.title('Medicamentos')

        med_df = load_med(id)
        if not med_df.empty:
            st.subheader('Medicamentos actuales del paciente:')
            st.write(med_df)
        else:
            st.error("No se han registrado medicamentos para este paciente.")

        st.title('Recetar medicamento')
        med = pd.read_excel('MEDICAMENTOS_ENERO_2022.xlsx')
        selected_med = st.selectbox('Seleccione el medicamento:', med['NOMBRE GENERICO'].unique())
        selected_concentracion = st.selectbox('Seleccione la concentración:', med[med['NOMBRE GENERICO'] == selected_med]['CONCENTRACION'].unique())

        with st.form("med_form"):
            instruc = st.text_input('Ingresar instrucciones del tratamiento:')
            
            doctor_id = st.text_input('ID del Doctor:')
            start_date = st.date_input('Fecha de inicio del tratamiento')
            end_date = st.date_input('Fecha de finalización del tratamiento')

            submitted = st.form_submit_button('Generar receta')

            if submitted:
                if selected_med and id and doctor_id:
                    save_medic(selected_med, selected_concentracion, id, doctor_id, start_date, end_date, instruc)
                else:
                    st.error("Por favor, complete todos los campos.")


    if selected == 'Ruta quirúrgica':

          with st.form("Ruta quirúrgica"):
            st.title('Guardar cirugías')
            st.header('Formulario de cirugías')
            doctor = f"{user_data['Nombre(s)']} {user_data['Apellido paterno']} {user_data['Apellido materno']}"
            cita = pd.read_csv("cirugias.csv")
            dfcita = cita.loc[cita["Doctor"] == doctor]
            st.dataframe(dfcita)

            cirugia = st.text_input('Ingresa el nombre de la cirugía:')
            descripcion = st.text_input('Ingresa una breve descripción de la cirugía:')
            id_doctor = st.text_input('Ingresa ID del doctor encargado de la cirugía:')
            doctors['Nombre Completo'] = doctors['Nombre(s)'] + ' ' + doctors['Apellido paterno'] + ' ' + doctors['Apellido materno']
            especialidad = doctors.loc[doctors['Nombre Completo'] == doctor, 'Especialidad'].values[0]
            fecha = st.date_input("Fecha", value=pd.Timestamp.today())
            estado = st.selectbox("Estado de cirugía: ", ['Pendiente','En proceso','Realizada'])

            submitted = st.form_submit_button("Guardar cirugía")
            if submitted:
                # Verificar si el ID del paciente existe en la base de datos
                if id in users['ID'].values:
                    # Si el ID del paciente existe, continuar con el proceso de guardar la cirugía
                    st.session_state['Paciente'] = id
                    st.session_state['Cirugía'] = cirugia
                    st.session_state['Descripción'] = descripcion
                    st.session_state['ID Doctor'] = id_doctor
                    st.session_state['Doctor'] = doctor
                    st.session_state['Especialidad'] = especialidad
                    st.session_state['Fecha'] = fecha
                    st.session_state['Estado'] = estado

                    pacienteid = users[users['ID'] == id]

                    nombre = f"{pacienteid.iloc[0]['Nombre(s)']} {pacienteid.iloc[0]['Apellido paterno']} {pacienteid.iloc[0]['Apellido materno']}"

                    insert_cirugia_to_excel(id,nombre, cirugia, descripcion, id_doctor, doctor, especialidad, fecha, estado)

                    st.success("Se guardó la cirugía correctamente.")
                    cita = pd.read_csv("cirugias.csv")
                    dfcita = cita.loc[cita["Doctor"] == doctor]
                    st.dataframe(dfcita)
                else:
                    # Si el ID del paciente no existe, mostrar un mensaje de error
                    st.error("El ID del paciente no existe en la base de datos.")

    if selected == 'Historial familiar':
        def cargar_historial(id_paciente):
            file_path = f'{id_paciente}_historial_familiar.csv'
            try:
                historial_df = pd.read_csv(file_path)
            except FileNotFoundError:
                historial_df = pd.DataFrame(columns=[
                    'ID Paciente', 'ID Familiar', 'Parentesco', 'Tabaquismo', 
                    'Alcoholismo', 'Afección Crónica', 'Afección Grave', 
                    'Enfermedad Mental', 'Edad en Desarrollarla', 
                    'Discapacidad de Desarrollo', 'Defectos Congénitos', 
                    'Problemas de Embarazo', 'Causa de Muerte'
                ])
            return historial_df

        def guardar_historial(id_paciente, id_familiar, parentesco, tabaquismo, alcoholismo, 
                              afeccion_cronica, afeccion_grave, enfermedad_mental, 
                              edad_en_desarrollarla, discapacidad_de_desarrollo, 
                              defectos_congenitos, problemas_de_embarazo, causa_de_muerte):
            
            historial_df = cargar_historial(id_paciente)
            
            nueva_entrada = pd.DataFrame({
                'ID Paciente': [id_paciente],
                'ID Familiar': [id_familiar],
                'Parentesco': [parentesco],
                'Tabaquismo': [tabaquismo],
                'Alcoholismo': [alcoholismo],
                'Afección Crónica': [afeccion_cronica],
                'Afección Grave': [afeccion_grave],
                'Enfermedad Mental': [enfermedad_mental],
                'Edad en Desarrollarla': [edad_en_desarrollarla],
                'Discapacidad de Desarrollo': [discapacidad_de_desarrollo],
                'Defectos Congénitos': [defectos_congenitos],
                'Problemas de Embarazo': [problemas_de_embarazo],
                'Causa de Muerte': [causa_de_muerte]
            })
            
            historial_df = pd.concat([historial_df, nueva_entrada], ignore_index=True)
            file_path = f'{id_paciente}_historial_familiar.csv'
            historial_df.to_csv(file_path, index=False)
            st.success(f"Se ha guardado la información del familiar para el paciente {id_paciente} en '{file_path}'")

        st.title('Historial Familiar del Paciente')

        id_paciente = st.text_input('Ingrese el ID del paciente')

        if id_paciente:
            historial_df = cargar_historial(id_paciente)
            if not historial_df.empty:
                st.subheader('Historial familiar del paciente:')
                st.write(historial_df)
            else:
                st.warning("Todavía no se han registrado datos para este paciente.")

        st.subheader('Ingresar Información del Familiar')

        with st.form(key='formulario_familiar'):
            id_familiar = st.text_input('ID del Familiar')
            parentesco = st.text_input('Parentesco')
            tabaquismo = st.selectbox('¿Presenta Tabaquismo?', ['Sí', 'No'])
            alcoholismo = st.selectbox('¿Presenta Alcoholismo?', ['Sí', 'No'])
            afeccion_cronica = st.text_input('Afección Crónica')
            afeccion_grave = st.text_input('Afección Grave')
            enfermedad_mental = st.text_input('Enfermedad Mental')
            edad_en_desarrollarla = st.number_input('Edad en Desarrollarla', min_value=0, max_value=120)
            discapacidad_de_desarrollo = st.text_input('Discapacidad de Desarrollo')
            defectos_congenitos = st.text_input('Defectos Congénitos')
            problemas_de_embarazo = st.text_input('Problemas de Embarazos o Partos')
            causa_de_muerte = st.text_input('Causa de Muerte')
            
            boton_enviar = st.form_submit_button(label='Agregar Información')

        if boton_enviar:
            if id_paciente and id_familiar:
                guardar_historial(id_paciente, id_familiar, parentesco, tabaquismo, alcoholismo, 
                                  afeccion_cronica, afeccion_grave, enfermedad_mental, 
                                  edad_en_desarrollarla, discapacidad_de_desarrollo, 
                                  defectos_congenitos, problemas_de_embarazo, causa_de_muerte)
                
                historial_df = cargar_historial(id_paciente)
                st.write(historial_df)
            else:
                st.error("Por favor, complete todos los campos obligatorios (ID del Paciente y ID del Familiar).")
                
    def save_note(doctor_id, patient_id, note):
        notes_df = load_notes(patient_id)
        doctor_info = doctors.loc[doctors['ID'] == doctor_id, ['Nombre(s)', 'Apellido paterno', 'Apellido materno']].values
        if doctor_info.size == 0:
            nombre_completo = "No se encontró al doctor con ese ID"
        else:
            nombre_completo = f"{doctor_info[0][0]} {doctor_info[0][1]} {doctor_info[0][2]}"

        new_note = pd.DataFrame({
            'ID Doctor': [doctor_id],
            'Nombre Doctor': [nombre_completo],
            'Fecha': [datetime.now().strftime("%Y-%m-%d")],
            'Nota': [note],
            'ID Paciente': [patient_id]
        })
        notes_df = pd.concat([notes_df, new_note], ignore_index=True)
        file_path = f'{patient_id}_notas.csv'
        notes_df.to_csv(file_path, index=False)
        st.success(f"Se ha guardado la nota del paciente {patient_id} en '{file_path}'")

    def load_notes(patient_id):
        file_path = f'{patient_id}_notas.csv'
        try:
            notes_df = pd.read_csv(file_path)
        except FileNotFoundError:
            notes_df = pd.DataFrame(columns=['ID Doctor', 'Nombre Doctor', 'Fecha', 'Nota', 'ID Paciente'])
        return notes_df

    if selected == 'Notas adicionales':
        st.title('Historial de notas')
        notes_df = load_notes(id)
        if not notes_df.empty:
            st.subheader('Notas adicionales del paciente:')
            st.write(notes_df)
            
        with st.form("note_form"):
            st.header('Nueva Nota Adicional')
            doctor_id = st.text_input('ID del Doctor:')
            note = st.text_area('Nota adicional:')
            submitted = st.form_submit_button('Guardar nota')

        if submitted:
            if doctor_id and note and id:
                save_note(doctor_id, id, note)
            else:
                st.error("Por favor, complete todos los campos.")
                
                
    def mostrar_archivos_pdf(id_paciente):
        st.subheader("Archivos")
        st.info('Selecciona el archivo a descargar:')
        folder_path = f"{id_paciente}_examenes"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
    def insert_examen_to_csv(idp, idd, name, desc):
        file_path = "examenes_laboratorio.csv"
    
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
        else:
            df = pd.DataFrame(columns=['ID del paciente', 'ID del doctor', 'Título del examen', 'Breve descripción'])
    
        new_data = pd.DataFrame([[idp, idd, name, desc]],
                                columns=['ID del paciente', 'ID del doctor', 'Título del examen', 'Breve descripción'])
    
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(file_path, index=False)
    
    def get_exam_from_csv(id):
        file_path = "examenes_laboratorio.csv"
    
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            citas = df[df['ID del paciente'] == id]
            return citas
        else:
            df = pd.DataFrame(columns=['ID del paciente', 'ID del doctor', 'Título del examen', 'Breve descripción'])
            return df

    
    if selected == 'Exámenes de laboratorio':
        st.title('Exámenes de laboratorio')
    
        if id is not None:
            st.info(f"Sube el examen del paciente ID: {id}")
    
            with st.form(key="upload_form"):
                id_doctor = st.text_input("ID del Doctor:")
                descripcion = st.text_input("Descripción del Examen:")
                uploaded_file = st.file_uploader("Subir un archivo PDF", type="pdf")
                new_file_name = st.text_input("Asignar Nombre (ejemplo P1001A_EXAMENSANGRE):",
                                              value="" if not uploaded_file else uploaded_file.name.replace('.pdf', ''))
                submitted = st.form_submit_button(label="Guardar archivo")
                if submitted:
                    insert_examen_to_csv(id, id_doctor, new_file_name, descripcion)
                    if new_file_name:
                        new_file_name = new_file_name if new_file_name.endswith('.pdf') else new_file_name + '.pdf'
                        st.success(f"Archivo subido: {new_file_name}")
                        folder_path = f"{id}_examenes"
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)
    
                        file_path = os.path.join(folder_path, new_file_name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        mostrar_archivos_pdf(id)
    
            # Mostrar tabla CSV
            st.subheader("Registro de Exámenes")
            df = get_exam_from_csv(id)
            st.write(df)
    
        else:
            st.error("No se ha seleccionado ningún paciente.")
    



def get_cirugia_from_excel(paciente):
      file_path = "cirugias.csv"

      if os.path.exists(file_path):
          df = pd.read_csv(file_path)
          citas = df[df['Paciente'] == paciente]
          return citas
      else:
          df=pd.DataFrame(columns=['Paciente','Cirugía', 'Descripción', 'ID Doctor', 'Doctor', 'Especialidad', 'Fecha', 'Estado'])
          return df

if selected == 'Ruta quirúrgica' and user_type == 'paciente':
        st.title('Cirugías Guardadas')
        NOMBRE_paciente = f"{user_data['ID']}"
        citas = get_cirugia_from_excel(NOMBRE_paciente)
        st.dataframe(citas)

