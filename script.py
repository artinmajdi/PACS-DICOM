import dotenv
import argparse
import streamlit as st
import pandas as pd
from pynetdicom import AE, sop_class, debug_logger
import pydicom
import subprocess
import os

class Connect_To_PACS():

    def __init__(self, addr="www.dicomserver.co.uk" , port=104, ae_title="AET"):

        self.addr = addr
        self.port = port # 104 # 11112
        self.ae_title = ae_title

    def verify(self):

        ae = AE(ae_title=self.ae_title)

        ae.add_requested_context( sop_class.Verification )

        # Adding the Verification SOP Class to the list of SOP Classes that the AE will support.
        assoc = ae.associate(self.addr, self.port)

        if assoc.is_established:
            # Use the C-ECHO service to send the request
            status = assoc.send_c_echo()
            if status:
                # If the status is 'Success' then the verification succeeded
                st.write('Verification successful')
            else:
                st.write('Connection timed out, was aborted or received invalid response')

            # Release the association
            assoc.release()
        else:
            st.write('Association rejected, aborted or never connected')

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

        os.makedirs( output_directory , exist_ok=True )

        command = f'nohup python -m pynetdicom getscu --output-directory {output_directory} {self.addr} {self.port} -k QueryRetrieveLevel={QueryRetrieveLevel} -k {subject_ID_element}={subject_ID_value} | tee -a {output_directory}/{subject_ID_value}.log'
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

class Streamlit_App(Connect_To_PACS):

    def __init__(self):

        self.output_dir   = None
        self.user_inputs = None
        self.df_user_csv = None

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
            self.df_user_csv = pd.read_csv(file)
            st.write(self.df_user_csv)

        return cols

    def extract_subject_path( self ):
        user_inputs = {}
        for subject_ID_value in self.df_user_csv[ self.df_user_csv.columns[0] ]:
            user_inputs[subject_ID_value] = f'{self.output_dir}/{subject_ID_value}'

        return user_inputs

    def  _get_download_info(self, cols=None):
        if self.reqContextAction == 'Get' and cols is not None:
            self.timelag = cols[1].number_input('Timelag between each download in seconds', min_value=0, max_value=100, value=60, step=1, format=None, key=None, help=None, on_change=None, args=None, kwargs=None,)
            self.output_dir = os.path.abspath(  cols[1].text_input('Output Directory' ,   value='/Users/personal-macbook/Documents/projects/D7.PACS/code/downloaded_images', type='default' ,)  )

    def getQueryRetrieveLevel(self):

        with st.expander('Query/Retrieve Level', expanded=False):

            self._get_patient_level_info()

            cols = self._get_CSV_File()

            self._get_download_info(cols=cols)

    def start_download(self):
        self.startButton =  st.button('Start Download',)

        if self.startButton:

            user_inputs = self.extract_subject_path()

            for idx ,  (subject_ID_value , output_directory)  in enumerate( user_inputs.items() ):

                st.markdown( f'**Download Progress:** {idx+1}/{len(user_inputs)}     **{self.subject_ID_element}** = {subject_ID_value}' )

                # output_directory = self.output_dir + '/' + subject_ID_value
                p = self.getscu(output_directory=output_directory, QueryRetrieveLevel=self.queryRetrieveLevel , subject_ID_element=self.subject_ID_element, subject_ID_value=subject_ID_value)

                # User specified timelag between each subject
                time.sleep(self.timelag)

    def update_log(self):

        btnUpdateLog = st.sidebar.button('Update Log')

        # Activates everytime the Update Log button is pressed
        if btnUpdateLog :
            user_inputs = self.extract_subject_path()

            for (subject_ID_value , output_directory)  in user_inputs.items():

                log_dir=f'{output_directory}/{subject_ID_value}.log'
                st.sidebar.write(subject_ID_value)

                if os.path.isfile(log_dir):
                    df = Streamlit_App.convert_log_to_csv( log_dir=log_dir)
                    st.sidebar.write(df)

                else:
                    st.sidebar.write('Log not found')

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

            self.verify()

    @staticmethod
    def convert_log_to_csv( log_dir: str):

        # Reading the log file
        with open(log_dir , 'r') as file:
            log_file = file.read().splitlines()

        # Getting the indices for each downloaded file
        last_line_index = [i for i, s in enumerate(log_file) if 'Releasing Association' in s]
        index = [i for i, s in enumerate(log_file[:last_line_index[-1]]) if 'Storing DICOM file:' in s]

        # Organizing the log file into columns
        df = pd.DataFrame()
        for ix in tqdm(index):
            dct = {}
            dct['case_name'] = log_file[ix].split('Storing DICOM file: ')[1]

            if 'W: DICOM file already exists, overwriting' in log_file[ix+1]:
                ix += 1

            dct['SCP_Response']  = log_file[ix+1].split('SCP Response:')[1]

            for name in [ 'Remaining' ,  'Completed' ,  'Failed' ]:
                dct[name] = log_file[ix+2].split(f'{name}:')[1].split(',')[0]

            df_temp = pd.DataFrame.from_dict(dct, orient='index').T
            df = pd.concat( (df , df_temp) )

        df.reset_index(drop=True, inplace=True)

        # Saving the log file
        df.to_csv(log_dir.replace('.log', '.csv') , index=False)

        return df


args = argparse.ArgumentParser(description='Process some integers.')
args.add_argument('--env', type=str, default='.env', help='Path to .env file')
args.add_argument('--output_dir', type=str, help='Path to save the downloaded files')
args.add_argument('--user_inputs', type=str, help='Path to a csv containing the subjects to download')


CONFIG = dotenv.dotenv_values()




if __name__ == '__main__':

    streamlit_app = Streamlit_App()
    streamlit_app.getQueryRetrieveLevel()
    streamlit_app.start_download()
    streamlit_app.update_log()