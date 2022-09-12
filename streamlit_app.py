import streamlit as st
import pandas as pd
import numpy as np
from funcs import Connect_To_PACS
import pydicom
from pynetdicom import AE, sop_class
from pydicom import uid


class App(Connect_To_PACS):

    def __init__(self):

        st.title('Retrieving DICOM images from PACS')
        st.markdown(' Use the menu at the left to select the settings for data retrieval ')

        Connect_To_PACS.__init__(self, port=104, ae_title='AET')


    def getQueryRetrieveLevel(self):

        st.sidebar.markdown('## Parameters')
        cols = st.sidebar.columns(2)
        self.queryRetrieveLevel = cols[0].radio(label='Select the Query Retrieval Level', options=['STUDY' ,'PATIENT'], horizontal=True , )
        self.queryRetrieveLevel2 = cols[1].radio(label='', options=['SERIES', 'IMAGE'], horizontal=True , disabled=True)


    # QueryRetrieveLevel
    def getRequestedContext(self):

        assert self.queryRetrieveLevel, 'queryRetrieveLevel() must be ran before calling getRequestedContext()'

        if self.queryRetrieveLevel == 'STUDY':
            reqContext = 'StudyRoot' + 'QueryRetrieveInformationModel'

        elif self.queryRetrieveLevel == 'PATIENT':
            output = st.sidebar.radio('PatientRoot or PatientStudy', ['Root', 'StudyOnly'], horizontal=True)
            reqContext = 'Patient' + output + 'QueryRetrieveInformationModel'
        else:
            st.write('These options are not currently available')


        st.sidebar.markdown('## Action')
        if self.queryRetrieveLevel in ['STUDY', 'PATIENT']:

            self.reqContextAction = st.sidebar.radio('Select the Requested Context', ['Find', 'Get', 'Move'], horizontal=True)
            reqContext = reqContext + self.reqContextAction

            self.requestedContext = eval( f'sop_class.{reqContext}' )

            st.sidebar.success(f'SOP Class: \n - {reqContext}  \n - {self.requestedContext}')


    def do_c_find(self):

        self.send_c_find(show_results=False, queryRetrieveLevel=sidebar.queryRetrieveLevel, requestedContext=sidebar.requestedContext)
        st.markdown( f'Number of retrieved subjects: {len(self.list_sample_info)}' )

        cols = st.columns(2)
        index = cols[0].slider("Select the subject index to display it's status", min_value=0, max_value=len(self.list_sample_info)-1, value=0, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None)

        cols[1].markdown(self.list_sample_info[index][0])



sidebar = App()
sidebar.getQueryRetrieveLevel()
sidebar.getRequestedContext()
sidebar.do_c_find()




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
