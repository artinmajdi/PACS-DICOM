import pandas as pd
import time
import os
import streamlit as st
from utils.funcs import convert_log_to_csv, ConnectToPACS


# @st.cache
class StreamlitApp(ConnectToPACS):

    def __init__(self):

        self.startButton = None
        self.output_dir = None
        self.user_inputs = None
        self.df_user_csv = None

        st.title('Retrieving DICOM Images from PACS')
        self.reqContextAction = 'Get'

        self._get_port_aetitle()
        ConnectToPACS.__init__(self, addr=self.addr, port=self.port, ae_title=self.ae_title)

    def _get_patient_level_info(self):
        """
        The function creates 3 columns and then populates them with a dropdown menu, a radio button, and
        another radio button
        """

        # Creating 3 columns
        cols = st.columns([1, 1, 1])

        # PATIENT level
        self.queryRetrieveLevel = cols[0].selectbox('Select the Query Retrieval Level',
                                                    ['STUDY', 'PATIENT', 'SERIES', 'IMAGE'], index=1)

        # Unique key for PATIENT level
        if self.queryRetrieveLevel == 'STUDY':
            self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name',
                                                    ['AccessionNumber/StudyInstanceUID', 'Other'])

        elif self.queryRetrieveLevel == 'PATIENT':
            self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name',
                                                    ['PatientID', 'PatientName', 'Other'])

        elif self.queryRetrieveLevel == 'SERIES':
            self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name',
                                                    ['SeriesInstanceUID', 'Other'])

        elif self.queryRetrieveLevel == 'IMAGE':
            self.subject_ID_element = cols[1].radio('Subject Identifier Element  ID/Name', ['SOPInstanceUID', 'Other'])

        # Element ID/Name
        if self.subject_ID_element == 'Other':
            cols[1].text_input('Enter the Element ID/Name', value='(0008,0050)', type='default')

        # Find/Get
        self.reqContextAction = cols[2].radio('Select the Requested Context', ['Find', 'Get', ], index=1)

    def load_csv_file(self):
        """
        > This function creates a column in the streamlit app and allows the user to upload a CSV file
        :return: the columns that were created.
        """

        # Create 2 columns
        cols = st.columns([1, 1])

        # Get a CSV containing all the subjects' identifier information
        file = cols[0].file_uploader('CSV file containing subjects identifier information ', type='csv')

        # Loading the CSV file
        if file is not None:
            self.df_user_csv = pd.read_csv(file)
            st.write(self.df_user_csv)

        return cols

    def extract_subject_path(self):
        """
        This function takes the first column of the user input csv file and creates a dictionary with
        the subject ID as the key and the path to the subject's output directory as the value

        :return: A dictionary with the subject ID as the key and the path to the subject's directory as
        the value.
        """
        return {
            subject_ID_value: f'{self.output_dir}/{subject_ID_value}'
            for subject_ID_value in self.df_user_csv[self.df_user_csv.columns[0]]
        }

    def _get_download_info(self, cols=None):
        """
        The function takes the time lag between each download and the output directory to save the downloaded files.
        """
        if self.reqContextAction == 'Get' and cols is not None:
            self.timelag = cols[1].number_input('Timelag between each download in seconds', min_value=0, max_value=200,
                                                value=30, step=1)
            self.output_dir = os.path.abspath(cols[1].text_input('Output Directory',
                                                                 value='/Users/personal-macbook/Documents/projects/D7.PACS/code/data',
                                                                 type='default'))

    def get_query_retrieve_level(self):
        """
        > This function displays a collapsible section that contains a table of patient level
        information and a table of download information
        """

        with st.expander('Query/Retrieve Level', expanded=False):
            self._get_patient_level_info()

            cols = self.load_csv_file()

            self._get_download_info(cols=cols)

    def start_download(self):
        """
        The function takes in the user inputs and downloads the data for each subject
        """
        self.startButton = st.button('Start Download')

        if self.startButton:

            user_inputs = self.extract_subject_path()

            for idx, (subject_ID_value, output_directory) in enumerate(user_inputs.items()):
                st.markdown(
                    f'**Download Progress:** {idx + 1}/{len(user_inputs)}     **{self.subject_ID_element}** = {subject_ID_value}')

                if os.path.exists(output_directory):
                    st.write(f'{subject_ID_value} already downloaded')
                    continue

                # output_directory = self.output_dir + '/' + subject_ID_value
                self.getscu(output_directory=output_directory, QueryRetrieveLevel=self.queryRetrieveLevel,
                            subject_ID_element=self.subject_ID_element, subject_ID_value=subject_ID_value)

                # User specified timelag between each subject
                time.sleep(self.timelag)

            # Convert the log file to csv files
            self.update_log()

    def update_log(self):
        """
        The function takes in a log file and converts it into a pandas dataframe
        """

        # btn_update_log = st.sidebar.button('Update Log')

        # # Activates everytime the Update Log button is pressed
        # if btn_update_log:
        user_inputs = self.extract_subject_path()

        for (subject_ID_value, output_directory) in user_inputs.items():

            log_dir = f'{output_directory}/{subject_ID_value}.log'
            st.sidebar.write(subject_ID_value)

            if os.path.isfile(log_dir):
                df = convert_log_to_csv(log_dir=log_dir)
                st.sidebar.write(df)

            else:
                st.sidebar.write('Log not found')

    def do_c_find(self):
        """
        > The function `do_c_find` is called when the user clicks on the `Find` button. It sends a
        C-FIND request to the server and displays the number of retrieved subjects. It also displays the
        status of the subject at the index selected by the user
        """

        self.send_c_find(show_results=False, )

        st.info(f'Number of retrieved subjects: {len(self.list_sample_info)}')

        cols = st.columns([2, 2, 1])
        index = cols[0].slider("Select the subject index to display it's status", min_value=0,
                               max_value=len(self.list_sample_info) - 1, value=0, step=1, format=None, key=None,
                               help=None, on_change=None, args=None, kwargs=None)
        cols[1].info(self.list_sample_info[index][0])

    def _get_port_aetitle(self):
        """
        > The function takes in the port number, AE title, and PACS address, and verifies that the PACS
        server is running
        """

        with st.expander('PACS Settings', expanded=False):
            cols = st.columns([1, 1, 3])
            self.port = int(cols[0].number_input('Enter the port number', value=11112))
            self.ae_title = cols[1].text_input('Enter the AE Title', value='AET', type='default')
            self.addr = cols[2].text_input('Enter the PACS address', value='www.dicomserver.co.uk', type='default')

            self.verify()


if __name__ == '__main__':
    streamlit_app = StreamlitApp()
    streamlit_app.get_query_retrieve_level()
    streamlit_app.start_download()
