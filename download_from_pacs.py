import dotenv
import argparse
import pandas as pd
import os
from collections import namedtuple
import time
from tqdm import tqdm
from utils.funcs import convert_log_to_csv, ConnectToPACS

parser = argparse.ArgumentParser(description='DICOM Server')
parser.add_argument('--output_dir', type=str, default='../data', help='Path to save the downloaded files')
parser.add_argument('--csv_dir', type=str, default='other/test.csv', help='Path to csv file of cases')
parser.add_argument('--env', type=str, default='config.env', help='Path to .env file')
args = parser.parse_args()


class DownloadFromPACS(ConnectToPACS):

    def __init__(self):
        # Extract .env file's variables
        self.port = None
        self.timelag = None
        self.reqContextAction = None
        self.subject_ID_element = None
        self.queryRetrieveLevel = None
        self.ae_title = None
        self.addr = None
        self.config = None
        self.get_env_variables()
        ConnectToPACS.__init__(self, addr=self.addr, port=self.port, ae_title=self.ae_title)

        # Extract CLI variables
        self.output_dir = os.path.abspath(args.output_dir)
        self.csv_dir = os.path.abspath(args.csv_dir)
        self.df_user_csv = DownloadFromPACS.load_csv_file(self.csv_dir)
        self.user_inputs = DownloadFromPACS.extract_subject_path(df=self.df_user_csv, output_dir=self.output_dir)

    def get_env_variables(self):

        config = dotenv.dotenv_values(args.env)

        self.config = namedtuple('Config', config.keys())(*config.values())
        self.addr = self.config.Server
        self.port = int(self.config.Port)
        self.ae_title = self.config.AE_TITLE
        self.queryRetrieveLevel = self.config.QueryRetrieveLevel
        self.subject_ID_element = self.config.Subject_Identifier
        self.reqContextAction = self.config.reqContextAction
        self.timelag = int(self.config.timelag)

        self.verify()

    def start_download(self):

        for (subject_ID_value, output_directory) in tqdm(self.user_inputs.items()):

            if os.path.exists(output_directory):
                print(f'{subject_ID_value} already downloaded')
                continue

            p = self.getscu(output_directory=output_directory, QueryRetrieveLevel=self.queryRetrieveLevel,
                            subject_ID_element=self.subject_ID_element, subject_ID_value=subject_ID_value)

            # User specified timelag between each subject
            time.sleep(self.timelag)

    def update_log(self):

        for (subject_ID_value, output_directory) in self.user_inputs.items():

            log_dir = f'{output_directory}/{subject_ID_value}.log'

            if os.path.isfile(log_dir):
                convert_log_to_csv(log_dir=log_dir)

    @staticmethod
    def load_csv_file(csv_dir):
        assert os.path.isfile(csv_dir)
        return pd.read_csv(csv_dir)

    @staticmethod
    def extract_subject_path(df, output_dir):
        return {
            subject_ID_value: f'{output_dir}/{subject_ID_value}'
            for subject_ID_value in df[df.columns[0]]
        }


if __name__ == '__main__':
    streamlit_app = DownloadFromPACS()
    streamlit_app.start_download()
    streamlit_app.update_log()
