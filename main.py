# Importem les llibreries que necessitem per desenvolupar el programa
import urllib
import re
from bs4 import BeautifulSoup
import pandas as pd
import os

''' Per tal de no massificar les consultes, demanem a l'usuari que introdueixi  el rang d'anys de
les películes que vol consultar'''

print("Benvinguts al programa de web-scraping de FilmAffinity.")
rang_any = input("Introdueix un rang d'anys, separats per '-', vols fer la cerca. Disponible des de 1900 fins 2019 \n")
# Separem les diferents lletres i ho convertim tot en MAYUS
rang_any = rang_any.split('-')
# Si s'introdueix un caràcter no acceptat, es dóna error i s'acaba el programa
for y in rang_any:
    try:
       y = int(y)
    except ValueError:
        print("Valor introduït no numèric!")

print('Introdueix el país que vols cercar.')
sel_pais = input("Codis disponibles: USA, ESP, FRA, UK, GER, ITA, ARG, JPN i ALL \n")
pais_admes = ['USA', 'ESP', 'FRA', 'UK', 'GER', 'ITA', 'ARG', 'JPN', 'ALL']
if sel_pais not in pais_admes:
    print('El país introdüit no està dins el llistat disponible. Si us plau, introdueixi un país del llistat')
    exit()

# Diccionari convertir en ISO-2 dels països 
dic_pais = {'USA' : 'US', 'ESP' : 'ES', 'FRA':'FR', 'UK':'GB', 'GER':'DE', 'ITA':'IT', 'ARG': 'AR', 'JAP':'JP', 'ALL':''}

# Comptador de películes descarregades
cont = 0

# Llistat que contindrá els IDs de les películes per poder descarregar la informació de la taula
ids = []

# Inicialització dels diferents camps que descarreguerem
id_code = []
nom = []
year = []
durada = []
pais = []
direccio = []
guionista = []
musica = []
fotografia = []
productora = []
actors = []
genere = []
nota = []
vots = []
web = []

# Creació d'un dataframe per emmagatzemar les IDs de les pelicules
movies_id = pd.DataFrame([], columns = ['id'])

# Definició de la funció per a descarregar la URL
def dl_URL(url, user_agent="Sergi_MR", num_retries=2):
    # Identificador de l'usuari
    headers = {'User-agent': user_agent}
    # Request de la URL
    request = urllib.request.Request(url=url, headers=headers)
    print("Downloading:", url)
    try:
        html = urllib.request.urlopen(request)
    # En cas de no poder accedir a la URL, detallem l'error obtingut
    except urllib.error.URLError as e:
        print("Download error:", e.reason)
        html = None
        if num_retries > 0:
            # Per errors del tipus HTTP 5XX, tornem a provar la connexió
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return dl_URL(url, user_agent, num_retries - 1)
    return html

# Definició de la funció que llegeix les pelicules a descarregar
def getFilms(ids):
    new_movies_id = pd.DataFrame(ids, columns=['id'])

    # Emmagatzemem la ID de cada nova pelicula
    global movies_id
    movies_id = movies_id.append(new_movies_id, ignore_index = True)
    movies_id = movies_id.drop_duplicates()

    # Descarreguem la pàgima HTML per a cada película
    for j in movies_id['id']:
        movie_url = "https://www.filmaffinity.com/es/film" + str(int(j)) + ".html"
        movie = dl_URL(movie_url)
        if movie is not None:

            # Realitzem l'scrap de la web de la película. Si la funció retorna True parem el bucle perquè ens han banejat
            if scrap(j, movie):
                print("Error en el scrap. Possible 'Too many requests.' Comprova si la web https://www.filmaffinity.com es carrega correctament.")
                print('En cas de no fer-ho, deixa passar uns minuts')
                break
            # Sumem +1 al contador de películes descarregades
            global cont
            cont += 1

# Definición de la funció per realitzar l'scrap
def scrap(id, movie):
    # Convertim a parser el codi HTML per tal de navegar per les etiquetes
    soup = BeautifulSoup(movie, 'html.parser')

    # Busquem entre les etiquetes la que tengui la classe movie-info
    dl = soup.find('dl', attrs={'class': 'movie-info'})

    if dl is None:
        # En cas de no trobar l'etqiueta, parem. Possible 'Too many requests'
        return True
    else:
        # Seleccionem el primer element dd
        dd = dl.find('dd')
        if dd != None:
            titulo = dd.text.strip()
            
            # Eliminem la paraula 'aka' en els casos en què estigui en el titol
            if titulo[-3:] == 'aka': titulo = titulo[:-3].strip()

        else:
            titulo = 'NA'

        # Extracció d'any
        dl = soup.find('dd', attrs={'itemprop': 'datePublished'})
        if dl != None:
            año = dl.text.strip().split()[0]
        else:
            año = 'NA'

        # Extracció de duració
        dl = soup.find('dd', attrs={'itemprop': 'duration'})
        if dl != None:
            duracion = dl.text.strip().split()[0]
        else:
            duracion = 'NA'

        # Extracció de país
        span = soup.find('span', attrs={'id': 'country-img'})
        img = span.find_all('img')[0]['alt']
        if img != None:
            ctry = img
        else:
            ctry = 'NA'

        # Extracció de direcció
        a_directores = []
        direccion = soup.find('dd', attrs={'class': 'directors'})
        if direccion is None:
            a_directores.append('NA')
        else:
            for directors in direccion.find_all('span', attrs={'itemprop': 'director'}):
                directors_name = directors.find('span', attrs={'itemprop': 'name'})
                a_directores.append(directors_name.text.strip())

        # Extracció de guió, música, fotografía i productora
        a_guion = []
        a_musica = []
        a_fotografia = []
        a_productora = []
        creditos = soup.dd

        while creditos is not None:
            tagPrevio = creditos.find_previous_sibling('dt')

            if (tagPrevio.text.strip() == 'Guion'):

                for g in creditos.find_all('span', attrs={'class': 'nb'}):
                    g = g.span

                    a_guion.append(g.text.strip())
            if (tagPrevio.text.strip() == 'Música'):

                for musico in creditos.find_all('span', attrs={'class': 'nb'}):
                    musico = musico.span

                    a_musica.append(musico.text.strip())
            if (tagPrevio.text.strip() == 'Fotografía'):

                for fotografo in creditos.find_all('span', attrs={'class': 'nb'}):
                    fotografo = fotografo.span

                    a_fotografia.append(fotografo.text.strip())
            if (tagPrevio.text.strip() == 'Productora'):

                for productor in creditos.find_all('span', attrs={'class': 'nb'}):
                    productor = productor.span

                    a_productora.append(productor.text.strip())
            creditos = creditos.find_next_sibling('dd')
        if not a_guion:
            a_guion.append('NA')
        if not a_musica:
            a_musica.append('NA')
        if not a_fotografia:
            a_fotografia.append('NA')
        if not a_productora:
            a_productora.append('NA')

        # Extracció de repartiment
        a_actores =[]
        for act in soup.find_all('span', attrs={'itemprop': 'actor'}):
            if act is None:
                a_actores.append('NA')
                break
            else:
                actors_name = act.find('span', attrs={'itemprop': 'name'})
                a_actores.append(actors_name.text.strip())

        # Extracció de gènere
        a_genero = []
        for genero in soup.find_all("span", attrs={'itemprop': 'genre'}):
            if genero is None:
                a_genero.append('NA')
                break
            else:
                a_genero.append(genero.a.contents)

        # Extracciñó de la nota mitjana
        dl = soup.find('div', attrs={'id': 'movie-rat-avg'})
        if dl != None:
            nota_mig = dl.text.strip()
        else:
            nota_mig = 'NA'

        # Extracció del nombre de votacions
        dl = soup.find('div', attrs={'id': 'movie-count-rat'})
        if dl != None:
            dl.span
            votaciones = dl.text.strip().split()[0]
        else:
            votaciones = 'NA'

        # Afegim a les dades a les llistes corresponents
        id_code.append(id)
        nom.append(titulo)
        year.append(año)
        durada.append(duracion)
        pais.append(ctry)
        direccio.append(a_directores)
        guionista.append(a_guion)
        musica.append(a_musica)
        fotografia.append(a_fotografia)
        productora.append(a_productora)
        actors.append(a_actores)
        genere.append(a_genero)
        nota.append(nota_mig)
        vots.append(votaciones)
        web.append("https://www.filmaffinity.com/es/film" + str(int(id)) + ".html")

# Definició de la funció d'emmagatzament de les dades
def saveData(id_code, nom, year, durada, pais, direccio, guionista, musica,
fotografia, productora, actors, genere, nota, vots, web):

    if os.path.exists('db_FA.csv'): 
        df = pd.read_csv('db_FA.csv')
    else:
        df = pd.DataFrame({'Id': [],
                           'Titol': [],
                           'Any': [],
                           'Duracio (min)': [],
                           'Pais': [],
                           'Direcció': [],
                           'Guió': [],
                           'Música': [],
                           'Fotografia': [],
                           'Productora': [],
                           'Repartiment': [],
                           'Gènere': [],
                           'Nota':[],
                           'Num. vots': [],
                           'Web': [],
                           },
                          columns=['Id', 'Titol', 'Any', 'Duracio (min)', 'Pais', 'Direcció', 'Guió', 'Música', 'Fotografia', 'Productora', 'Repartiment', 'Gènere', 'Nota', 'Num. vots', 'Web'])

        
    # Creem un nou DF amb les noves dades
    new_df = pd.DataFrame({'Id': id_code,
                           'Titol': nom,
                           'Any': year,
                           'Duracio (min)': durada,
                           'Pais': pais,
                           'Direcció': direccio,
                           'Guió': guionista,
                           'Música': musica,
                           'Fotografia': fotografia,
                           'Productora': productora,
                           'Repartiment': actors,
                           'Gènere': genere,
                           'Nota': nota,
                           'Num. vots': vots,
                           'Web': web,
                           },
                          columns=['Id', 'Titol', 'Any', 'Duracio (min)', 'Pais', 'Direcció', 'Guió', 'Música', 'Fotografia', 'Productora', 'Repartiment', 'Gènere', 'Nota', 'Num. vots', 'Web'])

    # Omplim el DF
    df = pd.concat([df, new_df])
    
    # Guardem el DF al disc
    df.to_csv('db_FA.csv', index = False , encoding='utf-8')

# Consulta principal - Bucle per consultar cada una de les pàgines --> Suposem que sempre hi ha 500 pelicules (màxim permès de FA)
ids=[]
for i in range(25):
    url = "https://www.filmaffinity.com/es/advsearch.php?page=" + str(i+1) + "&stype[]=title&country=" + dic_pais[sel_pais] + "&genre=&fromyear=" + rang_any[0] + "&toyear=" + rang_any[1]
    page = dl_URL(url)
    # Si la pàgina descarregada està buida, tornem error
    if page is None:
        break
    else:
        content = page.read()
        # Si arribem al límit de peticions al servidor, parem el búcle principal
        if re.search('Too many requests', str(content)):
            print("Error: Too many requests")
            stop = True
            break
        else:
            # Extraiem els identificadors de les pelicules i les guardem en una llista
            id = re.findall('data-movie-id="(.*?)"', str(content))
            for j in id:
                if int(j) not in list(movies_id['id']):
                    ids.append(j)

getFilms(ids)
# Cridem la funció SaveData per gaurdar en un CSV la informació descarregada
saveData(id_code, nom, year, durada, pais, direccio, guionista, musica, fotografia, productora, actors, genere, nota, vots, web)

print('Procés completat. Películes descarregades: ', cont)
