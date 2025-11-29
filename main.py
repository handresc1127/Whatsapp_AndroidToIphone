import os
import tarfile
import shutil
import sqlite3
import subprocess

req_file_list = {'bin': ['adb.exe', 'AdbWinApi.dll','AdbWinUsbApi.dll','LegacyWhatsApp.apk'],'.':['migrate.py']}
iphone_backup_root_locs = [
    os.getenv('APPDATA')+'\\Apple Computer\\MobileSync\\Backup',
    os.getenv('USERPROFILE')+'\\Apple\\MobileSync\\Backup',
    os.getenv('USERPROFILE')+'\\Apple\\MobileSync'
]

print('\nWhatsApp android to ios transferrer\n')

# Detectar ADB disponible
adb_command = 'bin\\adb.exe'
if not os.path.exists(adb_command):
    print('bin\\adb.exe not found, trying system adb command...')
    # Verificar si adb está en PATH usando subprocess
    try:
        result = subprocess.run(
            ['adb', 'version'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            adb_command = 'adb'
            # Extraer ubicación del ADB
            adb_location = 'system PATH'
            for line in result.stdout.split('\n'):
                if 'Installed as' in line:
                    adb_location = line.split('Installed as')[1].strip()
                    break
            print(f'[OK] Using system adb: {adb_location}')
        else:
            raise Exception('ADB not in PATH')
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        print('\n[ERROR] ADB not found!')
        print('Please either:')
        print('  1. Place adb.exe in bin/ directory (see bin/README.md), or')
        print('  2. Install Android Platform Tools and add to PATH')
        print('\nDownload: https://developer.android.com/tools/releases/platform-tools')
        exit(1)
else:
    print('[OK] Using bin\\adb.exe')

# Validar archivos requeridos
for dirname in req_file_list:
    for filename in req_file_list[dirname]:
        # Omitir validación de adb.exe si ya lo validamos arriba
        if filename == 'adb.exe':
            continue
        # Omitir DLLs si estamos usando ADB del sistema
        if filename in ['AdbWinApi.dll', 'AdbWinUsbApi.dll'] and adb_command == 'adb':
            continue
        path = os.path.join(dirname,filename)
        if not os.path.exists(path):
            print('Missing: {}, terminating!'.format(path))
            exit(1)

use_android_backup = False

if os.path.exists('out\\android.db'):
    print('Android backup file already exists. Path: out\\android.db')
    use_android_backup = input('Do you want to use the current backup? [y/n]: ').upper() == 'Y'

if not use_android_backup:
    print('¿Quieres migrar WhatsApp estándar o WhatsApp Business?')
    print('1. WhatsApp estándar')
    print('2. WhatsApp Business')
    wa_choice = input('Selecciona 1 o 2: ').strip()
    if wa_choice == '2':
        wa_package = 'com.whatsapp.w4b'
        wa_apk = 'LegacyWhatsAppBusiness.apk' # Debes colocar el APK de WhatsApp Business legacy en bin/
        wa_db_path = 'tmp\\apps\\com.whatsapp.w4b\\db\\msgstore.db'
    else:
        wa_package = 'com.whatsapp'
        wa_apk = 'LegacyWhatsApp.apk'
        wa_db_path = 'tmp\\apps\\com.whatsapp\\db\\msgstore.db'
    os.system(f'{adb_command} kill-server')
    os.system(f'{adb_command} start-server')
    os.system(f'{adb_command} wait-for-device')

    print('\nAndroid device connected!\n')

    print('***********************************************')
    print('Please backup all your whatsapp chats before proceeding.')
    print('***********************************************')
    inp = input('\nDo you want to continue?[y/n]: ')
    if inp.upper() != 'Y':
        print('Exiting.')
        exit()

    print('\nStarting backup process.')

    if not os.path.exists('tmp'):
        print('Creating tmp directory.')
        os.mkdir('tmp')

    print('Desinstalando APK actual.')
    os.system(f'{adb_command} shell pm uninstall -k {wa_package}')

    print(f'Instalando APK legacy: {wa_apk}')
    os.system(f'{adb_command} install -r -d bin\\{wa_apk}')
    print('¡Instalación completa!')

    print('Respaldando datos.')
    print('\nNota: No pongas ninguna contraseña.\n')
    os.system(f'{adb_command} backup -f tmp\\whatsapp.ab {wa_package}')

    print('\nPlease confirm the backup operation is complete and tmp/whatsapp.ab is present.')
    input('Press Enter to continue after backup is complete...')

    print('Extracting tmp\\whatsapp.ab file.')
    with open('tmp/whatsapp.ab','rb') as inp:
        with open('tmp/whatsapp.tar','wb') as out:
            out.write(b'\x1f\x8b\x08\x00\x00\x00\x00\x00')
            inp.read(24)
            while True:
                b = inp.read(512)
                if not b:
                    break
                out.write(b)

    with tarfile.open('tmp\\whatsapp.tar') as tp:
        tp.extractall(path='tmp')
    print("\nExtracted folder structure:")
    for root, dirs, files in os.walk('tmp'):
        level = root.replace('tmp', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        for name in files:
            print(f"{indent}  {name}")

    print('Creating out directory.')
    if not os.path.exists('out'):
        os.mkdir('out')

    print('Copying android db')
    if os.path.exists(wa_db_path):
        shutil.copyfile(wa_db_path,'out\\android.db')
    else:
        print(f'ERROR: No se encontró el archivo {wa_db_path}. La copia de seguridad puede estar incompleta o no contener los datos de WhatsApp.')
        print('Verifica que el backup se realizó correctamente y que el archivo existe antes de continuar.')
        exit(1)
    print('Cleaning up...')
    print('Deleting tmp directory.')
    shutil.rmtree('tmp')
    print('Stopping adb.')
    os.system(f'{adb_command} kill-server')


    print('\nYou can now safely remove your android device.')
print('\nPlease follow below steps to restore whatsapp backup to your iphone:')
print('\t1. Login into whatsapp with the same number in your iphone.')
print('\t   If already logged in, script will preverse iphone chats also.')
print('\n\t2. Disable \'Find My iPhone\' option in your iphone.')
print('\n\t3. Create an unencrypted local backup using iTunes.')

input('Press enter to conitnue...')
print('Looking for iphone backup.')

root_loc_exists = False
for tmp_root_loc in iphone_backup_root_locs:
    if os.path.exists(tmp_root_loc):
        root_loc_exists = True
        iphone_backup_root_loc = tmp_root_loc
        break

if not root_loc_exists:
    print('Backup directory is missing.')
    exit(2)

dirnames = os.listdir(iphone_backup_root_loc)
if len(dirnames)==0:
    print('No backup found.')
    exit(3)
elif len(dirnames)>1:
    print('Multiple backups found.')
    iphone_backup_loc = input('Please enter backup folder path: ')
else:
    iphone_backup_loc = os.path.join(iphone_backup_root_loc,dirnames[0])

manifest_db_path = os.path.join(iphone_backup_loc,'Manifest.db')
if not os.path.exists(manifest_db_path):
    print('Manifest.db is missing.')
    exit(4)

print('Looking for whatsapp data in iphone backup.')
manifest_db = sqlite3.connect(manifest_db_path)

chatstorage = list(manifest_db.execute("SELECT fileID FROM Files WHERE relativePath='ChatStorage.sqlite' AND domain='AppDomainGroup-group.net.whatsapp.WhatsApp.shared'"))
if len(chatstorage)!=1:
    print('Error finding whatsapp data. Terminating!')
    exit(5)

chatstorage_path = os.path.join(iphone_backup_loc,chatstorage[0][0][:2],chatstorage[0][0])

shutil.copyfile(chatstorage_path,'out\\ios.db')
print('Backup copied.\n')
uid = input("Enter phone number with country code, eg: 9185XXXXXXXX: ")
print('Starting migration script.')
os.system('python migrate.py -adb out\\android.db -idb out\\ios.db -u {}'.format(uid))

print('Migration complete!')
print('Updating iphone backup')
shutil.copyfile('out\\out.db',chatstorage_path)
print('Deleting out directory.')
shutil.rmtree('out')
print('\n\t4. Restore local backup and start the whatsapp.')
print('\n\n\t   Note: To fix any buggy behaviour after the restoration, backup iphone whatsapp to icloud and reinstall it.')