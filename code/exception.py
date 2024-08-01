import os
import cv2
import numpy as np
import csv


def folder_create(folder):
    """
    Cette fonction vérifie si le dossier existe, sinon elle le crée.

    :param folder: Le chemin du dossier à vérifier/créer
    """
    if not os.path.exists(folder):
        # Si le dossier n'existe pas, essayez de le créer
        try:
            # Crée le dossier avec des permissions 777 (lecture, écriture, exécution pour tout le monde)
            os.makedirs(folder, mode=0o777, exist_ok=False)
            print(f"Le dossier '{folder}' a été créé.")
        except Exception as e:
            # Si une erreur se produit lors de la création du dossier, affiche un message d'erreur
            print(f"Une erreur est survenue lors de la création du dossier '{folder}': {e}")
    else:
        # Si le dossier existe déjà, informe l'utilisateur
        print(f"Le dossier '{folder}' existe déjà.")


def file_create(data, file_name, file_type, folder_name=None):
    """
    Cette fonction crée un fichier du type spécifié dans le dossier donné (facultatif).

    :param data: Données à enregistrer dans le fichier
    :param file_name: Nom du fichier à créer (sans extension)
    :param file_type: Type de fichier à créer ('csv', 'image', 'npy', etc.)
    :param folder_name: Dossier dans lequel créer le fichier (facultatif)
    """
    # Construction du chemin complet du fichier
    if folder_name:
        name = folder_name + '/' + file_name + '.' + file_type
    else:
        name = file_name + '.' + file_type

    try:
        # Vérifie le type de fichier et appelle la fonction d'écriture appropriée
        if file_type in ['jpg', 'png']:
            # Pour les images (formats jpg, png), utilise OpenCV pour enregistrer l'image
            cv2.imwrite(name, data)

        elif file_type == 'npy':
            # Pour les fichiers NumPy (.npy), utilise NumPy pour sauvegarder les données
            np.save(name, data)

        elif file_type == 'csv':
            # Pour les fichiers CSV, utilise le module csv pour écrire les données
            with open(name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                for row in data:
                    processed_row = []
                    for item in row:
                        if isinstance(item, (int, float)):
                            # Si l'élément est un nombre, le convertir en chaîne et remplacer le point par une virgule
                            processed_row.append(str(item).replace('.', ','))
                        else:
                            processed_row.append(item)
                    writer.writerow(processed_row)

    except Exception as e:
        # En cas d'erreur lors de la création du fichier, affiche un message d'erreur
        print(f"Une erreur est survenue lors de la création du fichier '{name}': {e}")



def show_image(title, image, cmap='gray'):
    #liste des différentes couleurs d'opencv pour appliquer les couleurs
    colormaps = {
        "autumn": cv2.COLORMAP_AUTUMN,
        "bone": cv2.COLORMAP_BONE,
        "jet": cv2.COLORMAP_JET,
        "winter": cv2.COLORMAP_WINTER,
        "rainbow": cv2.COLORMAP_RAINBOW,
        "ocean": cv2.COLORMAP_OCEAN,
        "summer": cv2.COLORMAP_SUMMER,
        "spring": cv2.COLORMAP_SPRING,
        "cool": cv2.COLORMAP_COOL,
        "hsv": cv2.COLORMAP_HSV,
        "pink": cv2.COLORMAP_PINK,
        "hot": cv2.COLORMAP_HOT,
        "parula": cv2.COLORMAP_PARULA,
        "magma": cv2.COLORMAP_MAGMA,
        "inferno": cv2.COLORMAP_INFERNO,
        "plasma": cv2.COLORMAP_PLASMA,
        "viridis": cv2.COLORMAP_VIRIDIS,
        "cividis": cv2.COLORMAP_CIVIDIS,
        "twilight": cv2.COLORMAP_TWILIGHT,
        "twilight_shifted": cv2.COLORMAP_TWILIGHT_SHIFTED,
        "turbo": cv2.COLORMAP_TURBO,
        "deepgreen": cv2.COLORMAP_DEEPGREEN
    }
    if cmap in colormaps:
        image = cv2.applyColorMap(image, colormaps[cmap])
    elif cmap != 'gray':
        print("La couleur sélectionner n'est pas disponible. Couleur par défaut appliquée")
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()