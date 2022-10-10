import pydicom
from pynetdicom import AE, sop_class
from pydicom import uid
import subprocess


def convert_log_to_csv(log_dir: str):
    # Reading the log file
    with open(log_dir, 'r') as file:
        log_file = file.read().splitlines()

    # Getting the indices for each downloaded file
    last_line_index = [i for i, s in enumerate(log_file) if 'Releasing Association' in s]
    index = [i for i, s in enumerate(log_file[:last_line_index[-1]]) if 'Storing DICOM file:' in s]

    # Organizing the log file into columns
    df = pd.DataFrame()
    for ix in tqdm(index):
        dct = {'case_name': log_file[ix].split('Storing DICOM file: ')[1]}

        if 'W: DICOM file already exists, overwriting' in log_file[ix + 1]:
            ix += 1

        dct['SCP_Response'] = log_file[ix + 1].split('SCP Response:')[1]

        for name in ['Remaining', 'Completed', 'Failed']:
            dct[name] = log_file[ix + 2].split(f'{name}:')[1].split(',')[0]

        df_temp = pd.DataFrame.from_dict(dct, orient='index').T
        df = pd.concat((df, df_temp))

    df.reset_index(drop=True, inplace=True)

    # Saving the log file
    df.to_csv(log_dir.replace('.log', '.csv'), index=False)

    return df