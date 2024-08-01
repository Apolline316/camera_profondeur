import os
import cv2
import numpy as np
from exception import file_create


class StereoCalibration:
    def __str__(self):
        """Retourne une représentation en chaîne de caractères des attributs de la classe."""
        output = ""
        for key, item in self.__dict__.items():
            output += key + ":\n"
            output += str(item) + "\n"
        return output

    def __init__(self):
        """Initialise la classe StereoCalibration avec des paramètres par défaut."""
        #: Matrices des caméras (paramètres intrinsèques)
        self.cam_mats = {"left": None, "right": None}
        #: Coefficients de distorsion (D)
        self.dist_coefs = {"left": None, "right": None}
        #: Matrice de rotation (R)
        self.rot_mat = None
        #: Vecteur de translation (T)
        self.trans_vec = None
        #: Matrice essentielle (E)
        self.e_mat = None
        #: Matrice fondamentale (F)
        self.f_mat = None
        #: Transformations de rectification (matrices de rectification 3x3 R1 / R2)
        self.rect_trans = {"left": None, "right": None}
        #: Matrices de projection (matrices de projection 3x4 P1 / P2)
        self.proj_mats = {"left": None, "right": None}
        #: Matrice de conversion de disparité en profondeur (matrice 4x4, Q)
        self.disp_to_depth_mat = None
        #: Boîtes de délimitation des pixels valides
        self.valid_boxes = {"left": None, "right": None}
        #: Cartes d'undistortion pour la remappage
        self.undistortion_map = {"left": None, "right": None}
        #: Cartes de rectification pour la remappage
        self.rectification_map = {"left": None, "right": None}

    def save_data(self):
        """Enregistre les données de calibration dans des fichiers .npy et .csv."""
        try:
            for key, item in self.__dict__.items():
                if isinstance(item, dict):
                    # Enregistre les données pour chaque côté (left, right) si c'est un dictionnaire
                    for side in ("left", "right"):
                        filename = f"{key}_{side}"
                        file_create(self.__dict__[key][side], filename, 'npy', 'data')
                        file_create(self.__dict__[key][side], filename, 'csv', 'data')
                else:
                    # Enregistre les données pour les attributs non-dictionnaires
                    file_create(self.__dict__[key], key, 'npy', 'data')
                    file_create(self.__dict__[key], key, 'csv', 'data')

        except Exception as e:
            print(f"Erreur lors de l'enregistrement des données dans 'data': {e}")

    def rectify(self, frames):
        """Rectifie les images stéréo en utilisant les cartes de rectification et d'undistortion."""
        new_frames = []
        for i, side in enumerate(("left", "right")):
            # Applique le remappage pour corriger les distorsions et rectifier les images
            new_frames.append(cv2.remap(frames[i],
                                        self.undistortion_map[side],
                                        self.rectification_map[side],
                                        cv2.INTER_NEAREST))
        return new_frames

    def load_data(self, directory):
        """Charge les paramètres de calibration à partir de fichiers .npy dans le répertoire spécifié."""
        try:
            for key in self.__dict__.keys():
                if isinstance(self.__dict__[key], dict):
                    for side in ("left", "right"):
                        filename = f"{directory}/{key}_{side}.npy"
                        if os.path.exists(filename):
                            # Charge les données pour chaque côté (left, right) depuis les fichiers .npy
                            self.__dict__[key][side] = np.load(filename)
                        else:
                            print(f"Fichier {filename} non trouvé.")
                else:
                    filename = f"{directory}/{key}.npy"
                    if os.path.exists(filename):
                        # Charge les données pour les attributs non-dictionnaires depuis les fichiers .npy
                        self.__dict__[key] = np.load(filename)
                    else:
                        print(f"Fichier {filename} non trouvé.")
            print("Chargement des données terminé avec succès.")
        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")


class Calibrator:
    def __init__(self, row, column, square_size, image_size):
        """Initialise la classe Calibrator avec les paramètres du tableau d'échecs et des images."""
        #: Nombre d'images de calibration
        self.image_count = 0
        #: Nombre de coins internes dans les rangées du tableau d'échecs
        self.row = row
        #: Nombre de coins internes dans les colonnes du tableau d'échecs
        self.column = column
        #: Taille des carrés du tableau d'échecs en centimètres
        self.square_size = square_size
        #: Taille des images de calibration en pixels
        self.image_size = image_size
        #: Coordonnées 3D des coins du tableau d'échecs
        pattern_size = (self.row, self.column)
        corner_coordinates = np.zeros((np.prod(pattern_size), 3), np.float32)
        corner_coordinates[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)
        corner_coordinates *= self.square_size
        #: Coordonnées réelles des coins trouvées dans chaque image
        self.corner_coordinates = corner_coordinates
        #: Liste des coordonnées des coins réels pour faire correspondre les coins trouvés
        self.object_points = []
        #: Liste des coordonnées des coins trouvées dans les images de calibration pour les caméras gauche et droite
        self.image_points = {"left": [], "right": []}

    def corner_detect(self, image_pair):
        """Détecte et affine les coins du tableau d'échecs dans une paire d'images."""
        side = "left"
        self.object_points.append(self.corner_coordinates)

        for image in image_pair:
            img = np.copy(image)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (self.row, self.column))
            if ret:
                # Dessine les coins détectés sur l'image
                cv2.drawChessboardCorners(img, (self.column, self.row), corners, ret)
                cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                 (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 0.01))
                # Sauvegarde l'image avec les coins détectés
                name = "corner/" + side + str(self.image_count + 1).zfill(2) + "corn"
                file_create(img, name, 'png')

            # Ajoute les coins détectés à la liste des points d'image
            self.image_points[side].append(corners.reshape(-1, 2))
            side = "right"
        self.image_count += 1

    def calibrate_camera(self):
        """Calibre les caméras stéréo et calcule les matrices de calibration."""
        criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS,
                    100, 1e-5)
        flags = (cv2.CALIB_FIX_ASPECT_RATIO + cv2.CALIB_ZERO_TANGENT_DIST +
                 cv2.CALIB_SAME_FOCAL_LENGTH)
        calib = StereoCalibration()

        # Effectue la calibration stéréo
        (calib.cam_mats["left"], calib.dist_coefs["left"],
         calib.cam_mats["right"], calib.dist_coefs["right"],
         calib.rot_mat, calib.trans_vec, calib.e_mat, calib.f_mat) = cv2.stereoCalibrate(self.object_points,
                                                                                         self.image_points["left"],
                                                                                         self.image_points["right"],
                                                                                         calib.cam_mats["left"],
                                                                                         calib.dist_coefs["left"],
                                                                                         calib.cam_mats["right"],
                                                                                         calib.dist_coefs["right"],
                                                                                         self.image_size,
                                                                                         calib.rot_mat,
                                                                                         calib.trans_vec,
                                                                                         calib.e_mat,
                                                                                         calib.f_mat,
                                                                                         criteria=criteria,
                                                                                         flags=flags)[1:]
        print("Étape 1 terminée")
        # Calcule les transformations de rectification pour les images
        (calib.rect_trans["left"], calib.rect_trans["right"],
         calib.proj_mats["left"], calib.proj_mats["right"],
         calib.disp_to_depth_mat, calib.valid_boxes["left"],
         calib.valid_boxes["right"]) = cv2.stereoRectify(calib.cam_mats["left"],
                                                         calib.dist_coefs["left"],
                                                         calib.cam_mats["right"],
                                                         calib.dist_coefs["right"],
                                                         self.image_size,
                                                         calib.rot_mat,
                                                         calib.trans_vec,
                                                         flags=0)
        print("Étape 2 terminée")
        # Calcule les éléments pour la rectification des images (partie map)
        for side in ("left", "right"):
            (calib.undistortion_map[side],
             calib.rectification_map[side]) = cv2.initUndistortRectifyMap(
                calib.cam_mats[side],
                calib.dist_coefs[side],
                calib.rect_trans[side],
                calib.proj_mats[side],
                self.image_size,
                cv2.CV_32FC1)
        print("Étape 3 terminée")
        return calib

    def calibration_process(self, nbr_photo, image_folder):
        """Effectue le processus de calibration en utilisant un nombre donné de photos dans le dossier spécifié."""
        photo_counter = 0
        print('Début de la calibration')
        print('Début de la lecture des images')

        # Boucle pour lire un nombre spécifié de paires d'images
        while photo_counter != nbr_photo:
            photo_counter += 1
            print('Importation de la paire No ' + str(photo_counter))
            left_name = image_folder + '/left' + str(photo_counter).zfill(2) + '.jpg'
            right_name = image_folder + '/right' + str(photo_counter).zfill(2) + '.jpg'

            if os.path.isfile(left_name) and os.path.isfile(right_name):
                # Charge les images gauche et droite
                img_left = cv2.imread(left_name, 1)
                img_right = cv2.imread(right_name, 1)
                # Détecte les coins du tableau d'échecs dans les images
                self.corner_detect((img_left, img_right))

        print('Fin du cycle')
        print('Début de la calibration... Cela peut prendre plusieurs minutes !')
        # Calibre les caméras et obtient les paramètres de calibration
        calib = self.calibrate_camera()
        print('Calibration terminée !')

        print('Sauvegarde des données')
        # Sauvegarde les paramètres de calibration
        calib.save_data()
        print('Fin de la sauvegarde des données')

        return calib
