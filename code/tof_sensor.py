import sys  # Importation pour la gestion des exceptions et des opérations système
import cv2  # Importation d'OpenCV pour le traitement d'images
import numpy as np  # Importation de NumPy pour les opérations mathématiques
import ArducamDepthCamera as ac  # Importation de la bibliothèque pour la caméra Arducam ToF
from depth_traitement import DepthMapProcessor  # Importation de la classe pour le traitement de la carte de profondeur


class TofCamera:
    def __init__(self, max_distance=4):
        """
        Initialise la caméra ToF avec les paramètres de distance maximale.

        :param max_distance: Distance maximale mesurable par la caméra en mètres
        """
        self.cam = ac.ArducamCamera()  # Création d'une instance de la caméra Arducam
        self.max_distance = max_distance  # Distance maximale pour normaliser la profondeur
        self.frame = None  # Cadre actuel capturé par la caméra
        self.amplitude_buf = None  # Tampon pour les données d'amplitude
        self.depth_buf = None  # Tampon pour les données de profondeur
        self.depth_normalized = None  # Carte de profondeur normalisée pour affichage
        self.result_image = None  # Image résultante après traitement
        self.n = 0  # Compteur pour le nom des images sauvegardées

    def process_frame(self) -> np.ndarray:
        """
        Traite le cadre capturé pour produire une image résultante en combinant les données de profondeur
        et d'amplitude.

        :return: Image résultante après traitement
        """
        if self.depth_buf is None or self.amplitude_buf is None:
            raise ValueError("Le tampon de profondeur et le tampon d'amplitude ne doivent pas être None.")

        # Conversion des valeurs NaN en zéro pour le tampon de profondeur
        self.depth_buf = np.nan_to_num(self.depth_buf)
        # Seuil des données d'amplitude
        self.amplitude_buf = np.where(self.amplitude_buf <= 7, 0, 255)

        # Normalisation des données de profondeur
        normalized_depth = (1 - (self.depth_buf / self.max_distance)) * 255
        normalized_depth = np.clip(normalized_depth, 0, 255).astype(np.uint8)
        self.depth_normalized = normalized_depth
        # Combinaison des données de profondeur normalisées et d'amplitude
        result_frame = normalized_depth & self.amplitude_buf.astype(np.uint8)
        return result_frame

    def capture_image(self):
        """
        Sauvegarde l'image résultante sous le nom tof{n}.png.
        """
        if self.result_image is not None:
            cv2.imwrite(f"tof{self.n}.png", self.result_image)
            print(f"Image sauvegardée sous le nom tof{self.n}.png")
            self.n += 1
        else:
            print("Aucune image à sauvegarder")

    def process_tof(self):
        """
        Traite la carte de profondeur en utilisant DepthMapProcessor pour analyser et extraire les contours.
        """
        processor = DepthMapProcessor(
                depth_map=self.depth_buf,
                disparity=self.depth_normalized,
                pixel_min=18000,
                min_contour_area=20,
                thresholds=[50, 100, 200, 255],
                kernel_size=5,
                dilate_iterations=1,
                erode_iterations=3
            )
        processor.process_disparity_image()

    def continuous_display(self):
        """
        Capture et affiche les images en continu à partir de la caméra ToF, avec des options pour sauvegarder
        et traiter les images.
        """
        # Ouverture de la connexion à la caméra ToF et démarrage du flux de données de profondeur
        if self.cam.open(ac.TOFConnect.CSI, 0) != 0 or self.cam.start(ac.TOFOutput.DEPTH) != 0:
            print("Échec de l'initialisation ou du démarrage de la caméra")
            sys.exit(1)

        # Configuration de la distance maximale de la caméra
        self.cam.setControl(ac.TOFControl.RANG, self.max_distance)

        try:
            while True:
                # Capture d'une trame depuis la caméra
                self.frame = self.cam.requestFrame(200)
                if self.frame is not None:
                    # Obtention des données de profondeur et d'amplitude
                    self.depth_buf = self.frame.getDepthData()
                    self.amplitude_buf = self.frame.getAmplitudeData()
                    self.cam.releaseFrame(self.frame)  # Libération de la trame après traitement

                    # Normalisation et traitement des données d'amplitude
                    self.amplitude_buf = np.clip(self.amplitude_buf * (255 / 1024), 0, 255)

                    # Traitement du cadre pour obtenir l'image résultante
                    self.result_image = self.process_frame()
                    # Application d'une carte de couleur pour améliorer l'affichage
                    self.result_image = cv2.applyColorMap(self.result_image, cv2.COLORMAP_JET)

                    # Affichage de l'image résultante
                    cv2.imshow("ToF Camera", self.result_image)

                    # Gestion des entrées clavier
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):  # Quitter si la touche 'q' est pressée
                        break
                    elif key == ord('s'):  # Sauvegarder l'image si la touche 's' est pressée
                        self.capture_image()
                    elif key == ord('t'):  # Traiter les données de profondeur si la touche 't' est pressée
                        self.process_tof()
                else:
                    print("Échec de la capture de la trame")

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()  # Nettoyage des ressources à la fin de l'exécution

    def cleanup(self):
        """
        Arrête et ferme la caméra, et détruit toutes les fenêtres OpenCV.
        """
        self.cam.stop()
        self.cam.close()
        cv2.destroyAllWindows()

    def get_depth_buf(self):
        """
        Retourne le tampon de profondeur actuel.

        :return: Tampon de profondeur
        """
        return self.depth_buf

    def get_depth_normalized(self):
        """
        Retourne la carte de profondeur normalisée.

        :return: Carte de profondeur normalisée
        """
        return self.depth_normalized
