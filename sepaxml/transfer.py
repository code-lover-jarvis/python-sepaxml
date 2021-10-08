import datetime
import xml.etree.ElementTree as ET

from shared import SepaPaymentInitn
from utils import int_to_decimal_str


class SepaTransfer(SepaPaymentInitn):
    """
    This class creates a Sepa transfer XML File.
    """
    root_el_g = "GrpHdr"
    root_el_p = "PmtInf"
    root_el = "CstmrCdtTrfInitn"

    def __init__(self, config, schema="pain.001.001.03", clean=True):
        super().__init__(config, schema, clean)

    def check_config(self, config):
        """
        Check the config file for required fields and validity.
        @param config: The config dict.
        @return: True if valid, error string if invalid paramaters where
        encountered.
        """
        validation = ""
        required = ["name", "currency", "IBAN"]

        if 'execution_date' in config:
            if not isinstance(config['execution_date'], datetime.date):
                validation += "EXECUTION_DATE_INVALID_OR_NOT_DATETIME_INSTANCE"
            config['execution_date'] = config['execution_date'].isoformat()

        for config_item in required:
            if config_item not in config:
                validation += config_item.upper() + "_MISSING "

        if not validation:
            return True
        else:
            raise Exception("Config file did not validate. " + validation)

    def check_payment(self, payment):
        """
        Check the payment for required fields and validity.
        @param payment: The payment dict
        @return: True if valid, error string if invalid paramaters where
        encountered.
        """
        validation = ""
        required = ["name", "IBAN", "amount"]

        for config_item in required:
            if config_item not in payment:
                validation += config_item.upper() + "_MISSING "

        if (('description' not in payment) and ('document' not in payment)):
            validation += "DESCRIPTION_OR_DOCUMENT_REQUIRED"
        if (("description" in payment) and ("document" in payment)):
            validation += "DESCRIPTION_AND_DOCUMENT_DONT_CO-EXIST"

        if not isinstance(payment['amount'], int):
            validation += "AMOUNT_NOT_INTEGER "

        if 'document' in payment:
            for invoices in payment["document"]:
                if 'invoice_date' in invoices:
                    if not isinstance(invoices["invoice_date"], datetime.date):
                        validation += "INVOICE_DATE_INVALID_OR_NOT_DATETIME_INSTANCE"
                    invoices["invoice_date"] = invoices["invoice_date"].isoformat()

        if 'execution_date' in payment:
            if not isinstance(payment['execution_date'], datetime.date):
                validation += "EXECUTION_DATE_INVALID_OR_NOT_DATETIME_INSTANCE"
            payment['execution_date'] = payment['execution_date'].isoformat()

        if validation == "":
            return True
        else:
            raise Exception('Payment did not validate: ' + validation)

    def add_payment(self, payment):
        """
        Function to add payments
        @param payment: The payment dict
        @raise exception: when payment is invalid
        """
        # Validate the payment
        self.check_payment(payment)

        if self.clean:
            from text_unidecode import unidecode

            payment['name'] = unidecode(payment['name'])[:70]
            if ("description" in payment):
                payment['description'] = unidecode(payment['description'])[:140]

        if not self._config['batch']:
            # Start building the non batch payment
            PmtInf_nodes = self._create_PmtInf_node()
            PmtInf_nodes['PmtInfIdNode'].text = self._config['unique_id']
            PmtInf_nodes['PmtMtdNode'].text = "TRA"
            PmtInf_nodes['BtchBookgNode'].text = "false"
            PmtInf_nodes['NbOfTxsNode'].text = "1"
            PmtInf_nodes['CtrlSumNode'].text = int_to_decimal_str(
                payment['amount'])

            if not self._config.get('domestic', False):
                PmtInf_nodes['Cd_SvcLvl_Node'].text = "SEPA"
            if 'execution_date' in payment:
                PmtInf_nodes['ReqdExctnDtNode'].text = payment['execution_date']
            else:
                PmtInf_nodes['ReqdExctnDtNode'].text = self._config['execution_date']


            PmtInf_nodes['Nm_Dbtr_Node'].text = self._config['name']
            PmtInf_nodes['IBAN_DbtrAcct_Node'].text = self._config['IBAN']
            if 'BIC' in self._config:
                PmtInf_nodes['BIC_DbtrAgt_Node'].text = self._config['BIC']

            PmtInf_nodes['ChrgBrNode'].text = "SLEV"
            PmtInf_nodes['MmbId_Node'].text = self._config['bank_code']

        if 'BIC' in payment:
            TX_nodes = self._create_TX_node(payment, bic = True)
            TX_nodes['BIC_CdtrAgt_Node'].text = payment['BIC']
        else:
            TX_nodes = self._create_TX_node(payment, bic = False)

        TX_nodes['Nm_Cdtr_Node'].text = payment['name']
        TX_nodes['InstdAmtNode'].set("Ccy", self._config['currency'])
        TX_nodes['InstdAmtNode'].text = int_to_decimal_str(payment['amount'])
        TX_nodes['Cd_CtgyPurp'].text = "SUPP"
        TX_nodes['IBAN_CdtrAcct_Node'].text = payment['IBAN']
        TX_nodes['EndToEnd_PmtId_Node'].text = payment.get('endtoend_id', 'NOTPROVIDED')

        if ("description" in payment):
            TX_nodes['UstrdNode'].text = payment['description']
        if self._config['batch']:
            self._add_batch(TX_nodes, payment)
        else:
            TX_nodes['InstrId_Node'].text = "1"
            self._add_non_batch(TX_nodes,  PmtInf_nodes)

    def _create_header(self):
        """
        Function to create the GroupHeader (GrpHdr)
        """

        if (self._config['CBI'] == False):
            CstmrCdtTrfInitn_node = self._xml.find('CstmrCdtTrfInitn')
            GrpHdr_node = ET.Element("GrpHdr")
        # Create the header nodes.
        MsgId_node = ET.Element("MsgId")
        CreDtTm_node = ET.Element("CreDtTm")
        NbOfTxs_node = ET.Element("NbOfTxs")
        CtrlSum_node = ET.Element("CtrlSum")
        InitgPty_node = ET.Element("InitgPty")
        Nm_node = ET.Element("Nm")
        Id_Othr_node = ET.Element("Id")
        Id_InitgPty_node = ET.Element("Id")
        Issr_node = ET.Element("Issr")
        Othr_node = ET.Element("Othr")
        OrgId_node = ET.Element("OrgId")

        # Add data to some header nodes.
        MsgId_node.text = self._config['unique_id']
        CreDtTm_node.text = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        Nm_node.text = self._config['name']
        if (self._config['CBI']):
            Id_Othr_node.text = self._config['issuer_id']
            Issr_node.text = 'CBI'

        # Append the nodes
        InitgPty_node.append(Nm_node)
        if (self._config['CBI']):
            Othr_node.append(Id_Othr_node)
            Othr_node.append(Issr_node)
            OrgId_node.append(Othr_node)
            Id_InitgPty_node.append(OrgId_node)
            InitgPty_node.append(Id_InitgPty_node)
            GrpHdr_node = self._xml.find('GrpHdr')
        GrpHdr_node.append(MsgId_node)
        GrpHdr_node.append(CreDtTm_node)
        GrpHdr_node.append(NbOfTxs_node)
        GrpHdr_node.append(CtrlSum_node)
        GrpHdr_node.append(InitgPty_node)

        if (self._config['CBI'] == False):
            CstmrCdtTrfInitn_node.append(GrpHdr_node)

    def _create_PmtInf_node(self):
        """
        Method to create the blank payment information nodes as a dict.
        """
        ED = dict()  # ED is element dict
        if (self._config['CBI'] == False):
            ED['PmtInfNode'] = ET.Element("PmtInf")
        ED['PmtInfIdNode'] = ET.Element("PmtInfId")
        ED['PmtMtdNode'] = ET.Element("PmtMtd")
        ED['BtchBookgNode'] = ET.Element("BtchBookg")
        ED['NbOfTxsNode'] = ET.Element("NbOfTxs")
        ED['CtrlSumNode'] = ET.Element("CtrlSum")
        ED['PmtTpInfNode'] = ET.Element("PmtTpInf")
        if not self._config.get('domestic', False):
            ED['SvcLvlNode'] = ET.Element("SvcLvl")
            ED['Cd_SvcLvl_Node'] = ET.Element("Cd")
        ED['ReqdExctnDtNode'] = ET.Element("ReqdExctnDt")

        ED['DbtrNode'] = ET.Element("Dbtr")
        ED['Nm_Dbtr_Node'] = ET.Element("Nm")
        ED['DbtrAcctNode'] = ET.Element("DbtrAcct")
        ED['Id_DbtrAcct_Node'] = ET.Element("Id")
        ED['IBAN_DbtrAcct_Node'] = ET.Element("IBAN")
        ED['DbtrAgtNode'] = ET.Element("DbtrAgt")
        ED['FinInstnId_DbtrAgt_Node'] = ET.Element("FinInstnId")
        ED['ClrSysMmbId_Node'] = ET.Element("ClrSysMmbId")
        ED['MmbId_Node'] = ET.Element("MmbId")
        if 'BIC' in self._config:
            ED['BIC_DbtrAgt_Node'] = ET.Element("BIC")
        ED['ChrgBrNode'] = ET.Element("ChrgBr")
        return ED

    def _create_TX_node(self, payment, bic=True):
        """
        Method to create the blank transaction nodes as a dict. If bic is True,
        the BIC node will also be created.
        """
        ED = dict()
        ED['CdtTrfTxInfNode'] = ET.Element("CdtTrfTxInf")
        ED['PmtIdNode'] = ET.Element("PmtId")
        ED['PmtTpInfNode'] = ET.Element("PmtTpInf")
        ED['CtgyPurpNode'] = ET.Element("CtgyPurp")
        ED['Cd_CtgyPurp'] = ET.Element("Cd")
        ED['EndToEnd_PmtId_Node'] = ET.Element("EndToEndId")
        ED['InstrId_Node'] = ET.Element("InstrId")
        ED['AmtNode'] = ET.Element("Amt")
        ED['InstdAmtNode'] = ET.Element("InstdAmt")
        ED['CdtrNode'] = ET.Element("Cdtr")
        ED['Nm_Cdtr_Node'] = ET.Element("Nm")

        ED['CdtrAgtNode'] = ET.Element("CdtrAgt")
        ED['FinInstnId_CdtrAgt_Node'] = ET.Element("FinInstnId")
        if bic:
            ED['BIC_CdtrAgt_Node'] = ET.Element("BIC")
        ED['CdtrAcctNode'] = ET.Element("CdtrAcct")
        ED['Id_CdtrAcct_Node'] = ET.Element("Id")
        ED['IBAN_CdtrAcct_Node'] = ET.Element("IBAN")
        ED['RmtInfNode'] = ET.Element("RmtInf")
        if ("description" in payment):
            ED['UstrdNode'] = ET.Element("Ustrd")
        return ED

    def _add_non_batch(self, TX_nodes,  PmtInf_nodes):
        """
        Method to add a transaction as non batch, will fold the transaction
        together with the payment info node and append to the main xml.
        """

        if (self._config['CBI']):
            PmtInfnode = self._xml.find('PmtInf')
        else:
            PmtInfnode = PmtInf_nodes['PmtInfNode']
        PmtInfnode.append(PmtInf_nodes['PmtInfIdNode'])
        PmtInfnode.append(PmtInf_nodes['PmtMtdNode'])
        PmtInfnode.append(PmtInf_nodes['BtchBookgNode'])
        if (self._config['CBI'] == False):
            PmtInf_node.append(PmtInf_nodes['NbOfTxsNode'])
            PmtInf_node.append(PmtInf_nodes['CtrlSumNode'])

        if not self._config.get('domestic', False):
            PmtInf_nodes['SvcLvlNode'].append(PmtInf_nodes['Cd_SvcLvl_Node'])
            PmtInf_nodes['PmtTpInfNode'].append(PmtInf_nodes['SvcLvlNode'])
            PmtInfnode.append(PmtInf_nodes['PmtTpInfNode'])
        PmtInfnode.append(PmtInf_nodes['ReqdExctnDtNode'])

        PmtInf_nodes['DbtrNode'].append(PmtInf_nodes['Nm_Dbtr_Node'])
        PmtInfnode.append(PmtInf_nodes['DbtrNode'])

        PmtInf_nodes['Id_DbtrAcct_Node'].append(PmtInf_nodes['IBAN_DbtrAcct_Node'])
        PmtInf_nodes['DbtrAcctNode'].append(PmtInf_nodes['Id_DbtrAcct_Node'])
        PmtInfnode.append(PmtInf_nodes['DbtrAcctNode'])

        if 'BIC' in self._config:
            PmtInf_nodes['FinInstnId_DbtrAgt_Node'].append(PmtInf_nodes['BIC_DbtrAgt_Node'])
        if (self._config['CBI']):
            PmtInf_nodes['ClrSysMmbId_Node'].append(PmtInf_nodes['MmbId_Node'])
            PmtInf_nodes['FinInstnId_DbtrAgt_Node'].append(PmtInf_nodes['ClrSysMmbId_Node'])
        PmtInf_nodes['DbtrAgtNode'].append(PmtInf_nodes['FinInstnId_DbtrAgt_Node'])
        PmtInfnode.append(PmtInf_nodes['DbtrAgtNode'])

        PmtInfnode.append(PmtInf_nodes['ChrgBrNode'])

        if (self._config['CBI']):
            TX_nodes['PmtIdNode'].append(TX_nodes['InstrId_Node'])
        TX_nodes['PmtIdNode'].append(TX_nodes['EndToEnd_PmtId_Node'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['PmtIdNode'])
        if (self._config['CBI']):
            TX_nodes['CtgyPurpNode'].append(TX_nodes['Cd_CtgyPurp'])
            TX_nodes['PmtTpInfNode'].append(TX_nodes['CtgyPurpNode'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['PmtTpInfNode'])
        TX_nodes['AmtNode'].append(TX_nodes['InstdAmtNode'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['AmtNode'])

        if 'BIC_CdtrAgt_Node' in TX_nodes and TX_nodes['BIC_CdtrAgt_Node'].text is not None:
            TX_nodes['FinInstnId_CdtrAgt_Node'].append(
                TX_nodes['BIC_CdtrAgt_Node'])
            TX_nodes['CdtrAgtNode'].append(TX_nodes['FinInstnId_CdtrAgt_Node'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['CdtrAgtNode'])

        TX_nodes['CdtrNode'].append(TX_nodes['Nm_Cdtr_Node'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['CdtrNode'])

        TX_nodes['Id_CdtrAcct_Node'].append(TX_nodes['IBAN_CdtrAcct_Node'])
        TX_nodes['CdtrAcctNode'].append(TX_nodes['Id_CdtrAcct_Node'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['CdtrAcctNode'])

        if('UstrdNode' in TX_nodes):
            TX_nodes['RmtInfNode'].append(TX_nodes['UstrdNode'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['RmtInfNode'])
        else:
            for x in self.strd_data(payment):
                TX_nodes['RmtInfNode'].append(x['StrdNode'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['RmtInfNode'])
        PmtInfnode.append(TX_nodes['CdtTrfTxInfNode'])

        if (self._config['CBI'] == False):
            CstmrCdtTrfInitn_node = self._xml.find('CstmrCdtTrfInitn')
            CstmrCdtTrfInitn_node.append(PmtInfnode)

    def _add_batch(self, TX_nodes, payment):
        """
        Method to add a payment as a batch. The transaction details are already
        present. Will fold the nodes accordingly and the call the
        _add_to_batch_list function to store the batch.
        """
        if (self._config['CBI']):
            TX_nodes['PmtIdNode'].append(TX_nodes['InstrId_Node'])
        TX_nodes['PmtIdNode'].append(TX_nodes['EndToEnd_PmtId_Node'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['PmtIdNode'])
        if (self._config['CBI']):
            TX_nodes['CtgyPurpNode'].append(TX_nodes['Cd_CtgyPurp'])
            TX_nodes['PmtTpInfNode'].append(TX_nodes['CtgyPurpNode'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['PmtTpInfNode'])
        TX_nodes['AmtNode'].append(TX_nodes['InstdAmtNode'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['AmtNode'])

        if 'BIC_CdtrAgt_Node' in TX_nodes and TX_nodes['BIC_CdtrAgt_Node'].text is not None:
            TX_nodes['FinInstnId_CdtrAgt_Node'].append(
                TX_nodes['BIC_CdtrAgt_Node'])
            TX_nodes['CdtrAgtNode'].append(TX_nodes['FinInstnId_CdtrAgt_Node'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['CdtrAgtNode'])

        TX_nodes['CdtrNode'].append(TX_nodes['Nm_Cdtr_Node'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['CdtrNode'])

        TX_nodes['Id_CdtrAcct_Node'].append(TX_nodes['IBAN_CdtrAcct_Node'])
        TX_nodes['CdtrAcctNode'].append(TX_nodes['Id_CdtrAcct_Node'])
        TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['CdtrAcctNode'])

        if('UstrdNode' in TX_nodes):
            TX_nodes['RmtInfNode'].append(TX_nodes['UstrdNode'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['RmtInfNode'])
        else:
            for x in self.strd_data(payment):
                TX_nodes['RmtInfNode'].append(x['StrdNode'])
            TX_nodes['CdtTrfTxInfNode'].append(TX_nodes['RmtInfNode'])
        self._add_to_batch_list(TX_nodes, payment)

    def _add_to_batch_list(self, TX_nodes, payment):
        """
        Method to add a transaction to the batch list. The correct batch will
        be determined by the payment dict and the batch will be created if
        not existant. This will also add the payment amount to the respective
        batch total.
        """
        batch_key = payment.get('execution_date', self._config['execution_date'])
        if batch_key in self._batches.keys():
            self._batches[batch_key].append(TX_nodes['CdtTrfTxInfNode'])
        else:
            self._batches[batch_key] = []
            self._batches[batch_key].append(TX_nodes['CdtTrfTxInfNode'])

        if batch_key in self._batch_totals:
            self._batch_totals[batch_key] += payment['amount']
        else:
            self._batch_totals[batch_key] = payment['amount']

    def _finalize_batch(self):
        """
        Method to finalize the batch, this will iterate over the _batches dict
        and create a TX_nodes for each batch. The correct information (from
        the batch_key and batch_totals) will be inserted and the batch
        transaction nodes will be folded. Finally, the batches will be added to
        the main XML.
        """
        for batch_meta, batch_nodes in self._batches.items():
            PmtInf_nodes = self._create_PmtInf_node()
            PmtInf_nodes['PmtInfIdNode'].text = self._config['unique_id']
            PmtInf_nodes['PmtMtdNode'].text = "TRA"
            PmtInf_nodes['BtchBookgNode'].text = "true"
            if not self._config.get('domestic', False):
                PmtInf_nodes['Cd_SvcLvl_Node'].text = "SEPA"
            if batch_meta:
                PmtInf_nodes['ReqdExctnDtNode'].text = batch_meta

            PmtInf_nodes['NbOfTxsNode'].text = str(len(batch_nodes))
            PmtInf_nodes['CtrlSumNode'].text = int_to_decimal_str(self._batch_totals[batch_meta])

            PmtInf_nodes['Nm_Dbtr_Node'].text = self._config['name']
            PmtInf_nodes['IBAN_DbtrAcct_Node'].text = self._config['IBAN']
            if 'BIC' in self._config:
                PmtInf_nodes['BIC_DbtrAgt_Node'].text = self._config['BIC']

            PmtInf_nodes['ChrgBrNode'].text = "SLEV"
            PmtInf_nodes['MmbId_Node'].text = self._config['bank_code']

            if (self._config['CBI']):
                PmtInfnode = self._xml.find('PmtInf')
            else:
                PmtInfnode = PmtInf_nodes['PmtInfNode']
            PmtInfnode.append(PmtInf_nodes['PmtInfIdNode'])
            PmtInfnode.append(PmtInf_nodes['PmtMtdNode'])
            PmtInfnode.append(PmtInf_nodes['BtchBookgNode'])

            if (self._config['CBI'] == False):
                PmtInfnode.append(PmtInf_nodes['NbOfTxsNode'])
                PmtInfnode.append(PmtInf_nodes['CtrlSumNode'])

            if not self._config.get('domestic', False):
                PmtInf_nodes['SvcLvlNode'].append(PmtInf_nodes['Cd_SvcLvl_Node'])
                PmtInf_nodes['PmtTpInfNode'].append(PmtInf_nodes['SvcLvlNode'])
                PmtInfnode.append(PmtInf_nodes['PmtTpInfNode'])
            PmtInfnode.append(PmtInf_nodes['ReqdExctnDtNode'])

            PmtInf_nodes['DbtrNode'].append(PmtInf_nodes['Nm_Dbtr_Node'])
            PmtInfnode.append(PmtInf_nodes['DbtrNode'])

            PmtInf_nodes['Id_DbtrAcct_Node'].append(PmtInf_nodes['IBAN_DbtrAcct_Node'])
            PmtInf_nodes['DbtrAcctNode'].append(PmtInf_nodes['Id_DbtrAcct_Node'])
            PmtInfnode.append(PmtInf_nodes['DbtrAcctNode'])

            if 'BIC' in self._config:
                PmtInf_nodes['FinInstnId_DbtrAgt_Node'].append(PmtInf_nodes['BIC_DbtrAgt_Node'])
            if (self._config['CBI']):
                PmtInf_nodes['ClrSysMmbId_Node'].append(PmtInf_nodes['MmbId_Node'])
                PmtInf_nodes['FinInstnId_DbtrAgt_Node'].append(PmtInf_nodes['ClrSysMmbId_Node'])
            PmtInf_nodes['DbtrAgtNode'].append(PmtInf_nodes['FinInstnId_DbtrAgt_Node'])
            PmtInfnode.append(PmtInf_nodes['DbtrAgtNode'])

            PmtInfnode.append(PmtInf_nodes['ChrgBrNode'])

            for txnode in batch_nodes:
                PmtInfnode.append(txnode)

            if (self._config['CBI'] == False):
                CstmrCdtTrfInitn_node = self._xml.find('CstmrCdtTrfInitn')
                CstmrCdtTrfInitn_node.append(PmtInf_nodes['PmtInfNode'])


    def _create_strd_nodes(self):

        ED = dict()
        ED['Nb_Node'] = ET.Element('Nb')
        ED['Cd_Node'] = ET.Element('Cd')
        ED['CdtNoteAmt_Node'] = ET.Element('CdtNoteAmt')
        ED['RltdDt_Node'] = ET.Element('RltdDt')
        ED['StrdNode'] = ET.Element("Strd")
        ED['CdOrPrtryNode'] = ET.Element("CdOrPrtry")
        ED['TpNode'] = ET.Element("Tp")
        ED['RfrdDocInfNode'] = ET.Element("RfrdDocInf")
        ED['RfrdDocAmtNode'] = ET.Element("RfrdDocAmt")

        return ED

    def strd_data(self, payment):

        lst =  list()
        for batches in payment['document']:
            # adding data to TX_Nodes
            strd_node = self._create_strd_nodes()
            strd_node['Nb_Node'].text = batches["invoice_number"]
            strd_node['Cd_Node'].text = batches["type"]
            strd_node['CdtNoteAmt_Node'].set("Ccy", self._config["currency"])
            strd_node['CdtNoteAmt_Node'].text = batches["invoice_amount"]
            strd_node['RltdDt_Node'].text = batches["invoice_date"]

            #appending the strd node for each batches
            strd_node['CdOrPrtryNode'].append(strd_node['Cd_Node'])
            strd_node['TpNode'].append(strd_node['CdOrPrtryNode'])
            strd_node['RfrdDocInfNode'].append(strd_node['TpNode'])
            strd_node['RfrdDocInfNode'].append(strd_node['Nb_Node'])
            strd_node['RfrdDocInfNode'].append(strd_node['RltdDt_Node'])
            strd_node['StrdNode'].append(strd_node['RfrdDocInfNode'])
            strd_node['RfrdDocAmtNode'].append(strd_node['CdtNoteAmt_Node'])
            strd_node['StrdNode'].append(strd_node['RfrdDocAmtNode'])
            lst.append(strd_node)
            del strd_node
        return lst
