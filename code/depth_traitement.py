import cv2
import numpy as np
import matplotlib.pyplot as plt
from exception import show_image


class DepthMapProcessor:
    def __init__(self, depth_map, disparity, pixel_min=15000, min_contour_area=10, thresholds=[], kernel_size=5, dilate_iterations=1, erode_iterations=2):
        """
        Initialise la classe DepthMapProcessor avec les paramètres fournis.

        :param depth_map: Carte de profondeur originale
        :param disparity: Carte de disparité normalisée
        :param pixel_min: Nombre minimum de pixels non nuls pour considérer un segment (par défaut 15000)
        :param min_contour_area: Aire minimale pour les contours à considérer (par défaut 10)
        :param thresholds: Liste des seuils pour la segmentation de la disparité
        :param kernel_size: Taille du noyau pour les opérations morphologiques (par défaut 5)
        :param dilate_iterations: Nombre d'itérations pour la dilatation (par défaut 1)
        :param erode_iterations: Nombre d'itérations pour l'érosion (par défaut 2)
        """
        self.depth_map_original = depth_map
        self.depth_map_normalized = disparity
        self.pixel_min = pixel_min
        self.min_contour_area = min_contour_area
        self.thresholds = thresholds
        self.kernel_size = kernel_size
        self.dilate_iterations = dilate_iterations
        self.erode_iterations = erode_iterations
        self.segmented_image = None
        self.contours = []
        self.mean_amplitudes = {}

    def apply_morphological_operations(self, image):
        """
        Applique des opérations morphologiques (dilatation et érosion) à l'image spécifiée.

        :param image: Image à traiter
        :return: Image après application des opérations morphologiques
        """
        # Création du noyau pour les opérations morphologiques
        kernel = np.ones((self.kernel_size, self.kernel_size), np.uint8)
        # Application de la dilatation
        dilated_image = cv2.dilate(image, kernel, iterations=self.dilate_iterations)
        # Application de l'érosion sur l'image dilatée
        eroded_image = cv2.erode(dilated_image, kernel, iterations=self.erode_iterations)
        # Application de la dilatation une seconde fois sur l'image érodée
        dilated_image2 = cv2.dilate(eroded_image, kernel, iterations=self.dilate_iterations)
        return dilated_image2

    def calculate_mean_amplitude(self, contours):
        """
        Calcule l'amplitude moyenne pour chaque contour spécifié.

        :param contours: Liste des contours trouvés dans l'image
        :return: Dictionnaire des amplitudes moyennes pour chaque contour
        """
        self.mean_amplitudes = {}
        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) >= self.min_contour_area:
                # Création d'un masque pour le contour actuel
                mask = np.zeros(self.depth_map_original.shape, dtype=np.uint8)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                # Calcul de l'amplitude moyenne dans la zone du masque
                mean_amplitude = cv2.mean(self.depth_map_original, mask=mask)[0]
                self.mean_amplitudes[i] = mean_amplitude
        return self.mean_amplitudes

    def find_and_draw_contours(self, processed_image):
        """
        Trouve et dessine les contours dans l'image traitée.

        :param processed_image: Image après les opérations morphologiques
        :return: Image avec les contours dessinés
        """
        # Détection des bords avec l'algorithme Canny
        edges = cv2.Canny(processed_image, 50, 150)
        # Trouver les contours dans l'image des bords
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Conversion de l'image traitée en une image couleur pour le dessin des contours
        image_with_contours = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2BGR)

        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) >= self.min_contour_area:
                # Générer une couleur aléatoire pour chaque contour
                color = tuple(np.random.randint(0, 256, size=3).tolist())
                # Dessiner le contour sur l'image
                cv2.drawContours(image_with_contours, [contour], -1, color, 2)
                mean_amplitude = self.mean_amplitudes.get(i, 0)
                if mean_amplitude > 0:
                    # Dessiner l'amplitude moyenne près du contour
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.putText(image_with_contours, f"{mean_amplitude:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        self.contours = contours
        return image_with_contours

    def process_contour(self):
        """
        Traite les contours en appliquant des opérations morphologiques, en trouvant et en dessinant les contours,
        et en calculant les amplitudes moyennes pour les contours trouvés.
        """
        processed_image = self.apply_morphological_operations(self.segmented_image)
        # Affichage de la carte de profondeur normalisée (commenté)
        #show_image('Carte de Profondeur Normalisée', processed_image)
        processed_image_with_contours = self.find_and_draw_contours(processed_image)

        self.mean_amplitudes = self.calculate_mean_amplitude(self.contours)
        for idx, mean_amplitude in self.mean_amplitudes.items():
            print(f'Contour {idx} : Moyenne des Amplitudes = {mean_amplitude:.2f}')
        # Affichage de l'image avec les contours et les amplitudes moyennes (commenté)
        processed_image_with_contours = self.find_and_draw_contours(processed_image)
        show_image('Image avec Contours et Moyennes', processed_image_with_contours)
        cv2.imwrite('contour.png', processed_image_with_contours)

    def process_disparity_image(self):
        """
        Traite l'image de disparité en la segmentant selon les seuils définis, puis en appliquant le traitement de contours
        sur chaque segment.
        """
        # Affichage de la carte de disparité normalisée (commenté)
        #show_image('Carte de Disparité Normalisée', self.depth_map_normalized)

        for i in range(len(self.thresholds) - 1):
            lower_thresh = self.thresholds[i]
            upper_thresh = self.thresholds[i + 1]
            # Création d'un masque pour le seuil actuel
            mask = cv2.inRange(self.depth_map_normalized, lower_thresh, upper_thresh)
            # Application du masque pour extraire la région d'intérêt
            self.segmented_image = cv2.bitwise_and(self.depth_map_normalized, self.depth_map_normalized, mask=mask)

            hist = calculate_histogram(self.segmented_image)
            non_zero_count = count_non_zero_pixels_from_histogram(hist)

            if non_zero_count >= self.pixel_min:
                # Affichage du segment (commenté)
                #show_image(f'Segment {i + 1}: {lower_thresh} - {upper_thresh}', self.segmented_image)
                print(f'Nombre de pixels non nuls pour le segment {i + 1} ({lower_thresh} - {upper_thresh}): {non_zero_count}')
                self.process_contour()
            else:
                print(f'Segment {i + 1} ({lower_thresh} - {upper_thresh}) rejeté : trop peu de pixels non nuls ({non_zero_count})')

def calculate_histogram(image):
    """
    Calcule l'histogramme des valeurs de pixels de l'image.

    :param image: Image à analyser
    :return: Histogramme des valeurs de pixels
    """
    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    return hist.flatten()

def count_non_zero_pixels_from_histogram(hist):
    """
    Compte le nombre de pixels non nuls à partir de l'histogramme des valeurs de pixels.

    :param hist: Histogramme des valeurs de pixels
    :return: Nombre total de pixels non nuls
    """
    return int(np.sum(hist[1:]))

def plot_histogram(title, hist):
    """
    Trace et affiche l'histogramme des valeurs de pixels.

    :param title: Titre du graphique
    :param hist: Histogramme des valeurs de pixels
    """
    plt.figure(figsize=(8, 6))
    plt.title(title)
    plt.plot(hist, color='blue')
    plt.xlabel('Valeur de Disparité')
    plt.ylabel('Nombre de Pixels')
    plt.show()
