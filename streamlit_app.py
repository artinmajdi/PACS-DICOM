import streamlit as st
import pandas as pd
import numpy as np
import funcs
import pydicom
from pynetdicom import AE, sop_class
from pydicom import uid


class SideBar():

    def __init__(self):
        st.sidebar.markdown('## Select the Requested Context')

    def getQueryRetrieveLevel(self):
        self.queryRetrieveLevel = st.sidebar.radio('Select the Query Retrieval Level', ['STUDY' ,'PATIENT','SERIES', 'IMAGE'])

    # QueryRetrieveLevel
    def getRequestedContext(self):
        assert self.queryRetrieveLevel, 'queryRetrieveLevel() must be ran before calling getRequestedContext()'

        if self.queryRetrieveLevel == 'STUDY':
            reqContext = 'StudyRoot' + 'QueryRetrieveInformationModel'

        elif self.queryRetrieveLevel == 'PATIENT':
            output = st.sidebar.radio('PatientRoot or PatientStudy', ['Root', 'StudyOnly'])
            reqContext = 'Patient' + output + 'QueryRetrieveInformationModel'

        output = st.sidebar.radio('Select the Requested Context', ['Find', 'Get', 'Move'])
        requestedContext = reqContext + output

        st.sidebar.markdown(f'SOP Class = {requestedContext}')



st.title('Retrieving DICOM images from PACS')
st.markdown(' Use the menu at the left to select the settings for data retrieval ')

sidebar = SideBar()
sidebar.getQueryRetrieveLevel()
sidebar.getRequestedContext()

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
