import time
from picamera2 import Picamera2, Preview
import os
import cv2  # OpenCV pour l'affichage des images

# Importation de la fonction show_image
from exception import show_image


class DualCameraCapture:
    def __init__(self, left_cam_id=0, right_cam_id=1, preview_size=(800, 600),
                 preview_type=Preview.QTGL, capture_delay=0, interval=5):
        """
        Initialise la classe DualCameraCapture avec les paramètres de la caméra.

        :param left_cam_id: ID de la caméra gauche (par défaut 0)
        :param right_cam_id: ID de la caméra droite (par défaut 1)
        :param preview_size: Taille de l'aperçu (par défaut (800, 600))
        :param preview_type: Type d'aperçu (par défaut Preview.QTGL)
        :param capture_delay: Délai avant la capture d'image (par défaut 0)
        :param interval: Intervalle entre les captures d'images (par défaut 5)
        """
        self.left_cam_id = left_cam_id
        self.right_cam_id = right_cam_id
        self.preview_size = preview_size
        self.preview_type = preview_type
        self.capture_delay = capture_delay
        self.interval = interval

    def capture_and_save_image(self, picam_id, filename):
        """
        Capture et sauvegarde une image depuis la caméra spécifiée.

        :param picam_id: ID de la caméra à utiliser
        :param filename: Nom du fichier dans lequel sauvegarder l'image
        """
        # Création d'une instance de Picamera2 avec l'ID spécifié
        picam = Picamera2(picam_id)
        # Création de la configuration d'aperçu avec la taille spécifiée
        preview_config = picam.create_preview_configuration(main={"size": self.preview_size})
        picam.configure(preview_config)
        # Démarrage de l'aperçu de la caméra avec le type d'aperçu spécifié
        picam.start_preview(self.preview_type)
        # Démarrage de la capture
        picam.start()
        # Délai pour permettre à la caméra de se stabiliser avant la capture
        time.sleep(self.capture_delay)
        # Capture de l'image et sauvegarde dans le fichier spécifié
        metadata = picam.capture_file(filename)
        print(f"Image capturée {filename}: {metadata}")
        # Fermeture de la caméra après la capture
        picam.close()

    def display_images(self, left_filename, right_filename):
        """
        Affiche les images capturées à partir des fichiers spécifiés.

        :param left_filename: Nom du fichier de l'image gauche
        :param right_filename: Nom du fichier de l'image droite
        """
        # Lecture des images à partir des fichiers spécifiés
        left_image = cv2.imread(left_filename)
        right_image = cv2.imread(right_filename)

        # Affichage des images à l'aide de la fonction show_image importée
        show_image("Image Gauche", left_image, cmap='gray')
        show_image("Image Droite", right_image, cmap='gray')

    def validate_images(self):
        """
        Valide si les images capturées sont acceptables.

        :return: True si les images sont acceptables, sinon False
        """
        while True:
            # Demande à l'utilisateur de valider les images
            user_input = input("Les images sont-elles acceptables ? (y/n) : ").strip().lower()
            if user_input in ["y", "n"]:
                # Retourne True si l'utilisateur accepte les images, sinon False
                return user_input == "y"
            print("Entrée invalide. Veuillez taper 'y' ou 'n'.")

    def capture_images(self, nbr_photos, image_folder):
        """
        Capture un nombre spécifié de paires d'images et les sauvegarde dans le dossier spécifié.

        :param nbr_photos: Nombre de paires d'images à capturer
        :param image_folder: Dossier où sauvegarder les images
        """
        photo_counter = 0
        while photo_counter < nbr_photos:
            # Attendre avant de capturer la prochaine paire d'images
            time.sleep(self.interval)
            # Définition des noms de fichiers pour les images gauche et droite
            left_filename = os.path.join(image_folder, f'left_{str(photo_counter + 1).zfill(2)}.png')
            right_filename = os.path.join(image_folder, f'right_{str(photo_counter + 1).zfill(2)}.png')

            # Capture et sauvegarde des images pour la caméra gauche et droite
            self.capture_and_save_image(self.left_cam_id, left_filename)
            self.capture_and_save_image(self.right_cam_id, right_filename)

            # Affichage des images capturées pour validation
            self.display_images(left_filename, right_filename)

            # Validation des images par l'utilisateur
            if self.validate_images():
                photo_counter += 1
                print(f'Capture de la paire No {photo_counter}')
            else:
                print("Reprise des images...")
