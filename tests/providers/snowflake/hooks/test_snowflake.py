#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Dict
from unittest import mock

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from airflow.models import Connection
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

_PASSWORD = 'snowflake42'

BASE_CONNECTION_KWARGS: Dict = {
    'login': 'user',
    'password': 'pw',
    'schema': 'public',
    'extra': {
        'database': 'db',
        'account': 'airflow',
        'warehouse': 'af_wh',
        'region': 'af_region',
        'role': 'af_role',
    },
}


@pytest.fixture()
def non_encrypted_temporary_private_key(tmp_path: Path):
    key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)
    private_key = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    test_key_file = tmp_path / "test_key.pem"
    test_key_file.write_bytes(private_key)
    return test_key_file


@pytest.fixture()
def encrypted_temporary_private_key(tmp_path: Path):
    key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)
    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(_PASSWORD.encode()),
    )
    test_key_file: Path = tmp_path / "test_key.p8"
    test_key_file.write_bytes(private_key)
    return test_key_file


class TestPytestSnowflakeHook:
    @pytest.mark.parametrize(
        "connection_kwargs,expected_uri,expected_conn_params",
        [
            (
                BASE_CONNECTION_KWARGS,
                (
                    'snowflake://user:pw@airflow.af_region/db/public?'
                    'application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
                ),
                {
                    'account': 'airflow',
                    'application': 'AIRFLOW',
                    'authenticator': 'snowflake',
                    'database': 'db',
                    'password': 'pw',
                    'region': 'af_region',
                    'role': 'af_role',
                    'schema': 'public',
                    'session_parameters': None,
                    'user': 'user',
                    'warehouse': 'af_wh',
                },
            ),
            (
                {
                    **BASE_CONNECTION_KWARGS,
                    'extra': {
                        'extra__snowflake__database': 'db',
                        'extra__snowflake__account': 'airflow',
                        'extra__snowflake__warehouse': 'af_wh',
                        'extra__snowflake__region': 'af_region',
                        'extra__snowflake__role': 'af_role',
                    },
                },
                (
                    'snowflake://user:pw@airflow.af_region/db/public?'
                    'application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
                ),
                {
                    'account': 'airflow',
                    'application': 'AIRFLOW',
                    'authenticator': 'snowflake',
                    'database': 'db',
                    'password': 'pw',
                    'region': 'af_region',
                    'role': 'af_role',
                    'schema': 'public',
                    'session_parameters': None,
                    'user': 'user',
                    'warehouse': 'af_wh',
                },
            ),
            (
                {
                    **BASE_CONNECTION_KWARGS,
                    'extra': {
                        'extra__snowflake__database': 'db',
                        'extra__snowflake__account': 'airflow',
                        'extra__snowflake__warehouse': 'af_wh',
                        'extra__snowflake__region': 'af_region',
                        'extra__snowflake__role': 'af_role',
                        'extra__snowflake__insecure_mode': 'True',
                    },
                },
                (
                    'snowflake://user:pw@airflow.af_region/db/public?'
                    'application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
                ),
                {
                    'account': 'airflow',
                    'application': 'AIRFLOW',
                    'authenticator': 'snowflake',
                    'database': 'db',
                    'password': 'pw',
                    'region': 'af_region',
                    'role': 'af_role',
                    'schema': 'public',
                    'session_parameters': None,
                    'user': 'user',
                    'warehouse': 'af_wh',
                    'insecure_mode': True,
                },
            ),
            (
                {
                    **BASE_CONNECTION_KWARGS,
                    'extra': {
                        'extra__snowflake__database': 'db',
                        'extra__snowflake__account': 'airflow',
                        'extra__snowflake__warehouse': 'af_wh',
                        'extra__snowflake__region': 'af_region',
                        'extra__snowflake__role': 'af_role',
                        'extra__snowflake__insecure_mode': 'False',
                    },
                },
                (
                    'snowflake://user:pw@airflow.af_region/db/public?'
                    'application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
                ),
                {
                    'account': 'airflow',
                    'application': 'AIRFLOW',
                    'authenticator': 'snowflake',
                    'database': 'db',
                    'password': 'pw',
                    'region': 'af_region',
                    'role': 'af_role',
                    'schema': 'public',
                    'session_parameters': None,
                    'user': 'user',
                    'warehouse': 'af_wh',
                },
            ),
            (
                {
                    **BASE_CONNECTION_KWARGS,
                    'extra': {
                        **BASE_CONNECTION_KWARGS['extra'],
                        'region': '',
                    },
                },
                (
                    'snowflake://user:pw@airflow/db/public?'
                    'application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
                ),
                {
                    'account': 'airflow',
                    'application': 'AIRFLOW',
                    'authenticator': 'snowflake',
                    'database': 'db',
                    'password': 'pw',
                    'region': '',
                    'role': 'af_role',
                    'schema': 'public',
                    'session_parameters': None,
                    'user': 'user',
                    'warehouse': 'af_wh',
                },
            ),
            (
                {
                    **BASE_CONNECTION_KWARGS,
                    'password': ';/?:@&=+$, ',
                },
                (
                    'snowflake://user:;%2F?%3A%40&=+$, @airflow.af_region/db/public?'
                    'application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
                ),
                {
                    'account': 'airflow',
                    'application': 'AIRFLOW',
                    'authenticator': 'snowflake',
                    'database': 'db',
                    'password': ';/?:@&=+$, ',
                    'region': 'af_region',
                    'role': 'af_role',
                    'schema': 'public',
                    'session_parameters': None,
                    'user': 'user',
                    'warehouse': 'af_wh',
                },
            ),
        ],
    )
    def test_hook_should_support_prepare_basic_conn_params_and_uri(
        self, connection_kwargs, expected_uri, expected_conn_params
    ):
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ):
            assert SnowflakeHook(snowflake_conn_id='test_conn').get_uri() == expected_uri
            assert SnowflakeHook(snowflake_conn_id='test_conn')._get_conn_params() == expected_conn_params

    def test_get_conn_params_should_support_private_auth_with_encrypted_key(
        self, encrypted_temporary_private_key
    ):
        connection_kwargs = {
            **BASE_CONNECTION_KWARGS,
            'password': _PASSWORD,
            'extra': {
                'database': 'db',
                'account': 'airflow',
                'warehouse': 'af_wh',
                'region': 'af_region',
                'role': 'af_role',
                'private_key_file': str(encrypted_temporary_private_key),
            },
        }
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ):
            assert 'private_key' in SnowflakeHook(snowflake_conn_id='test_conn')._get_conn_params()

    def test_get_conn_params_should_support_private_auth_with_unencrypted_key(
        self, non_encrypted_temporary_private_key
    ):
        connection_kwargs = {
            **BASE_CONNECTION_KWARGS,
            'password': None,
            'extra': {
                'database': 'db',
                'account': 'airflow',
                'warehouse': 'af_wh',
                'region': 'af_region',
                'role': 'af_role',
                'private_key_file': str(non_encrypted_temporary_private_key),
            },
        }
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ):
            assert 'private_key' in SnowflakeHook(snowflake_conn_id='test_conn')._get_conn_params()
        connection_kwargs['password'] = ''
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ):
            assert 'private_key' in SnowflakeHook(snowflake_conn_id='test_conn')._get_conn_params()
        connection_kwargs['password'] = _PASSWORD
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ), pytest.raises(TypeError, match="Password was given but private key is not encrypted."):
            SnowflakeHook(snowflake_conn_id='test_conn')._get_conn_params()

    def test_should_add_partner_info(self):
        with unittest.mock.patch.dict(
            'os.environ',
            AIRFLOW_CONN_TEST_CONN=Connection(**BASE_CONNECTION_KWARGS).get_uri(),
            AIRFLOW_SNOWFLAKE_PARTNER='PARTNER_NAME',
        ):
            assert (
                SnowflakeHook(snowflake_conn_id='test_conn')._get_conn_params()['application']
                == "PARTNER_NAME"
            )

    def test_get_conn_should_call_connect(self):
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**BASE_CONNECTION_KWARGS).get_uri()
        ), unittest.mock.patch('airflow.providers.snowflake.hooks.snowflake.connector') as mock_connector:
            hook = SnowflakeHook(snowflake_conn_id='test_conn')
            conn = hook.get_conn()
            mock_connector.connect.assert_called_once_with(**hook._get_conn_params())
            assert mock_connector.connect.return_value == conn

    def test_get_sqlalchemy_engine_should_support_pass_auth(self):
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**BASE_CONNECTION_KWARGS).get_uri()
        ), unittest.mock.patch(
            'airflow.providers.snowflake.hooks.snowflake.create_engine'
        ) as mock_create_engine:
            hook = SnowflakeHook(snowflake_conn_id='test_conn')
            conn = hook.get_sqlalchemy_engine()
            mock_create_engine.assert_called_once_with(
                'snowflake://user:pw@airflow.af_region/db/public'
                '?application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh'
            )
            assert mock_create_engine.return_value == conn

    def test_get_sqlalchemy_engine_should_support_insecure_mode(self):
        connection_kwargs = deepcopy(BASE_CONNECTION_KWARGS)
        connection_kwargs['extra']['extra__snowflake__insecure_mode'] = 'True'

        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ), unittest.mock.patch(
            'airflow.providers.snowflake.hooks.snowflake.create_engine'
        ) as mock_create_engine:
            hook = SnowflakeHook(snowflake_conn_id='test_conn')
            conn = hook.get_sqlalchemy_engine()
            mock_create_engine.assert_called_once_with(
                'snowflake://user:pw@airflow.af_region/db/public'
                '?application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh',
                connect_args={'insecure_mode': True},
            )
            assert mock_create_engine.return_value == conn

    def test_get_sqlalchemy_engine_should_support_session_parameters(self):
        connection_kwargs = deepcopy(BASE_CONNECTION_KWARGS)
        connection_kwargs['extra']['session_parameters'] = {"TEST_PARAM": "AA", "TEST_PARAM_B": 123}

        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ), unittest.mock.patch(
            'airflow.providers.snowflake.hooks.snowflake.create_engine'
        ) as mock_create_engine:
            hook = SnowflakeHook(snowflake_conn_id='test_conn')
            conn = hook.get_sqlalchemy_engine()
            mock_create_engine.assert_called_once_with(
                'snowflake://user:pw@airflow.af_region/db/public'
                '?application=AIRFLOW&authenticator=snowflake&role=af_role&warehouse=af_wh',
                connect_args={'session_parameters': {"TEST_PARAM": "AA", "TEST_PARAM_B": 123}},
            )
            assert mock_create_engine.return_value == conn

    def test_get_sqlalchemy_engine_should_support_private_key_auth(self, non_encrypted_temporary_private_key):
        connection_kwargs = deepcopy(BASE_CONNECTION_KWARGS)
        connection_kwargs['password'] = ''
        connection_kwargs['extra']['private_key_file'] = str(non_encrypted_temporary_private_key)

        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**connection_kwargs).get_uri()
        ), unittest.mock.patch(
            'airflow.providers.snowflake.hooks.snowflake.create_engine'
        ) as mock_create_engine:
            hook = SnowflakeHook(snowflake_conn_id='test_conn')
            conn = hook.get_sqlalchemy_engine()
            assert 'private_key' in mock_create_engine.call_args[1]['connect_args']
            assert mock_create_engine.return_value == conn

    def test_hook_parameters_should_take_precedence(self):
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_TEST_CONN=Connection(**BASE_CONNECTION_KWARGS).get_uri()
        ):
            hook = SnowflakeHook(
                snowflake_conn_id='test_conn',
                account="TEST_ACCOUNT",
                warehouse="TEST_WAREHOUSE",
                database="TEST_DATABASE",
                region="TEST_REGION",
                role="TEST_ROLE",
                schema="TEST_SCHEMA",
                authenticator='TEST_AUTH',
                session_parameters={"AA": "AAA"},
            )
            assert {
                'account': 'TEST_ACCOUNT',
                'application': 'AIRFLOW',
                'authenticator': 'TEST_AUTH',
                'database': 'TEST_DATABASE',
                'password': 'pw',
                'region': 'TEST_REGION',
                'role': 'TEST_ROLE',
                'schema': 'TEST_SCHEMA',
                'session_parameters': {'AA': 'AAA'},
                'user': 'user',
                'warehouse': 'TEST_WAREHOUSE',
            } == hook._get_conn_params()
            assert (
                "snowflake://user:pw@TEST_ACCOUNT.TEST_REGION/TEST_DATABASE/TEST_SCHEMA"
                "?application=AIRFLOW&authenticator=TEST_AUTH&role=TEST_ROLE&warehouse=TEST_WAREHOUSE"
            ) == hook.get_uri()

    @pytest.mark.parametrize(
        "sql,expected_sql,expected_query_ids",
        [
            ("select * from table", ["select * from table"], ["uuid"]),
            (
                "select * from table;select * from table2",
                ["select * from table;", "select * from table2"],
                ["uuid1", "uuid2"],
            ),
            (["select * from table;"], ["select * from table;"], ["uuid1"]),
            (
                ["select * from table;", "select * from table2;"],
                ["select * from table;", "select * from table2;"],
                ["uuid1", "uuid2"],
            ),
        ],
    )
    @mock.patch("airflow.providers.snowflake.hooks.snowflake.SnowflakeHook.get_conn")
    def test_run_storing_query_ids_extra(self, mock_conn, sql, expected_sql, expected_query_ids):
        hook = SnowflakeHook()
        conn = mock_conn.return_value
        cur = mock.MagicMock(rowcount=0)
        conn.cursor.return_value = cur
        type(cur).sfqid = mock.PropertyMock(side_effect=expected_query_ids)
        mock_params = {"mock_param": "mock_param"}
        hook.run(sql, parameters=mock_params)

        cur.execute.assert_has_calls([mock.call(query, mock_params) for query in expected_sql])
        assert hook.query_ids == expected_query_ids
        cur.close.assert_called()

    @mock.patch('airflow.providers.snowflake.hooks.snowflake.SnowflakeHook.run')
    def test_connection_success(self, mock_run):
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_SNOWFLAKE_DEFAULT=Connection(**BASE_CONNECTION_KWARGS).get_uri()
        ):
            hook = SnowflakeHook()
            mock_run.return_value = [{'1': 1}]
            status, msg = hook.test_connection()
            assert status is True
            assert msg == 'Connection successfully tested'
            mock_run.assert_called_once_with(sql='select 1')

    @mock.patch(
        'airflow.providers.snowflake.hooks.snowflake.SnowflakeHook.run',
        side_effect=Exception('Connection Errors'),
    )
    def test_connection_failure(self, mock_run):
        with unittest.mock.patch.dict(
            'os.environ', AIRFLOW_CONN_SNOWFLAKE_DEFAULT=Connection(**BASE_CONNECTION_KWARGS).get_uri()
        ):
            hook = SnowflakeHook()
            status, msg = hook.test_connection()
            assert status is False
            assert msg == 'Connection Errors'
            mock_run.assert_called_once_with(sql='select 1')
