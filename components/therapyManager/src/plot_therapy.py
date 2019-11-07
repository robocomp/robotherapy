import os

from matplotlib import pyplot as plt
import pandas as pd


def save_graph(csvPath, showResults):
    dir = os.path.dirname(csvPath)
    try:
        df = pd.read_csv(csvPath, delimiter=';')
    except:
        print("[ERROR] No se ha encontrado datos para representar")
        return
    else:
        dict_parts = {"upper_trunk": ["LeftArmFlexion", "RightArmFlexion", "LeftArmElevation", "RightArmElevation"],
                      "lower_trunk": ["LeftLegFlexion", "RightLegFlexion", "RightLegElevation", "LeftLegElevation"],
                      "deviations": ['SpineDeviation', 'ShoulderDeviation', 'HipDeviation', 'KneeDeviation']
                      }

        dict_label_color = {"LeftArmFlexion": ["Flexion brazo izquierdo", "yellowgreen"],
                            "RightArmFlexion": [" Flexion brazo derecho", "gold"],
                            "LeftArmElevation": [" Elevacion brazo izquierdo", "darkturquoise"],
                            "RightArmElevation": [" Elevacion brazo derecho", "mediumorchid"],
                            "LeftLegFlexion": ["Flexion pierna izquierda ", "olive"],
                            "RightLegFlexion": ["Flexion pierna derecha ", "goldenrod"],
                            "LeftLegElevation": ["Elevacion pierna izquierda ", "darkcyan"],
                            "RightLegElevation": ["Elevacion pierna derecha ", "darkorchid"],
                            "SpineDeviation": ["Desviacion columna ", "plum"],
                            "ShoulderDeviation": ["Desviacion hombros ", "lightsalmon"],
                            "HipDeviation": ["Desviacion caderas ", "lightblue"],
                            "KneeDeviation": ["Desviacion rodillas ", "palegreen"],
                            }

        # df = df.dropna()
        
        for id, rep in dict_parts.items():
            plt.figure(str(id))
            ax = plt.subplot2grid((5, 5), (0, 0), colspan=5, rowspan=4)
            for part in rep:
                try:
                    # plt.plot('Time', part, data=df)
                    df.plot(x='Time', y=part, ax=ax, label=dict_label_color[part][0], color=dict_label_color[part][1])
                except:
                    "No se pudo representar", str(part)

            plt.xlabel("Tiempo (s)")
            plt.ylabel("Angulo (grados)")
            plt.ylim(0, 180)
            plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=None)
            plt.legend(bbox_to_anchor=(0, -0.2, 1, 0), loc=2, ncol=2, mode="expand", borderaxespad=0, prop={'size': 8})
            plt.savefig(os.path.join(dir, str(id) + ".png"))

        if showResults:
            plt.show()

    return
