import multiprocessing
from time import sleep
import cv2
import psutil
import sys
import os
import shutil
import signal

from tof_sensor import TofCamera
from stereo_vision import StereoVision, DualCameraCapture
from calibration_camera import Calibrator
from exception import folder_create


def calibrate_cameras(cam_capture):
    print("Début de la calibration des caméras...")
    
    # Paramètres de calibration
    img_width = 800
    img_height = 600
    image_size = (img_width, img_height)
    
    # Prendre les photos nécessaires pour la calibration
    nbr_photos = int(input("Donner le nombre d'images à prendre pour la calibration : "))
    rows = int(input("Donner le nombre de lignes sur l'échéquier : "))
    columns = int(input("Donner le nombre de colonnes sur l'échéquier : "))
    square_size = 2.4  # Taille du carré de l'échéquier
    
    cam_capture.capture_images(nbr_photos=nbr_photos, image_folder="image")

    calibrator = Calibrator(rows, columns, square_size, image_size)
    calibration = calibrator.calibration_process(nbr_photos, 'image')

    # Sauvegarde des données de calibration
    calibration.save('data')

    print("Calibration terminée.")


def run_tof_camera(camera_queue):
    tof_camera = TofCamera(max_distance=4)
    tof_camera.continuous_display()
    while True:
        depth_buf = tof_camera.get_depth_buf()
        depth_normalized = tof_camera.get_depth_normalized()
        if depth_buf is not None and depth_normalized is not None:
            camera_queue.put((depth_buf, depth_normalized))
        sleep(1)


def run_stereo_vision():
    img_width = 800
    img_height = 600
    image_size = (img_width, img_height)
    cam_capture = DualCameraCapture(left_cam_id=2, right_cam_id=1, preview_size=image_size)
    stereo_vision = StereoVision(cam_capture)
    stereo_vision.process_and_display()

    disparity_normalized = stereo_vision.disparity_normalized
    depth = stereo_vision.depth
    return disparity_normalized, depth


def terminate_processes(processes):
    """ Termine les processus donnés. """
    for proc in processes:
        if proc.is_alive():
            proc.terminate()
            proc.join()


def kill_zombie_processes():
    """Termine les processus zombies."""
    for proc in psutil.process_iter(['pid', 'status']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                print(f"Processus zombie détecté : PID {proc.info['pid']}")
                os.kill(proc.info['pid'], signal.SIGKILL)
                print(f"Processus zombie {proc.info['pid']} tué.")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"Erreur en traitant le processus {proc.info['pid']}: {e}")


def clean_temp_dirs(directories):
    """Nettoie les répertoires temporaires spécifiés."""
    for directory in directories:
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Erreur en nettoyant {file_path}: {e}")
        except Exception as e:
            print(f"Erreur en nettoyant {directory}: {e}")


def cleanup():
    """Effectue les opérations de nettoyage."""
    kill_zombie_processes()
    clean_temp_dirs(['/tmp', '/var/tmp'])
    print("Mémoire libérée.")
    print("Nettoyage du système terminé.")


if __name__ == "__main__":
    cleanup()
    folder_create('data')
    folder_create('image')
    folder_create('corner')

    calib_choice = input("Voulez-vous calibrer les caméras (y/n) ? ").strip().lower()

    if calib_choice == "y":
        cam_capture = DualCameraCapture(left_cam_id=2, right_cam_id=1, preview_size=(840, 820))
        calibrate_cameras(cam_capture)
    elif calib_choice == "n":
        print("Les caméras ne seront pas calibrées.")
    else:
        print("Choix invalide. Veuillez entrer 'y' ou 'n'.")
        exit(1)

    # Initialisation des queues pour la communication entre processus
    camera_queue = multiprocessing.Queue()

    # Création des processus
    tof_process = multiprocessing.Process(target=run_tof_camera, args=(camera_queue,))
    stereo_process = multiprocessing.Process(target=run_stereo_vision)

    # Démarrage des processus
    tof_process.start()
    stereo_process.start()

    processes = [tof_process, stereo_process]

    # Attente de la fin des processus
    try:
        # Maintenir les processus en vie
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Interruption détectée. Arrêt des processus...")
    finally:
        # Arrêt des processus
        terminate_processes(processes)
        print("Tous les processus ont été arrêtés.")
        cleanup()
        sys.exit(0)
