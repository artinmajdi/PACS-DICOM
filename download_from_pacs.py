import dotenv
import argparse
import pandas as pd
from pynetdicom import AE, sop_class, debug_logger
import pydicom
import subprocess
import os
from collections import namedtuple
import time
from tqdm import tqdm

parser = argparse.ArgumentParser(description='DICOM Server')
parser.add_argument('--output_dir', type=str, default='data', help='Path to save the downloaded files')
parser.add_argument('--csv_dir', type=str, default='test.csv', help='Path to csv file of cases')
parser.add_argument('--env', type=str, default='.env', help='Path to .env file')
args = parser.parse_args()

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
                print('Verification successful')
            else:
                print('Connection timed out, was aborted or received invalid response')

            # Release the association
            assoc.release()
        else:
            print('Association rejected, aborted or never connected')

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

        command = f'nohup python -m pynetdicom getscu --output-directory {output_directory} {self.addr} {self.port} -k QueryRetrieveLevel={QueryRetrieveLevel} -k {subject_ID_element}={subject_ID_value} | tee -a {output_directory}/{subject_ID_value}.log &'
        print(command)

        p = subprocess.Popen('exec ' + command, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()

        p.wait()

    def _show_results(self, release=False):

        for (status, identifier) in self.list_sample_info:

            if status: print('C-FIND query status: 0x{0:04X}'.format(status.Status))
            else:      print('Connection timed out, was aborted or received invalid response')


        if release:  self.release()

    def release(self):
        ''' Release the association '''
        self.assoc.release()

class Download_From_PACS(Connect_To_PACS):

    def __init__(self):
        # Extract .env file's variables
        self.get_env_variables()
        Connect_To_PACS.__init__(self, addr=self.addr, port=self.port, ae_title=self.ae_title)

        # Extract CLI variables
        self.output_dir = os.path.abspath( args.output_dir )
        self.csv_dir       = os.path.abspath(  args.csv_dir )
        self.df_user_csv = Download_From_PACS.load_csv_file(self.csv_dir)
        self.user_inputs = Download_From_PACS.extract_subject_path( df=self.df_user_csv ,  output_dir=self.output_dir )

    def get_env_variables(self):

        config = dotenv.dotenv_values(args.env)
        self.config = namedtuple('Config', config.keys())(*config.values())

        self.addr      = self.config.Server
        self.port      = int(self.config.Port)
        self.ae_title = self.config.AE_TITLE
        self.queryRetrieveLevel  = self.config.QueryRetrieveLevel
        self.subject_ID_element = self.config.Subject_Identifier
        self.reqContextAction     = self.config.reqContextAction
        self.timelag = int(self.config.timelag)

        self.verify()

    def start_download(self):

        for (subject_ID_value , output_directory)  in tqdm( self.user_inputs.items() ):

            if os.path.exists(output_directory):
                print(f'{subject_ID_value} already downloaded')
                continue

            p = self.getscu(output_directory=output_directory, QueryRetrieveLevel=self.queryRetrieveLevel , subject_ID_element=self.subject_ID_element, subject_ID_value=subject_ID_value)

            # User specified timelag between each subject
            time.sleep(self.timelag)

    def update_log(self):

        for (subject_ID_value , output_directory)  in self.user_inputs.items():

            log_dir=f'{output_directory}/{subject_ID_value}.log'

            if os.path.isfile(log_dir):
                df = Download_From_PACS.convert_log_to_csv( log_dir=log_dir)
                df.to_csv( log_dir.replace('log' , 'csv') , index=False )

    @staticmethod
    def load_csv_file(csv_dir):
        assert os.path.isfile(csv_dir)
        return pd.read_csv(csv_dir)

    @staticmethod
    def extract_subject_path( df , output_dir ):
        user_inputs = {}
        for subject_ID_value in df[ df.columns[0] ]:
            user_inputs[subject_ID_value] = f'{output_dir}/{subject_ID_value}'

        return user_inputs

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
        for ix in index:
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


if __name__ == '__main__':
    streamlit_app = Download_From_PACS()
    streamlit_app.start_download()
    streamlit_app.update_log()