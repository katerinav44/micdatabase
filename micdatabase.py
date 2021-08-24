import datetime
import os
import requests

import streamlit as st
from gsheetsdb import connect
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
import matplotlib.pyplot as plt
#from quickstart import create_client_service as service_func
from Google import Create_Service as service_func
from googleapiclient.http import MediaFileUpload
from apiclient import errors



def insert_file(service, title, parent_id, mime_type, filename):
  """Insert new file.

  Args:
    service: Drive API service instance.
    title: Title of the file to insert, including the extension.
    description: Description of the file to insert.
    parent_id: Parent folder's ID.
    mime_type: MIME type of the file to insert.
    filename: Filename of the file to insert.
  Returns:
    Inserted file metadata if successful, None otherwise.
  """
  media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
  body = {
    'title': title,
    'mimeType': mime_type
  }
  # Set the parent folder.
  if parent_id:
    body['parents'] = [{'id': parent_id}]

  try:
    file = service.files().insert(
        body=body,
        media_body=media_body).execute()

    # Uncomment the following line to print the File ID
    # print 'File ID: %s' % file['id']

    return file
  except errors.HttpError as error:
    print ('An error occurred: %s' % error)
    return None

@st.cache(hash_funcs={"_thread.RLock": lambda _: None})
def to_bin(filename_txt, filename_png, image):
    """
    TO BIN
    Converts image inputted by user to binary format
    Saves it to binary png and txt
    """
    img=Image.open(image)
    width = 720
    height = 480
    dims = (width, height)
    img.resize(dims)
    #255 is white, 200 is the threshhold value(a very light gray)
    thresh = 200
    fn = lambda x : 255 if x > thresh else 0
    r = img.convert('L').point(fn, mode='1')
    #0 is for black, 1 is for white
    thresh1 = np.array(r, dtype=int)
    #saving the files to google drive
    #CONNECT TO GDRIVE

    
    API_NAME = 'drive'
    API_VERSION = 'v2'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    service = service_func(st.secrets["web"], API_NAME, API_VERSION, SCOPES)
    image_folder_id = '1uTxBRSkS-E6cC71T0EOCprxwB9vtub20'
    txt_folder_id = '1JYQ79IGsjDWYn4SiMCeRc0h-KTUOyD3_'

    mime_types = ['text/plain', 'image/png']
    txt_path = "bin txt files\\%s" % filename_txt
    png_path = "bin images\\%s" % filename_png
    f = open(txt_path, "w")
    for row in thresh1:
        np.savetxt(f, row, newline = ",", fmt = "%s")
    f.close()
    r.save(png_path)
    txt_file_metadata = insert_file(service, filename_txt, txt_folder_id, mime_types[0], txt_path)
    png_file_metadata = insert_file(service, filename_png, image_folder_id, mime_types[1], png_path)
    return r
    
def scopus_search(DOI):
    """
    SCOPUS SEARCH
    Retrieves article metrics using scopus api.
    Displays error message upon invalid DOI.
    """ 
    root = "https://api.elsevier.com/content/search/scopus/?"
    #print(doi)
    query=f"DOI({DOI})"
    #key = os.environ.get('ELSEVIER_API_KEY')
    key = st.secrets["elsevier_key"]
    payload = {"APIKey":key, "query":query}
    res = requests.get(root, params=payload)
    try:
        res.raise_for_status()
    except Exception as exc:
        print(f"There was a problem: {exc}")
    d = res.json()
    #print(json.dumps(d, indent=4, sort_keys=True))
    try:
        Title = d["search-results"]["entry"][0]['dc:title']
    except KeyError:
        Title = ''
        st.error("Unable to find DOI, please enter a different one.")
        return
    try:
        Author = d["search-results"]["entry"][0]['dc:creator']
    except KeyError:
        Author = ''
    try:
        journal = d["search-results"]["entry"][0]['prism:publicationName']
    except KeyError:
        journal = ''
    try:
        pubdate_str = d["search-results"]["entry"][0]['prism:coverDisplayDate']
        pubdate = datetime.datetime.strptime(pubdate_str, "%d %B %Y").strftime("%d/%m/%Y")
    except KeyError:
        pubdate = ''
    try:
        citedby = d["search-results"]["entry"][0]['citedby-count']
    except KeyError:
        citedby = ''
    article_info = [Title, Author, pubdate, journal, citedby]
    return article_info
           
def add_entry():
    """
    ADD ENTRY PAGE
    Retrieves design info. Checks for missing doi or image. Submit button.
    """
    
    DOI = st.text_input("Enter doi:")
    #get rid of the scopus ones and add a scopus search function
    
    image = st.file_uploader("Image", type = ['png'])
    
    
    width = st.number_input("Channel width:",step=50)
    depth = st.number_input("Channel depth:",step=50)
    inlets = st.number_input("Number of inlets:", step=1)
    outlets = st.number_input("Number of outlets:", step=1)
    material1 = st.text_input("Enter channel material:")
    material2 = st.text_input("Enter electrode/magnet material:")
    material3 = st.text_input("Enter bottom layer material:")
    usecase = st.selectbox("Select a use case", options = ['OOC', 'POC', 'chemical analysis', 'cell analysis'])
    keywords = st.text_input("Enter any other relevant key words:")
    readout = st.text_input("Briefly describe the specific readout/application of the chip:")
    submit_button = st.checkbox(label="add entry")
    if submit_button and (image == None or DOI == ""):
        st.warning("Incomplete submission.")
    if submit_button and image != None and DOI != None:
        confirmation(DOI, image, width, depth, inlets, outlets, material1, material2, material3,  usecase, keywords, readout)

def confirmation(DOI, image, width, depth, inlets, outlets, material1, material2, material3, usecase, keywords, readout):
    """
    CONFIRMATION
    Displays confirmation message upon pressing submit button. 
    Appends new entry to database
    """
    st.write("Please confirm your submission by pressing submit below.")
    #after you press button
    Title, Author, pubdate, journal, citedby = scopus_search(DOI)
    article_info = [Title, Author, pubdate, journal, citedby]
    lastname = Author.split(' ')[0]
    year = pubdate[-4:] 
    filename_txt ="binary{}{}.txt".format(lastname, year)
    filename_png = "binary{}{}.png".format(lastname, year)
    r= to_bin(filename_txt, filename_png, image)
    st.header(article_info[0])
    st.write("Author:", article_info[1],",  Published: ", article_info[2])
    st.write("Journal:", article_info[3], ",  Cited by: ", article_info[4]) 
    st.image(r)
    new_row = [DOI, Title, Author, journal, pubdate, citedby, filename_txt, filename_png, depth, width, inlets, outlets, material1, material2, material2, usecase, keywords, readout]
    checked = st.button(label='Submit')
    if checked:
        #add to pandas database
        st.write("Your entry was submitted successfully")
        append_new_row(new_row)

def append_new_row(new_row):
    #Appends new_row in list format to the Google sheets
    #create a gsheets api service instance
    API_NAME = 'sheets'
    API_VERSION = 'v4'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = service_func(st.secrets["web"], API_NAME, API_VERSION, SCOPES)
    spreadsheet_id = '1wUghvgCPVcVS6-k-vWXVdbLJUfSg0G8KwQEDCDLsPHc'
    # The A1 notation of a range to search for a logical table of data.
    # Values will be appended after the last row of the table.
    range_ = 'Sheet1!A:A'  

    # How the input data should be interpreted.
    value_input_option = 'RAW' 

    # How the input data should be inserted.
    insert_data_option = 'INSERT_ROWS'  

    value_range_body = {
        "values" : [new_row]
    }

    request = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=value_range_body)
    response = request.execute()






def gsheets_connect():
    #CONNECT TO GSHEETS
    #connection object
    conn = connect()
    # Perform SQL query on the Google Sheet.
    # Uses st.cache to only rerun when the query changes or after 1 min.
    @st.cache(ttl=60)
    def run_query(query):
        rows = conn.execute(query, headers=1)
        return rows

    columns = ['DOI', 'Title', 'Author', 'Journal Name', 'Publication Date', 'Cited by', 'Design (bin txt)','Design (png)', 'Channel depth(μm)', 'Channel width(μm)', 'No of Inlets', 'No of Outlets', 'Material (channel)', 'Material (electrode, magnet)', 'Material (bottom)', 'Use Case', 'Keywords', 'Readout']
    sheet_url = st.secrets["public_gsheets_url"]
    rows = run_query(f'SELECT * FROM "{sheet_url}"')
    data = pd.DataFrame(rows, columns= columns)
    
    return data

def search(data):
    """
    Searches data in a use case by keyword
    Displays top 5 articles which match the search and all related info from google sheets 
    """
    columns = ['DOI', 'Title', 'Author', 'Journal Name', 'Publication Date', 'Cited by', 'Design (bin txt)','Design (png)', 'Channel depth(μm)', 'Channel width(μm)', 'No of Inlets', 'No of Outlets', 'Material (channel)', 'Material (electrode, magnet)', 'Material (bottom)', 'Use Case', 'Keywords', 'Readout']
    usecase = st.selectbox("Select a use case", options = ['OOC', 'POC', 'chemical analysis', 'cell analysis'])
    data1 = data[data['Use Case']== usecase]
    st.write(data1)
    keys = st.text_input("Search by keywords")
    keys_list = keys.split()
    stuff1 = data1[data1['Keywords'].str.contains('|'.join(keys_list), case=False, na=False)]
    st.write(stuff1)

    
        
    
    
    

def main():
    """
    MAIN PAGE OF THE DATABASE
    Displays data in a table format.
    Sidebar menu.
    """
    st.title('Microfluidics Database')
    menu = ["View data", "Add entry","Search", "About"]
    
    data = gsheets_connect()
    choice = st.sidebar.selectbox("Menu", menu)
    if choice == "View data":
        ndata = data.drop(labels = 'Design (bin txt)', axis = 1)
        st.dataframe(ndata, 3500, 500)
        st.write("Link to google sheets database: https://docs.google.com/spreadsheets/d/1wUghvgCPVcVS6-k-vWXVdbLJUfSg0G8KwQEDCDLsPHc/edit?usp=sharing")
        st.write("Google Drive folder with Images of the Channel Layout: https://drive.google.com/drive/folders/1uTxBRSkS-E6cC71T0EOCprxwB9vtub20?usp=sharing")
        #histogram of no of pubs per year
        st.subheader("Number of publications per year")
        data['Publication Date'] = pd.to_datetime(data['Publication Date'])
        fig1,ax1 = plt.subplots()
        ax1.hist(data['Publication Date'].dt.year, bins=20, color = 'lightblue', edgecolor='black', align='left')
        st.pyplot(fig1)
        #pie-chart of use-cases
        st.subheader("Use Cases in Dataset")
        labels1 = []
        pie_data = []
        pie = data['Use Case'].value_counts().to_dict()
        for key in pie:
            pie_data.append(pie[key])
            labels1.append(key)
        fig2, ax2 = plt.subplots()
        ax2.pie(pie_data, labels=labels1, shadow=True, startangle=90, colors=['indigo', 'lightblue', 'cyan', 'mediumblue'])
        ax2.axis('equal')
        st.pyplot(fig2)
        #Journal popularity histogram
        st.subheader("Journal popularity")
        series1 = pd.value_counts(data['Journal Name'])
        mask = (series1/series1.sum() * 100).lt(1)
        new1 = series1[~mask]
        new1['Other'] = series1[mask].sum()
        labels2 = []
        bar_data = []
        new1=new1.to_dict()
        for key in new1:
            bar_data.append(new1[key])
            labels2.append(key)
        colors = [plt.cm.tab20b(i/float(len(labels2))) for i in range(len(labels2))]
        fig3, ax3 = plt.subplots(nrows=1, ncols=1, figsize=(15,25))
        ax3.barh(labels2, width = bar_data, height = 0.4, color = colors, align='center')
        st.pyplot(fig3)
        #Channel material waffle chart
        data_copy = data.copy(deep=False)
        st.subheader("Channel Material")
        series = pd.value_counts(data['Material (channel)'])
        mask = (series/series.sum() * 100).lt(1)
        new = series[~mask]
        new['Other'] = series[mask].sum()
        new = new.to_dict()
        labels3 = []
        bar_data2 = []
        for key in new:
           bar_data2.append(new[key])
           labels3.append(key)
        colors = colors = [plt.cm.tab20c(i/float(len(labels3))) for i in range(len(labels3))] 
        fig4, ax4 = plt.subplots()
        ax4.bar(labels3, height=bar_data2, color = colors)
        ax4.set_xticklabels(labels3, rotation=60, horizontalalignment= 'center')
        st.pyplot(fig4)
        st.write("Please visit the About page to learn more about the database and how to add entries.")
    elif choice== "Add entry":
        st.subheader("Add Entry")
        add_entry()
    elif choice == "Search":
        st.subheader("Search")
        search(data)
    elif choice == "About":
        st.subheader("About")
        st.write("Microfluidics is a field which involves manipulating small amounts of fluids on chips measuring only a few centimeters. In this way, microfluidic chips allow complex chemical/biological processes to be performed with higher throughput, increased automation, and reduced waste. Designing a lab-on-chip device is often a tedious, trial-and-error process for scientists. The behavior of fluids in the microfluidics device depends on numerous parameters (channel dimensions, materials, number of inlets/outlets, etc.) which must be carefully selected by scientists to produce the desired readout. Machine Learning (ML) and applied optimization research have the potential to address the problem of mechanical device design. ")
        st.write("The purpose of the microfluidics database is to compile microfluidic device designs documented in the past 20 years of microfluidics research. This database will serve as an important first step towards conducting ML research to optimize device design.")
        st.write("Currently, the database is stored in a google sheets file. It contains microfluidic device designs from microfluidics papers written over the past 20 years. There are 18 columns/features :")
        """
        - DOI: This column contains the digital object identifier of the paper.
        - Title 
        - Author : Contains the first author listed in the paper
        - Journal Name
        - Publication date
        - Cited by: This column contains the number of current citations of the paper
        - Device design (.txt): A binary representation of the top-down view of the device design. The column stores a link to a .txt file containing values of “1” or “0” for each pixel. “0” indicates the presence of a microchannel (black), “1” indicates there is no microchannel (white)
        - Device design (.png) : Contains a black and white png image of the top-down device design
        - Channel depth
        - Channel width
        - Number of inlets
        - Number of outlets
        - Material (channel) : The material used in the fluidic layer of the device
        - Material (electrode, magnet): When the paper talks of electrophoresis or magnetophoresis, this column contains the material used for the electrode(s) or magnet.
        - Material (bottom) : The material used for the bottom layer of the device (if applicable)
        - Use Case: Each paper is sorted into 1 of 4 use cases:
            - Chemical analysis
            - Cell analysis
            - Point-of-care diagnostics (POC)
            - Organ-on-chip (OOC)
        - Keywords: keywords representing the exact application/use of each device
        - Readout: a brief sentence describing the precise application of the device

        """
        st.subheader("A few notes on adding entries")
        """
        1. Image format
            - Columns G and H of the database contain binary txt and png files of the top down image of the channel layout. These images are all standardized to be the same size and colors (black and white). Black(0) indicates the presence of a channel and white(1) indicates no channel. 
            - Make sure the image you use contains no text. The background should be white. Don't worry about resizing or recoloring the image.
            - Here are a few examples of accepted formats:
        """
        
        st.image("hubner2020.png")
        st.image("img1.PNG")
        st.image("img2.PNG")
        """
        2. Channel heights and widths
            - If a paper contains multiple different channel heights and widths, please create separate entries for each instance.
            - Please indicate channel heights and widths in μm
        3. Keywords
            - Usually keywords are indicated near the abstract of a paper. You can make use of those or any other key concepts explored in the paper as determined by your own judgement.
        4. Missing info
            - It is mandatory to indicate a DOI, use case and image for each paper. If information for other columns is missing, it may be omitted.
        """

if __name__ == '__main__':
    main()
