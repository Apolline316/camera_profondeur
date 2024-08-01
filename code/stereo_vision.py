import cv2  # Importation d'OpenCV pour le traitement d'images
import numpy as np  # Importation de NumPy pour les opérations mathématiques et le traitement d'images
from multiprocessing import Process, Queue, Event  # Importation des modules pour la gestion des processus
from calibration_camera import StereoCalibration  # Importation de la classe pour la calibration stéréo
from exception import file_create  # Importation de la fonction pour la création de fichiers
from camera_control import DualCameraCapture  # Importation de la classe pour le contrôle des caméras
from depth_traitement import DepthMapProcessor  # Importation de la classe pour le traitement de la carte de profondeur

# Importation de la fonction show_image
from exception import show_image


class StereoVision:
    def __init__(self, cam_capture, baseline=0.06, focale=1300, block_size=15, P1=10 * 15, P2=64, min_disp=-16,
                 max_disp=128,
                 uniqueRatio=4, speckleWindowSize=200, speckleRange=4, disp12MaxDiff=0):
        """
        Initialise les paramètres pour la vision stéréo.

        :param cam_capture: Instance de DualCameraCapture pour capturer les images
        :param baseline: Distance entre les caméras (en mètres)
        :param focale: Focale de la caméra
        :param block_size: Taille du bloc pour la correspondance stéréo
        :param P1: Poids pour la régularisation des coûts d'assignation
        :param P2: Poids pour la régularisation des coûts d'assignation
        :param min_disp: Disparité minimale à considérer
        :param max_disp: Disparité maximale à considérer
        :param uniqueRatio: Ratio d'unicité pour la correspondance stéréo
        :param speckleWindowSize: Taille de la fenêtre pour filtrer les speckles
        :param speckleRange: Plage de valeurs pour filtrer les speckles
        :param disp12MaxDiff: Différence maximale entre les disparités gauche et droite
        """
        self.cam_capture = cam_capture  # Instance de la classe de capture de caméras

        # Chargement des données de calibration stéréo
        self.calibration = StereoCalibration()
        self.calibration.load_data('data')
        self.focale = focale  # Focale calculée pendant la calibration
        self.baseline = baseline  # Distance entre les caméras

        # Dictionnaire pour stocker les images
        self.images = {"left": None, "right": None, "left_rectify": None, "right_rectify": None}

        self.disparity = None
        self.disparity_normalized = None
        self.depth = None

        # Paramètres pour les filtres de la caméra de profondeur
        self.block_size = block_size
        self.min_disp = min_disp
        self.max_disp = max_disp
        self.num_disp = max_disp - min_disp
        self.P1 = P1
        self.P2 = P2
        self.uniquenessRatio = uniqueRatio
        self.speckleWindowSize = speckleWindowSize
        self.speckleRange = speckleRange
        self.disp12MaxDiff = disp12MaxDiff

        # Événement pour arrêter les processus
        self.stop_event = Event()

        self.n = 0  # Compteur pour le nombre d'images sauvegardées

    def stereo_taking(self):
        """
        Capture et rectifie les images stéréo.
        """
        # Capture des images des caméras gauche et droite
        self.cam_capture.capture_and_save_image(self.cam_capture.left_cam_id, 'left.png')
        self.cam_capture.capture_and_save_image(self.cam_capture.right_cam_id, 'right.png')

        # Lecture des images capturées en niveaux de gris
        for side in ("left", "right"):
            self.images[side] = cv2.imread(side + '.png', 0)

        # Rectification des images en utilisant les données de calibration
        rectify_pair = self.calibration.rectify((self.images["left"], self.images["right"]))
        for i, side in enumerate(("left_rectify", "right_rectify")):
            self.images[side] = rectify_pair[i]

    def save_images(self):
        """
        Sauvegarde les images et la carte de disparité normalisée.
        """
        for side in ("left", "right", "left_rectify", "right_rectify"):
            file_create(self.images[side], side + str(self.n), 'png')
        if self.disparity_normalized is not None:
            file_create(self.disparity_normalized, "depthmap" + str(self.n), 'png')
            self.n += 1

    def depth_map_calcul(self):
        """
        Calcule la carte de disparité à partir des images rectifiées.
        """
        # Création de l'objet StereoSGBM pour le calcul de la carte de disparité
        stereo = cv2.StereoSGBM_create(
            minDisparity=self.min_disp,
            numDisparities=self.num_disp,
            blockSize=self.block_size,
            P1=self.P1,
            P2=self.P2,
            uniquenessRatio=self.uniquenessRatio,
            speckleWindowSize=self.speckleWindowSize,
            speckleRange=self.speckleRange,
            disp12MaxDiff=self.disp12MaxDiff)

        # Calcul de la disparité
        self.disparity = stereo.compute(self.images["left_rectify"], self.images["right_rectify"])
        self.disparity = self.disparity.astype(np.float32) / 16.0  # Normalisation pour calculer
        self.disparity[self.disparity < 0] = 0  # Filtrage des valeurs négatives
        # Normalisation pour affichage
        self.disparity_normalized = cv2.normalize(self.disparity, None, alpha=255, beta=0, norm_type=cv2.NORM_MINMAX,
                                                  dtype=cv2.CV_8U)

    def depth_calcul(self):
        """
        Calcule la profondeur pour chaque pixel à partir de la carte de disparité.
        """
        # Initialisation de la profondeur
        self.depth = np.zeros_like(self.disparity)
        valid_disparity_mask = (self.disparity > 0)
        # Calcul de la profondeur
        self.depth[valid_disparity_mask] = self.focale * self.baseline / self.disparity[valid_disparity_mask]

    def process_stereo(self):
        """
        Traite la carte de profondeur en utilisant DepthMapProcessor.
        """
        processor_stereo = DepthMapProcessor(
            depth_map=self.depth,
            disparity=self.disparity_normalized,
            pixel_min=20000,
            thresholds=[50, 100, 200, 255],
            kernel_size=5,
            dilate_iterations=1,
            erode_iterations=2
        )
        processor_stereo.process_disparity_image()

    def capture_and_compute(self, queue):
        """
        Capture les images, calcule la carte de disparité et la profondeur, puis place les résultats dans une file
        d'attente.

        :param queue: File d'attente pour transmettre les résultats entre les processus
        """
        while not self.stop_event.is_set():
            # Capture et traitement des images stéréo
            self.stereo_taking()
            self.depth_map_calcul()
            self.depth_calcul()
            # Place les résultats dans la file d'attente
            queue.put((self.disparity_normalized, self.depth))

        # Assurez-vous que la file d'attente est vide avant de quitter
        queue.put((None, None))  # Envoyer un signal de fin de traitement pour le processus d'affichage

        print("Capture et traitement des images arrêtés.")

    def depth_map_display(self, queue):
        """
        Affiche la carte de disparité et la profondeur à partir des résultats de la file d'attente.

        :param queue: File d'attente pour obtenir les résultats calculés
        """
        while not self.stop_event.is_set() or not queue.empty():
            if not queue.empty():
                self.disparity_normalized, self.depth = queue.get()
                # Application d'une carte de couleur pour améliorer l'affichage
                disparity_normalized_color = cv2.applyColorMap(self.disparity_normalized, cv2.COLORMAP_JET)
                cv2.imshow("disparity", disparity_normalized_color)
                key = cv2.waitKey(1)  # Attendre une courte période pour les événements de la fenêtre
                if key == ord('q'):  # Quitter si la touche 'q' est pressée
                    self.stop_event.set()  # Signaler à l'autre processus de s'arrêter
                elif key == ord('s'):  # Sauvegarder les images et la carte de profondeur si la touche 's' est pressée
                    self.save_images()
                elif key == ord('t'):  # Traiter les images stéréo si la touche 't' est pressée
                    self.process_stereo()
        cv2.destroyAllWindows()

    def process_and_display(self):
        """
        Crée des processus pour la capture et le calcul des images, ainsi que pour l'affichage des résultats.
        """
        queue = Queue()

        # Création des processus
        capture_process = Process(target=self.capture_and_compute, args=(queue,))
        display_process = Process(target=self.depth_map_display, args=(queue,))

        try:
            # Démarrage des processus
            capture_process.start()
            display_process.start()

            # Attente de la fin des processus
            capture_process.join()
            display_process.join()

        except KeyboardInterrupt:
            print("Interruption détectée. Arrêt des processus...")
            self.stop_event.set()  # Signaler aux processus de s'arrêter

        finally:    
            # Assurez-vous que les processus sont terminés correctement
            if capture_process.is_alive():
                capture_process.terminate()
                capture_process.join()

            if display_process.is_alive():
                display_process.terminate()
                display_process.join()

            # Nettoyage des fenêtres OpenCV
            cv2.destroyAllWindows()
