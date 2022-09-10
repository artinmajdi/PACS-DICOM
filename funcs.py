import pydicom
from pynetdicom import AE, sop_class
from pydicom import uid



class Connect_To_PACS():

    def __init__(self, addr="www.dicomserver.co.uk" , port=104, ae_title="AET"):

        self.addr = addr
        self.port = port # 104 # 11112
        self.ae_title = ae_title


    def _dataset(self, queryRetrieveLevel='STUDY'):

        assert queryRetrieveLevel in ['STUDY' 'PATIENT', 'STUDY', 'SERIES', 'IMAGE'], "queryRetrieveLevel must be one of 'PATIENT', 'STUDY', 'SERIES', 'IMAGE'"

        self.ds = pydicom.dataset.Dataset()
        self.ds.QueryRetrieveLevel = queryRetrieveLevel


    def _associate(self, requestedContext=sop_class.PatientRootQueryRetrieveInformationModelFind):

        self.requestedContext = requestedContext

        # Associate with a peer AE at IP
        self.ae = AE(ae_title=self.ae_title)

        self.ae.add_requested_context(self.requestedContext)

        self.assoc = self.ae.associate(addr=self.addr, port=self.port)


    def send_c_find(self, show_results=False):

        self._dataset(queryRetrieveLevel='STUDY')

        self._associate(requestedContext=sop_class.PatientRootQueryRetrieveInformationModelFind)


        # Send the C-FIND request
        assert self.assoc.is_established, "Association must be established before calling _show_results()"

        self.responses = self.assoc.send_c_find(dataset=self.ds, query_model=self.requestedContext)

        if show_results: self._show_results()


    def _show_results(self, release=False):

        for (status, identifier) in self.responses:

            if status: print('C-FIND query status: 0x{0:04X}'.format(status.Status))
            else:      print('Connection timed out, was aborted or received invalid response')


        if release:  self.release()


    def release(self):
        ''' Release the association '''
        self.assoc.release()