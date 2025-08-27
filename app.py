

import streamlit as st
st.title("harvend_artifects")
import sqlite3
import requests
import pandas as pd
from streamlit_option_menu import option_menu

conn = sqlite3.connect("harvard_artifacts.db")
cursor = conn.cursor()
api_key = "db2b6282-2a12-4ac0-949e-105e248d9eae"
url = "https://api.harvardartmuseums.org/object"

#------------------------------------------------ Create 3 SQL tables--------------------------------------------------------------------------------------#


def create_tables():
    cursor.execute("""create table if not exists artifacts_metadata (
                    id integer primary key,
                    title text,
                    culture text,
                    dated text,
                    period text,
                    division text,
                    medium text,
                    dimensions varchar(75),
                    dept text,
                    description text,
                    classification text,
                    accession_year integer,
                    access_method text
)""")
    cursor.execute("""create table if not exists artifacts_media(
                    object_id integer,
                    image_count int,
                    media_count int,
                    color_count int,
                    rank int,
                    datebegin int,
                    dateend int,
                    FOREIGN KEY(object_id)REFERENCES artifacts_metadata(id)

)""")
    cursor.execute("""create table if not exists artifacts_colors(
                  object_id integer,
                  color text,
                  spectrum text,
                  hue text,
                  percentage REAL,
                  css text,
                  FOREIGN KEY(object_id)REFERENCES artifacts_metadata(id)
)""")


create_tables()

# ------------------------------------------------------------------------Data Collection per class-----------------------------------------------------------------#

def classes(api_key,class_name):
    all_records = []


    for page in range(1, 26):
        params = {
            "apikey": api_key,
            "size": 100,
            "page": page,
            "hasimage": 1,
            "classification": class_name
        }

        response = requests.get(url, params=params)

        data = response.json()
        records = data.get('records', [])
        all_records.extend(records)

        return all_records

# Collecting metadata, media and color details

def artifacts_details(records):

      artifacts = []
      media = []
      colors = []

      for i in records:
          artifacts.append(dict(
              id = i['id'],
              title = i['title'],
              culture = i['culture'],
              dated = i['dated'],
              period = i.get('period'),
              division = i['division'],
              medium = i.get('medium'),
              dimensions = i.get("dimensions"),
              dept = i.get("department"),
              desc = i.get('description'),
              classf = i['classification'],
              acc_yr = i['accessionyear'],
              methd = i['accessionmethod']
                          ))

          media.append(dict(
              objid = i['objectid'],
              imgcnt = i['imagecount'],
              medcnt = i['mediacount'],
              col = i['colorcount'],
              rank = i['rank'],
              begin = i['datebegin'],
              dateend = i['dateend']

          ))

          sub_list = i['colors']
          for j in sub_list:
              colors.append(dict(
                  objid = i['objectid'],
                  color = j.get('color'),
                  spec= j.get('spectrum'),
                  hue = j['hue'],
                  percent = j['percent'],
                  css = j['css3']

              ))
              

      return artifacts,media,colors

# ----------------------------------------------------------------------------------Data Insertion -------------------------------------------------------------------#

def insert_values(arti,med,col):
      insert_meta = """insert into artifacts_metadata values(?,?,?,?,?,?,?,?,?,?,?,?,?)"""
      insert_media = """insert into artifacts_media values(?,?,?,?,?,?,?)"""
      insert_col  = """insert into artifacts_colors values(?,?,?,?,?,?)"""

      for i in arti:
          values1 = (i['id'], i['title'], i['culture'],i['dated'], i['period'], i['division'], i['medium'], i['dimensions'], i['dept'], i['desc'], i['classf'], i['acc_yr'], i['methd'])
          cursor.execute(insert_meta,values1)

      for i in med:
          values2 = (i['objid'], i['imgcnt'], i['medcnt'], i['col'], i['rank'], i['begin'], i['dateend'])
          cursor.execute(insert_media,values2)

      for i in col:
          values3 = (i['objid'], i['color'], i['spec'], i['hue'], i['percent'], i['css'])
          cursor.execute(insert_col,values3)

      conn.commit()

 

#---------------------------------------------------------------------------- Streamlit UI ----------------------------------------------------------------------------#

st.set_page_config(layout="wide")



st.markdown("<h3 style='text-align: center; color: black;'>🎨🏛️ Harvard’s Artifacts Collection</h3>", unsafe_allow_html=True)




classification = st.text_input("Enter a classification:") #Coins
button = st.button("Collect data")
menu = option_menu(None,["Select Your Choice","Migrate to SQL","SQL Queries"], orientation="horizontal")




if button:
    if classification != '':
        records = classes(api_key,classification)
        arti ,med,col = artifacts_details(records)
        c1,c2,c3 = st.columns(3)
        with c1:
              st.header("Metadata")
              st.json(arti)
        with c2:
              st.header("Media")
              st.json(med)
        with c3:
              st.header("Colours")
              st.json(col)

    else:
          st.error("Kindly enter a classification")



if menu == 'Migrate to SQL':
    try:
        cursor.execute("select distinct(classification) from artifacts_metadata")
        result = cursor.fetchall()
        classes_list = [i[0] for i in result]

        st.subheader("Insert the collected data")
        if st.button("Insert Data"):
            if classification not in classes_list:
                try:
                    records = classes(api_key, classification)
                    arti, med, col = artifacts_details(records)
                    insert_values(arti, med, col)
                    st.success("✅ Data Inserted successfully")

                    # show inserted tables
                    st.header("Inserted Data:")
                    st.divider()

                    for tbl, name in [
                        ("artifacts_metadata", "Artifacts Metadata"),
                        ("artifacts_media", "Artifacts Media"),
                        ("artifacts_colors", "Artifacts Colors"),
                    ]:
                        st.subheader(name)
                        cursor.execute(f"SELECT * FROM {tbl}")
                        result_tbl = cursor.fetchall()
                        columns = [i[0] for i in cursor.description]
                        df = pd.DataFrame(result_tbl, columns=columns)
                        st.dataframe(df)

                except Exception as e:
                    st.error(f"❌ Error while inserting classification data: {e}")
            else:
                st.warning("⚠️ Classification already inserted!")

    except Exception as e:
        st.error(f"❌ Error while migrating data to SQL: {e}")



elif menu == "SQL Queries":

    option = st.selectbox("Queries",
        ("1.What are the unique cultures represented in the artifacts?",              
        "2.List all artifacts from the 14th century belonging to Italian culture?",
        "3.List all artifacts from the Italian Vessels?",
        "4.List artifact titles ordered by accession year in descending order.",
        "5.How many artifacts are there per department?",
        "6.Which artifacts have more than 1 image?",
        "7.What is the average rank of all artifacts?",
        "8.Which artifacts have a higher colorcount than mediacount?",
        "9.List all artifacts created between 1500 and 1600",
        "10.How many artifacts have no media files?",
        "11.What are all the distinct hues used in the dataset?",
        "12.What are the top 5 most used colors by frequency?",
        "13.What is the average coverage percentage for each hue?",
        "14.List all colors used for a given artifact ID",
        "15.What is the total number of color entries in the dataset?",
        "16.List artifact titles and hues for all artifacts belonging to the Japanese culture",
        "17.List each artifact title with its associated hues",
        "18.Get artifact titles, cultures, and media ranks where the period is not null",
        "19.Find artifact titles ranked in the top 10 that include the color hue 'Grey'",
        "20.How many artifacts exist per classification, and what is the average media count for each?",
        "21.List all artifacts created in the 18th century",
        "22.What are the distinct classifications available in the dataset?",
        "23.Find the artifact titles that have the highest media count",
        "24.How many artifacts belong to the Greek culture?",
        "25.List artifact titles and departments where rank is greater than 50"),
        index=None, placeholder="Select a query")

    if option:

        if option == "1.What are the unique cultures represented in the artifacts?":
            cursor.execute("SELECT DISTINCT culture FROM artifacts_metadata;")

        elif option == "2.List all artifacts from the 14th century belonging to Italian culture?":
            cursor.execute("SELECT id, title, culture, dated FROM artifacts_metadata WHERE dated LIKE '%14th century%' AND culture = 'Italian';")

        elif option == "3.List all artifacts from the Italian Vessels?":
             cursor.execute("SELECT id, title, culture, classification, dated FROM artifacts_metadata WHERE culture = 'Italian' AND classification LIKE '%Vessel%';")
    

        elif option == "4.List artifact titles ordered by accession year in descending order.":
            cursor.execute("SELECT title FROM artifacts_metadata ORDER BY accession_year DESC;")

        elif option == "5.How many artifacts are there per department?":
            cursor.execute("SELECT dept, COUNT(*) FROM artifacts_metadata GROUP BY dept;")

        elif option == "6.Which artifacts have more than 1 image?":
            cursor.execute("SELECT object_id, media_count FROM artifacts_media LIMIT 20;")
            st.write(cursor.fetchall())
        elif option == "7.What is the average rank of all artifacts?":
            cursor.execute("SELECT AVG(rank) FROM artifacts_media;")

        elif option == "8.Which artifacts have a higher colorcount than mediacount?":
            cursor.execute("SELECT * FROM artifacts_media WHERE color_count > media_count;")

        elif option == "9.List all artifacts created between 1500 and 1600":
            cursor.execute("SELECT a.id, a.title, a.culture, a.classification, m.datebegin, m.dateend FROM artifacts_metadata a JOIN artifacts_media m ON a.id = m.object_id WHERE m.datebegin >= 1500 AND m.dateend <= 1600;")
    
        elif option == "10.How many artifacts have no media files?":
            cursor.execute("SELECT COUNT(*) FROM artifacts_media WHERE media_count = 0;")

        elif option == "11.What are all the distinct hues used in the dataset?":
            cursor.execute("SELECT DISTINCT hue FROM artifacts_colors;")

        elif option == "12.What are the top 5 most used colors by frequency?":
            cursor.execute("SELECT hue, COUNT(*) AS frequency FROM artifacts_colors GROUP BY hue ORDER BY frequency DESC LIMIT 5;")

        elif option == "13.What is the average coverage percentage for each hue?":
            cursor.execute("SELECT hue, AVG(percentage) FROM artifacts_colors GROUP BY hue;")

        elif option == "14.List all colors used for a given artifact ID":
                        cursor.execute("SELECT id, title FROM artifacts_metadata LIMIT 20;")  # show first 20 IDs
                        available = cursor.fetchall()
                        st.write("Available Artifact IDs and Titles:")
                        df_avail = pd.DataFrame(available, columns=[i[0] for i in cursor.description])
                        st.dataframe(df_avail)
                 

        elif option == "15.What is the total number of color entries in the dataset?":
            cursor.execute("SELECT COUNT(*) FROM artifacts_colors;")

        elif option == "16.List artifact titles and hues for all artifacts belonging to the Japanese culture":
            cursor.execute("SELECT a.title, c.hue FROM artifacts_metadata a JOIN artifacts_colors c ON a.id = c.object_id WHERE a.culture = 'Japanese';")

        elif option == "17.List each artifact title with its associated hues":
            cursor.execute("SELECT a.title, c.hue FROM artifacts_metadata a JOIN artifacts_colors c ON a.id = c.object_id;")

        elif option == "18.Get artifact titles, cultures, and media ranks where the period is not null":
            cursor.execute("SELECT title, culture, rank FROM artifacts_metadata a JOIN artifacts_media m ON a.id = m.object_id WHERE period IS NOT NULL;")

        elif option == "19.Find artifact titles ranked in the top 10 that include the color hue 'Grey'":
            cursor.execute("SELECT a.id, a.title, c.color, c.hue FROM artifacts_metadata a JOIN artifacts_colors c ON a.id = c.object_id WHERE LOWER(c.hue) LIKE '%grey%' OR LOWER(c.hue) LIKE '%gray%'LIMIT 10;")

        elif option == "20.How many artifacts exist per classification, and what is the average media count for each?":
            cursor.execute("SELECT classification, COUNT(*) AS artifact_count, AVG(media_count) AS avg_media FROM artifacts_metadata a JOIN artifacts_media m ON a.id = m.object_id GROUP BY classification;")

        elif option == "21.List all artifacts created in the 18th century":
            cursor.execute("SELECT * FROM artifacts_metadata WHERE dated = '18th century';")

        elif option == "22.What are the distinct classifications available in the dataset?":
            cursor.execute("SELECT DISTINCT classification FROM artifacts_metadata;")

        elif option == "23.Find the artifact titles that have the highest media count":
            cursor.execute("SELECT a.title FROM artifacts_metadata a JOIN artifacts_media m ON a.id = m.object_id ORDER BY m.media_count DESC LIMIT 1;")

        elif option == "24.How many artifacts belong to the Greek culture?":
            cursor.execute("SELECT COUNT(*) FROM artifacts_metadata WHERE culture = 'Greek';")

        elif option == "25.List artifact titles and departments where rank is greater than 50":
            cursor.execute("SELECT a.title, a.dept FROM artifacts_metadata a JOIN artifacts_media m ON a.id = m.object_id WHERE m.rank > 50;")

        # Fetch & display
        result = cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in cursor.description])
        st.dataframe(df)