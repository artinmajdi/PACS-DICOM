import streamlit as st
import pandas as pd
# from funcs import Connect_To_PACS
from pynetdicom import AE, sop_class
import time
from tqdm import tqdm
import pydicom
from pynetdicom import AE, sop_class
import subprocess

class Connect_To_PACS():

    def __init__(self, addr="www.dicomserver.co.uk" , port=104, ae_title="AET"):

        self.addr = addr
        self.port = port # 104 # 11112
        self.ae_title = ae_title

    def dataset(self, queryRetrieveLevel='STUDY', subject_ID={ 'PatientID':None, 'StudyInstanceUID':None, 'SeriesInstanceUID':None}):

        assert queryRetrieveLevel in ['PATIENT', 'STUDY', 'SERIES', 'IMAGE'], "queryRetrieveLevel must be one of 'PATIENT', 'STUDY', 'SERIES', 'IMAGE'"

        self.ds = pydicom.dataset.Dataset()
        self.ds.QueryRetrieveLevel = queryRetrieveLevel

        # Unique key for PATIENT level
        if queryRetrieveLevel == 'PATIENT':
            self.ds.PatientID = subject_ID['PatientID']

        # Unique key for STUDY level
        elif queryRetrieveLevel == 'STUDY':
            self.ds.StudyInstanceUID = subject_ID['StudyInstanceUID']

        # Unique key for SERIES level
        elif queryRetrieveLevel == 'SERIES':
            self.ds.SeriesInstanceUID = subject_ID['SeriesInstanceUID']

    def associate(self, requestedContext=sop_class.PatientRootQueryRetrieveInformationModelFind):

        self.requestedContext = requestedContext
        # Associate with a peer AE at IP
        self.ae = AE(ae_title=self.ae_title)

        # if self.requestedContext is None:
        #     self.requestedContext = sop_class.RawDataStorage

        self.ae.add_requested_context(self.requestedContext)

        self.assoc = self.ae.associate(addr=self.addr, port=self.port)

    def send_c_find(self, show_results=False, release=True,):

        # Send the C-FIND request
        assert self.assoc.is_established, "Association must be established before calling _show_results()"
        self.responses = self.assoc.send_c_find(dataset=self.ds, query_model=self.requestedContext)
        self.list_sample_info = list(self.responses)

        if show_results: self._show_results(release=release)

    def send_c_get(self, priority=0):

        queryRetrieveLevel = 'PATIENT'
        subject_ID={ 'PatientID':'PAT009', 'StudyInstanceUID':None, 'SeriesInstanceUID':None}
        self.dataset(queryRetrieveLevel=queryRetrieveLevel, subject_ID=subject_ID)
        self.associate(requestedContext=sop_class.PatientStudyOnlyQueryRetrieveInformationModelGet)

        # Send the C-GET request
        assert self.assoc.is_established, "Association must be established before calling _show_results()"
        self.responses = self.assoc.send_c_get(dataset=self.ds, query_model=self.requestedContext, priority=priority)


    def getscu(self, output_directory='', QueryRetrieveLevel='PATIENT', subject_ID_element='PATIENTID', subject_ID_value='PAT009',):

        assert QueryRetrieveLevel in ['PATIENT', 'STUDY', 'SERIES', 'IMAGE'], "QueryRetrieveLevel must be one of 'PATIENT', 'STUDY', 'SERIES', 'IMAGE'"

        command = f'python -m pynetdicom getscu --output-directory {output_directory} {self.addr} {self.port} -k QueryRetrieveLevel={QueryRetrieveLevel} -k {subject_ID_element}={subject_ID_value}'
        print(command)
        p = subprocess.Popen('exec ' + command, stdout=subprocess.PIPE, shell=True)

        return p

    def _show_results(self, release=False):

        for (status, identifier) in self.list_sample_info:

            if status: print('C-FIND query status: 0x{0:04X}'.format(status.Status))
            else:      print('Connection timed out, was aborted or received invalid response')


        if release:  self.release()

    def release(self):
        ''' Release the association '''
        self.assoc.release()


class App(Connect_To_PACS):

    def __init__(self):

        st.title('Retrieving DICOM Images from PACS')
        self.reqContextAction = 'Get'

        self._getPortAEtitle()
        Connect_To_PACS.__init__(self, addr=self.addr, port=self.port, ae_title=self.ae_title)

    def _get_patient_level_info(self):

        # Creating 3 columns
        cols = st.columns([1,1,1])

        # PATIENT level
        self.queryRetrieveLevel  = cols[0].selectbox('Select the Query Retrieval Level', ['STUDY' ,'PATIENT', 'SERIES', 'IMAGE'])

        # Unique key for PATIENT level
        if self.queryRetrieveLevel == 'STUDY':         self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name', ['AccessionNumber/StudyInstanceUID' , 'Other'])
        elif self.queryRetrieveLevel == 'PATIENT':   self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name', ['PatientID', 'PatientName', 'Other'])
        elif self.queryRetrieveLevel == 'SERIES':     self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name', ['SeriesInstanceUID', 'Other'])
        elif self.queryRetrieveLevel == 'IMAGE':      self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name', ['SOPInstanceUID', 'Other'])

        # Element ID/Name
        if self.subject_ID_element == 'Other':    cols[1].text_input('Enter the Element ID/Name', value='(0008,0050)' , type='default')

        # Find/Get
        self.reqContextAction  = cols[2].radio('Select the Requested Context', ['Find', 'Get' ,])

    def _get_CSV_File(self):
        # Create 2 columns
        cols= st.columns([1,1])

        # Get a CSV containing all the subjects identifier information
        file = cols[0].file_uploader('CSV file containing subjects identifier information ',  type='csv')

        # Loading the CSV file
        if file is not None:
            self.df = pd.read_csv(file)
            st.write(self.df)

        return cols

    def  _get_download_info(self, cols=None):
        if self.reqContextAction == 'Get' and cols is not None:
            self.timelag = cols[1].number_input('Timelag between each download in seconds', min_value=0, max_value=100, value=60, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None,)
            self.output_dir = cols[1].text_input('Output Directory' ,   value='/Users/personal-macbook/Documents/projects/D7.PACS/code/Data7.PACS_DICOM')

    def getQueryRetrieveLevel(self):

        with st.expander('Query/Retrieve Level', expanded=False):

            self._get_patient_level_info()

            cols = self._get_CSV_File()

            self._get_download_info(cols=cols)

    def start_download(self):
        self.startButton =  st.button('Start Download',)

        if self.startButton:

            for idx, value in enumerate(self.df.values):

                st.markdown( f'**Download Progress:** {idx+1}/{self.df.shape[0]}     **{self.subject_ID_element}** = {value[0]}' )
                p = Connect_To_PACS.getscu(self, output_directory=self.output_dir, QueryRetrieveLevel=self.queryRetrieveLevel , subject_ID_element=self.subject_ID_element, subject_ID_value=value[0])
                time.sleep(self.timelag)


    def do_c_find(self):

        self.send_c_find(show_results=False,)

        st.info( f'Number of retrieved subjects: {len(self.list_sample_info)}' )

        cols = st.columns([2,2,1])
        index = cols[0].slider("Select the subject index to display it's status", min_value=0, max_value=len(self.list_sample_info)-1, value=0, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None)
        cols[1].info(self.list_sample_info[index][0])

    def _getPortAEtitle(self):

        with st.expander('PACS Settings', expanded=False):
            cols = st.columns([1,1, 3])
            self.port      =  int(cols[0].number_input('Enter the port number', value=11112))
            self.ae_title =  cols[1].text_input('Enter the AE Title', value='AET', type='default')
            self.addr      =  cols[2].text_input('Enter the PACS address', value='www.dicomserver.co.uk', type='default')

sidebar = App()
sidebar.getQueryRetrieveLevel()
sidebar.start_download()



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
