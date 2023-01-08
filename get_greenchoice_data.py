#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 09:54:37 2022

Zie:
    https://github.com/1ntroduc3/homeassistant-greenchoice-energy-only/blob/master/greenchoice_api.py

@author: edgordijn
"""

import requests
from requests import Session
from typing import List, Dict, Optional
from io import StringIO
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
# import logging

import pandas as pd


API_URL = 'https://mijn.greenchoice.nl'
# LOGGER = logging.getLogger(__package__)

# overeenkomstId = 2952119
# klantnummer = 84741

class GreenchoiceApi:

    def __init__(self, username: str, password: str) -> None:
        self.username: str = username
        self.password: str = password
        self.session: Optional[Session] = None

    def login(self):
        self.session = self.__get_session()

    @staticmethod
    def __get_verification_token(html_txt: str):
        soup = BeautifulSoup(html_txt, "html.parser")
        token_elem = soup.find("input", {"name": "__RequestVerificationToken"})

        return token_elem.attrs.get("value")

    @staticmethod
    def __get_oidc_params(html_txt: str):
        soup = BeautifulSoup(html_txt, "html.parser")

        code_elem = soup.find("input", {"name": "code"})
        scope_elem = soup.find("input", {"name": "scope"})
        state_elem = soup.find("input", {"name": "state"})
        session_state_elem = soup.find("input", {"name": "session_state"})

        # if not (code_elem and scope_elem and state_elem and session_state_elem):
        #     error = "Login failed, check your credentials?"
        #     LOGGER.error(error)
        #     raise (GreenchoiceError(error))

        return {
            "code": code_elem.attrs.get("value"),
            "scope": scope_elem.attrs.get("value").replace(" ", "+"),
            "state": state_elem.attrs.get("value"),
            "session_state": session_state_elem.attrs.get("value")
        }

    def __get_session(self) -> Session:
        # if not self.username or not self.password:
        #     error = "Username or password not set"
        #     LOGGER.error(error)
        #     raise (GreenchoiceError(error))
        sess: Session = requests.Session()

        # first, get the login cookies and form data
        login_page = sess.get(API_URL)
        return_url = parse_qs(urlparse(login_page.url).query).get("ReturnUrl", "")
        token = self.__get_verification_token(login_page.text)

        # perform actual sign in
        login_data = {
            "ReturnUrl": return_url,
            "Username": self.username,
            "Password": self.password,
            "__RequestVerificationToken": token,
            "RememberLogin": True
        }
        auth_page = sess.post(login_page.url, data=login_data)

        # exchange oidc params for a login cookie (automatically saved in session)      
        sess.post(url=API_URL+'/signin-oidc',
                  data=self.__get_oidc_params(auth_page.text)
                  )      
        return sess

    def __microbus_request(self, name, message=None):
        if not message:
            message = {}

        payload = {
            'name': name,
            'message': message
        }
        response = self.session.post(url=API_URL+'/microbus/request',
                                     json=payload)
        if not response:
            raise ConnectionError

        return response.json()


    def get_meterstanden(self, year, product=1):
        '''
        Haal de meterstanden op
        year int: het kalenderjaar
        product int: 1 voor elektriciteit of 2 voor gas
        '''
        with self.__get_session() as self.session:
            # Get meterstanden data
            json_data = self.__microbus_request(name='OpnamesCsvCommand',
                                                message={'Jaar': year, 'Product': product}
                                                )       
            
            # Create an in-memory stream for text I/O to capture the output data as a data frame
            with StringIO(json_data['csv']) as csv:   
                df = pd.read_csv(csv,
                                 delimiter=';',
                                 parse_dates=['OpnameDatum']
                                 )
    
            # Remove duplicates
            df = df.drop_duplicates(subset='OpnameDatum', keep='last')
    
            # Set index
            df = df.set_index('OpnameDatum')
            
            return df