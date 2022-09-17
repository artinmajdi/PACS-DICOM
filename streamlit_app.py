from faulthandler import disable
from turtle import width, window_width
import streamlit as st
import pandas as pd
import numpy as np
from funcs import Connect_To_PACS
from pynetdicom import AE, sop_class
# from pydicom import uid


class App(Connect_To_PACS):

    def __init__(self):

        st.title('Retrieving DICOM Images from PACS')

        self._getPortAEtitle()
        Connect_To_PACS.__init__(self, addr=self.addr, port=self.port, ae_title=self.ae_title)

    def getQueryRetrieveLevel(self):

        with st.expander('Query/Retrieve Level', expanded=False):
            cols = st.columns([1,1,1])
            self.queryRetrieveLevel  = cols[0].selectbox('Select the Query Retrieval Level', ['STUDY' ,'PATIENT', 'SERIES', 'IMAGE'])

            if self.queryRetrieveLevel == 'STUDY':
                self.reqContext = 'StudyRoot' + 'QueryRetrieveInformationModel'

            elif self.queryRetrieveLevel == 'PATIENT':
                output = cols[1].radio('PatientRoot or PatientStudy', ['Root', 'StudyOnly'])
                self.reqContext = 'Patient' + output + 'QueryRetrieveInformationModel'


            if self.queryRetrieveLevel in [  'STUDY' , 'PATIENT']:

                self.reqContextAction   = cols[2].radio('Select the Requested Context', ['Find', 'Get' , 'Move'])
                self.reqContext = self.reqContext + self.reqContextAction
                self.requestedContext = eval( f'sop_class.{self.reqContext}' )

                cols = st.columns([1,3,1])
                cols[0].write( '#### <span style="color:green"> SOP Class:  </span>', unsafe_allow_html=True)
                cols[1].success(f'- {self.reqContext}  \n - {self.requestedContext}')

                if self.reqContextAction =='Find':
                    self.do_c_find()

            elif self.queryRetrieveLevel in [ 'SERIES', 'IMAGE']:
                st.warning('This option is not supported at this time')

    def do_c_find(self):

        self.send_c_find(show_results=False, queryRetrieveLevel=self.queryRetrieveLevel, requestedContext=self.requestedContext)

        st.info( f'Number of retrieved subjects: {len(self.list_sample_info)}' )

        cols = st.columns([2,2,1])
        index = cols[0].slider("Select the subject index to display it's status", min_value=0, max_value=len(self.list_sample_info)-1, value=0, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None)
        cols[1].info(self.list_sample_info[index][0])

    def get_download_info(self):

        with st.expander('Download Settings', expanded=False):
            cols = st.columns([1,3])
            self.searchType = cols[0].radio('Search type', ['AccessionNumber', 'PatientID'])

            file = cols[1].file_uploader('CSV file containing subjects identifier information ',  type='csv')

            cols = st.columns([1,2])
            self.timelag = cols[0].number_input('Timelag between each download in seconds', min_value=0, max_value=100, value=60, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None)
            self.output_dir = cols[1].text_input('Output Directory' ,   value='/Users/personal-macbook/Documents/projects/D7.PACS/code/Data7.PACS_DICOM')

            if file is not None:
                self.df = pd.read_csv(file)
                st.write(self.df)

        disabled = False if self.queryRetrieveLevel in [  'STUDY' , 'PATIENT'] else True
        self.startButton =  st.button('Start Download', disabled=disabled)

        if self.startButton:
            i,n = 1,100
            cols[1].write( f'Download Progress: {i}/{n}' )

    def _getPortAEtitle(self):

        with st.expander('PACS Settings', expanded=False):
            cols = st.columns([1,1, 3])
            self.port = int(cols[0].number_input('Enter the port number', value=104))
            self.ae_title = cols[1].text_input('Enter the AE Title', value='AET', type='default')
            self.addr = cols[2].text_input('Enter the PACS address', value='www.dicomserver.co.uk', type='default')

sidebar = App()
sidebar.getQueryRetrieveLevel()
sidebar.get_download_info()



# # Accession or PatientID
# selected_identifier = st.sidebar.selectbox('Select your method of study identification', ['Accession number' , 'Patient ID'])

# # Data retrieval or checking a study
# selected_what_to_do = st.sidebar.selectbox('What do you want to do?', ['Retrieve in bulk', 'Check the existing files in a Study'])

# if selected_what_to_do == 'Check the existing files in a Study':

#     identifier = st.sidebar.text_input( f'Enter the {selected_identifier}', value='')

# elif selected_what_to_do == 'Retrieve in bulk':

#     connect_To_PACS = funcs.Connect_To_PACS()
#     connect_To_PACS.send_c_find(show_results=False, queryRetrieveLevel=queryRetrieveLevel, requestedContext=sop_class.PatientRootQueryRetrieveInformationModelFind)


# # uploaded_file = st.file_uploader("Choose a CSV file containing the list of accession numbers", type="csv")
