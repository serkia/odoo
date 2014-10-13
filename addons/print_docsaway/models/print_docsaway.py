import json
import urllib2

from ssl import SSLError
from openerp import api, fields, models
from openerp.exceptions import RedirectWarning,  Warning
from openerp.addons.print_docsaway.data.docsaway_error import _DOCSAWAY_ERROR_ACCOUNT, _DOCSAWAY_ERROR_STATION, _DOCSAWAY_ERROR_PRICE, _DOCSAWAY_ERROR_MAIL
from openerp.tools.translate import _


# URLs for requests
_DOCSAWAY_GETACCOUNT_URL = 'https://www.docsaway.com/app/api/rest/account.json'
_DOCSAWAY_GETSTATION_URL = 'https://www.docsaway.com/app/api/rest/station_finder.json'
_DOCSAWAY_GETPRICE_URL = 'https://www.docsaway.com/app/api/rest/pricing.json'
_DOCSAWAY_SENDMAIL_URL = 'https://www.docsaway.com/app/api/rest/mail.json'



class print_provider(models.Model):

    _inherit = 'print.provider'

    @api.model
    def _get_providers(self):
        providers = super(print_provider, self)._get_providers()
        providers.append(['docsaway', 'DocsAway'])
        return providers

    # --------------------------------------------------
    # MODEL FIELDS
    # --------------------------------------------------
    docsaway_email = fields.Char('Docsaway Account Email', help="Docsaway account email. Required to contact DocsAway server, it can be found into docsaway account preference (on docsaway.com)")
    docsaway_key = fields.Char('Docsaway Installation Key', help="Docsaway account installation key. Required to contact DocsAway server, it can be found into docsaway account preference (on docsaway.com)")
    docsaway_name = fields.Char('Docsaway Name', help="Name of the docsaway account.")
    docsaway_reference = fields.Char('Docsaway Reference', help="Reference code of Docsaway account.")
    docsaway_volume = fields.Integer('Docsaway Volume', help="Number of pages printed by Docsaway.")

    # --------------------------------------------------
    # Methods to be redefine from print.provider, with
    # correct naming convention.
    # --------------------------------------------------
    @api.one
    def docsaway_update_account_data(self):
        account = self._docsaway_fetch_account()
        self.write({
            'docsaway_name' : account['name'],
            'docsaway_reference' : account['reference'],
            'docsaway_volume' : account['volume'],
            'balance' : account['balance'],
        })



    # --------------------------------------------------
    # DocsAway API methods
    # --------------------------------------------------
    @api.model
    def _docsaway_get_credentials(self):
        """ get the credentials of the current docsaway provider, or throw error if provider not configured """
        if not (self.docsaway_email and self.docsaway_key):
            action = self.env.ref('base_setup.action_general_configuration')
            msg = _("Please configure your DocsAway Print Provider Account. See in Settings > Print Provider.")
            raise RedirectWarning(msg, action.id, _('Configure Account Now'))
        return self.docsaway_email, self.docsaway_key

    @api.model
    def _docsaway_do_server_request(self, url, request, error_map=_DOCSAWAY_ERROR_MAIL):
        """ Connect to the server, do a POST request to url with parameter
            'params' and return the JSON response.
            The format of request is explained in the following method.
            Raise Exceptions if the connection to DocsAway server failed, or if the request return an error.
        """
        # add Indentification Data
        email, installation_key = self._docsaway_get_credentials()
        request.update({
            'APIConnection': {
                'email': email,
                'key': installation_key,
            },
            'APIReport': bool(self.environment == 'test'),
        })

        # Send JSON object to the Docsaway server
        req = urllib2.Request(url, json.dumps(request), {'Content-Type': 'application/json'})
        try:
            f = urllib2.urlopen(req, timeout=15)
        except SSLError:
            raise Exception(_('Host unreachable.') + ' ' + _('Please try again later.'))

        if f.getcode() != 200:
            raise Exception(_('Failed request.') + ' ' + _('Please try again later.'))
        response = json.loads(f.read())
        f.close()

        # DocsAway Request Error
        if response['APIErrorNumber']:
            error_code = response['APIErrorNumber']
            raise Warning("DOCSAWAY ERROR : " + error_code + " " + error_map.get(error_code, _('Unknown Error')))
        return response

    @api.model
    def _docsaway_fetch_account(self, reference=None):
        """ Allow to access remotely to the Docsaway account and fetch information about
            If reference is set, then the Response JSON will add information
            about the document with the given reference
            Return a Response JSON object (explained below) if connection to the
            server succeeds, otherwise None

            Explaination of the Request JSON Object :
                - APIConnection: info about connection. It has 2 subfields:
                    - Email: login email
                    - Key: Docsaway installation key
                - APIReport: show more visual view for debugging
                - balance: True if want to have the balance in the JSON object
                - reference:  True if want to have the account reference in JSON
                - company: True if want to have the account company name in JSON
                - name: True if want to have the account name in JSON
                - audit: refenrence code of the document you want to retrieve

            Explaination of the Response JSON Object :
                - APIErrorNumber: if not 0, indicate error
                - APIReport: this JSON object in textual form (except APIReport)
                - audit: detailed informations if required
                - balance: decimal value which represent the current balance
                - company: account company name
                - name: account holders full name
                - reference: account holders account reference
                - volume: return the total number of documents sent
        """
        request = {
            'balance': True,
            'volume': True,
            'reference': True,
            'company': True,
            'name': True,
        }
        if reference is not None:
            request.update({
                'audit': reference,
            })
        return self._docsaway_do_server_request(_DOCSAWAY_GETACCOUNT_URL, request, _DOCSAWAY_ERROR_ACCOUNT)

    @api.model
    def _docsaway_fetch_station(self, destination, ink='BW', paper='80', stationID='AUTO'):
        """ Return the "best" station to print a document given a destination
            dest under a JSON format

            Explaination of the Request JSON Object :
                - APIConnection: info about connection. It has 2 subfields:
                    - Email: login email
                    - Key: Docsaway installation key
                - APIReport: show more visual view for debugging
                - action: function desired (here, getStationAuto)
                - ink: BW (Black & White) or CL (color)
                - paper: value in gram per square meter (default is 80 gsm)
                - destination: ISO 3166-1 (2 or 3 letter country codes)
                - StationID: AUTO (to find automatically)

             Explaination of the Response JSON Object :
                - APIErrorNumber: if not 0, indicate error
                - APIReport: this JSON object in textual form (except APIReport)
                - stationAuto: contains 3 subfields:
                    - stationID: the ID of the station
                    - courierID: the ID of the courier
                    - zone: integer (used for pricing)
        """
        request = {
            'action': "getStationAuto",
            'ink': ink,
            'paper': paper,
            'destination': destination,
            'StationID': stationID,
        }
        return self._docsaway_do_server_request(_DOCSAWAY_GETSTATION_URL, request, _DOCSAWAY_ERROR_STATION)

    @api.model
    def _docsaway_fetch_price(self, station, courier, zone, currency_name, nb_pages, ink='BW', paper=80):
        """ Return the price of sending a document with station, courier in zone
            that makes pageCount pages, if it's in color, and depending of the
            paper used

            Explaination of the Request JSON Object :
                - APIConnection: info about connection. It has 2 subfields:
                    - Email: login email
                    - Key: Docsaway installation key
                - APIReport: show more visual view for debugging
                - stationID: station id code of the station used
                - courierID: courier id code of the station used
                - paper: value in gram per square meter (default is 80 gsm)
                - ink: BW (Black & White) or CL (color)
                - zone: zone number given by _get_station_auto
                    (1=local, 2=national, 3=international)
                - pageCount: number of pages of the PDF to be sent (1-40)
                - currency: in which currency the price will be displayed.
                            By default, in AUD

            Explaination of the Response JSON Object :
                - APIErrorNumber: if not 0, indicate error
                - APIReport: this JSON object in textual form (except APIReport)
                - price: the price with two decimals
        """
        request = {
            'stationID': station,
            'courierID': courier,
            'zone': zone,
            # A coversheet is added, which add a page (see Docsaway.com)
            'pageCount': nb_pages + 1,
            'paper': paper,
            'ink': ink,
            'currency': currency_name,
        }
        return self._docsaway_do_server_request(_DOCSAWAY_GETPRICE_URL, request, _DOCSAWAY_ERROR_PRICE)

    @api.model
    def _docsaway_send_document(self, address, printing_infos, PDFfile):
        """ Ask Docsaway to send the report at the address of the partner

        Explaination of the Request JSON Object :
            - APIConnection: info about connection. It has 2 subfields:
            - Email: login email
            - Key: Docsaway installation key
            - APIReport: show more visual view for debugging
            - APIMode: LIVE in production, TEST for debug
            - Recipient: information about recipient, 8 subfields:
                - name
                - company (not mandatory)
                - address1
                - address2 (not mandatory)
                - city
                - state (not mandatory)
                - zip
                - country (in ISO 3166-1, alpha 2, 3 or numeric)
            - PrintingStation: specify the printing station used, 4 subfields:
                - id (of station, or AUTO for automatic choice)
                - courierID (or False for automatic choice)
                - ink (CL for colour, BW for Black & White)
                - paper (paper weight (in gsm), 80 by default)
            - PDFFile: the PDF file to print (in base64 encoding, max 2MB)
            - Reseller: requires the value of the Docsaway account reference,
            used for service where customers are using their login
            details via the module. Not mandatory

        Explaination of the Response JSON Object:
            - APIErrorNumber: if not 0, indicate error
            - APIReport: this JSON object in textual form (except APIReport)
            - document: properties about the document sent, 4 subfields:
                - Envelope: id of envelope used (DL, C4, ...)
                - Ink: id of ink used (CL or BW)
                - Paper: paper weight used for the document in GSM
                - Size: total number of pages in the document send
            - station: properties about the station used, 7 subfields:
                - ID: id of station used
                - ISO2: ISO country code of the station in ISO 3166-1 Alpha 2
                - Country: country name of the station
                - City: city name of the station
                - Courier ID: courier id used by the station
                - Courier Name: name of the courier used
                - Zone: (1=local, 2=national, 3=international)
            - transaction: propoerties of the transaction, 5 subfields:
                - Approved: y (successful transaction) or n (failed one)
                - Price: price (in AUD)
                - Reference: unique string to refer this transaction
                - Date: date and time of transaction according to Docsaway
                - Balance: return the remaining account balance after
                    transaction (in AUD)
        """
        APIMode = 'LIVE' if self.environment == 'prod' else 'TEST'
        # build request
        request = {
            'APIMode': APIMode,
            'Recipient': {
                'name': address.get('name'),
                'address1': address.get('street'),
                'city': address.get('city'),
                'zip': address.get('zip'),
                'country': address.get('country_code'),
            },
            'PrintingStation': {
                'id': printing_infos.get('station_id'),
                'courierID': printing_infos.get('courier_id'),
                'ink': printing_infos.get('ink', 'BW'),
                'paper': printing_infos.get('paper', 80),
            },
            'PDFFile': PDFfile,
        }
        # complete facultative parameters
        if address.get('street2', False):
            # avoid to return an error on facultative field
            if len(address.get('street2')) <= 50:
                request['Recipient'].update({
                    'address2': address.get('street2'),
                })
        if address.get('state', False):
            request['Recipient'].update({
                'state': address.get('state'),
            })
        return self._docsaway_do_server_request(_DOCSAWAY_SENDMAIL_URL, request, _DOCSAWAY_ERROR_MAIL)


class print_order(models.Model):

    _inherit = 'print.order'

    # station fields
    docsaway_station = fields.Char('Docsaway Station', help="Docsaway Station ID.")
    docsaway_courier = fields.Char('Docsaway Courier', help="Docsaway Printer ID.")
    docsaway_zone = fields.Integer('Docsaway Zone', help="Docsaway Station ID.")
    # transaction fields
    docsaway_reference = fields.Char('Docsaway Reference', help="Docsaway Reference Order.")
    docsaway_approved = fields.Char('Docsaway Approved', help="Docsaway Transation Status.")


    @api.multi
    def docsaway_action_prepare(self):
        """ Pre-process the sending by computing the best station for each given orders.
        """
        # minimize the number of call to DocsAway API by grouping by partner
        # (for localization) and by ink to find the best station.
        stations = {}
        for order in self:
            try:
                if not ((order.partner_id.id, order.ink) in stations):
                    stations[(order.partner_id.id, order.ink)] = order.provider_id._docsaway_fetch_station(order.partner_id.country_id.code, order.ink, order.paper)
                response = stations[(order.partner_id.id, order.ink)]
                order.write({
                    'docsaway_station' : response['stationAuto']['stationID'],
                    'docsaway_courier' : response['stationAuto']['courierID'],
                    'docsaway_zone' : response['stationAuto']['zone'],
                    'state' : 'ready_to_send'
                })
            except Exception, e:
                order.write({
                    'state' : 'error',
                    'error_message' : e,
                })


    @api.multi
    def docsaway_action_deliver(self):
        """ Send the orders for delivery to DocsAway.
            :return a dict, containing for each order, informations about its sending. (error_message is not mandatory)
                    {
                        'order_id' : [order.user_id, bool('correctly send'), error_message],
                    }
        """
        result = {}
        new_balance = False
        for order in self:
            if order.state == 'ready_to_send':
                # create params to send order to docsaway.
                address = {
                    'name' : order.partner_name,
                    'street' : order.partner_street,
                    'street2' : order.partner_street2,
                    'state' : order.partner_state_id.name,
                    'city' : order.partner_city,
                    'zip' : order.partner_zip,
                    'country_code' : order.partner_country_id.code
                }
                printing_infos = {
                    'station_id' : order.docsaway_station,
                    'courier_id' : order.docsaway_courier,
                    'zone' : order.docsaway_zone,
                    'ink' : order.ink,
                    'paper' : order.paper
                }
                try:
                    response = order.provider_id._docsaway_send_document(address, printing_infos, order.attachment_id.datas)
                    result[order.id] = [order.user_id.id, True]
                    order.write({
                        'docsaway_reference' : response['transaction']['reference'],
                        'docsaway_approved' : response['transaction']['approved'],
                        'price' : response['transaction']['price'],
                        'state' : 'sent',
                        'send_date' : fields.Datetime.now(),
                        'error_message' : False
                    })
                    new_balance = response['transaction']['balance']
                except Exception, e:
                    result[order.id] = [order.user_id.id, False, e]
                    order.write({
                        'state' : 'error',
                        'error_message' : e,
                        'price' : 0.0,
                    })
            else:
                result[order.id] = [order.user_id.id, False, "DOCSAWAY ERROR : Preparation failed."]
        # update balance of the Provider
        if new_balance and self[0]:
            self[0].provider_id.write({
                'balance' : new_balance
            })

        return result

