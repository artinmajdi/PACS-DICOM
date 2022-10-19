# Connecting to a PACS server and downloading DICOM files

[![GitHub.io](https://img.shields.io/badge/GitHub.io-artinmajdi)](https://artinmajdi.github.io/Data7.PACS_DICOM/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://artinmajdi-data7-pacs-dicom-app-id280r.streamlitapp.com/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/artinmajdi/Data7.PACS_DICOM.git/main?labpath=other%2Fd7.pacs.ipynb)
[![DockerHub](https://img.shields.io/badge/DockerHub-artinmajdi%2Fconnect--to--pacs-blue)](https://hub.docker.com/r/artinmajdi/connect_to_pacs)

## <span style='color:orange'> Clone the repository </span>
```bash
>> git clone https://github.com/artinmajdi/Data7.PACS_DICOM.git
```

## <span style='color:orange'> Local environment set up</span>
```bash
>> pip install -r requirements.txt
```
### <span style='color:green'> Running through CLI </span>
```bash
>> python download_from_pacs.py --output_dir [path-to-downloaded-files] --csv_dir [path-to-csv-files-of-subjects-IDs] --env /code/config.env
```
### <span style='color:green'> Running through streamlit app </span>
```bash
>> streamlit run app.py
```

## <span style='color:orange'> Setting up Docker</span>

### <span style='color:green'> Step 1: Building the docker container </span>

#####  I. Building the image using Dockerfile
```bash
>> docker build . -t artinmajdi/connect_to_pacs
```
##### II. Pulling from docker hub
```bash
>> docker pull artinmajdi/connect_to_pacs
```
### <span style='color:green'> Step 2: Run the container </span>

```bash
>> docker run --rm -i -v [path-to-repo]:/code -v [path-to-save-files]:/data artinmajdi/connect_to_pacs:latest python download_from_pacs.py --output_dir /data --csv_dir [path-to-csv-files-of-subjects-IDs] --env /code/config.env
```
##### Example:
```bash
>> docker run --rm -i -v [path-to-repo]:/code -v [path-to-save-files]:/data  artinmajdi/connect_to_pacs:latest python download_from_pacs.py --output_dir /data --csv_dir /code/other/test.csv --env /code/config.env
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
