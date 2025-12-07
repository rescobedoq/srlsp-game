#srlsp-game/src/signperu/games/PalabraN_ah.py
from random import choice 

ArchivoExterno=open("signperu/games/PALABRAS","r")
ListaPalabras=[]

for palabra in ArchivoExterno:
    PalabraCorregida=palabra.upper().removesuffix("\n")
    if PalabraCorregida!="":ListaPalabras.append(PalabraCorregida)

def PalabraNueva():
    try: return(choice(ListaPalabras))
    except:return("signperu/games/PALABRAS")

if __name__=="__main__":
    print(PalabraNueva())