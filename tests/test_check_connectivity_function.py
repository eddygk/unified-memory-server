"""
Direct unit tests for check_connectivity_in_test_mode function
"""
import os
import sys
import unittest
from unittest.mock import patch, Mock
import socket

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_selector import check_connectivity_in_test_mode, ConnectivityError


class TestCheckConnectivityInTestMode(unittest.TestCase):
    """Test suite for check_connectivity_in_test_mode function"""

    def test_non_test_mode_returns_none(self):
        """Test that function returns None when test_mode is False"""
        result = check_connectivity_in_test_mode(
            url="http://neo4j:8001",
            operation_name="test_operation",
            test_mode=False,
            service_name="Test Service"
        )
        self.assertIsNone(result)

    def test_external_hostname_returns_none(self):
        """Test that external hostnames don't trigger connectivity check"""
        external_urls = [
            "http://external-server.com:8001",
            "http://api.example.com/data",
            "https://production-server.org:443",
            "http://192.168.1.100:8080"
        ]
        
        for url in external_urls:
            with self.subTest(url=url):
                result = check_connectivity_in_test_mode(
                    url=url,
                    operation_name="test_operation",
                    test_mode=True,
                    service_name="Test Service"
                )
                self.assertIsNone(result)

    @patch('socket.gethostbyname')
    def test_internal_hostname_dns_success_returns_none(self, mock_gethostbyname):
        """Test that internal hostnames with successful DNS resolution return None"""
        mock_gethostbyname.return_value = "127.0.0.1"
        
        internal_urls = [
            "http://neo4j:8001",
            "http://redis:6379",
            "http://basic-memory:8080",
            "http://localhost:3000"
        ]
        
        for url in internal_urls:
            with self.subTest(url=url):
                result = check_connectivity_in_test_mode(
                    url=url,
                    operation_name="test_operation",
                    test_mode=True,
                    service_name="Test Service"
                )
                self.assertIsNone(result)

    @patch('socket.gethostbyname')
    def test_internal_hostname_dns_failure_raises_connectivity_error(self, mock_gethostbyname):
        """Test that internal hostnames with DNS failure raise ConnectivityError"""
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")
        
        with self.assertRaises(ConnectivityError) as context:
            check_connectivity_in_test_mode(
                url="http://neo4j:8001",
                operation_name="test_operation",
                test_mode=True,
                service_name="Test Service"
            )
        
        error_msg = str(context.exception)
        self.assertIn("Test Service at neo4j is not reachable", error_msg)
        mock_gethostbyname.assert_called_with('neo4j')

    @patch('socket.gethostbyname')
    def test_socket_error_raises_connectivity_error(self, mock_gethostbyname):
        """Test that socket.error also raises ConnectivityError"""
        mock_gethostbyname.side_effect = socket.error("Socket error")
        
        with self.assertRaises(ConnectivityError) as context:
            check_connectivity_in_test_mode(
                url="http://redis:6379",
                operation_name="test_operation",
                test_mode=True,
                service_name="Redis Service"
            )
        
        error_msg = str(context.exception)
        self.assertIn("Redis Service at redis is not reachable", error_msg)
        mock_gethostbyname.assert_called_with('redis')

    @patch('socket.gethostbyname')
    def test_default_service_name_behavior(self, mock_gethostbyname):
        """Test that default service_name uses 'Server' when not provided"""
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")
        
        with self.assertRaises(ConnectivityError) as context:
            check_connectivity_in_test_mode(
                url="http://basic-memory:8080",
                operation_name="test_operation",
                test_mode=True
                # service_name not provided
            )
        
        error_msg = str(context.exception)
        self.assertIn("Server at basic-memory is not reachable", error_msg)
        mock_gethostbyname.assert_called_with('basic-memory')

    def test_all_internal_hostnames_covered(self):
        """Test that all internal hostnames are properly handled"""
        from memory_selector import INTERNAL_HOSTNAMES
        
        # Make sure we test all internal hostnames
        expected_hostnames = ['basic-memory', 'neo4j', 'redis', 'localhost']
        self.assertEqual(sorted(INTERNAL_HOSTNAMES), sorted(expected_hostnames))
        
        with patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "127.0.0.1"
            
            for hostname in INTERNAL_HOSTNAMES:
                with self.subTest(hostname=hostname):
                    url = f"http://{hostname}:8080"
                    result = check_connectivity_in_test_mode(
                        url=url,
                        operation_name="test_operation",
                        test_mode=True,
                        service_name="Test Service"
                    )
                    self.assertIsNone(result)

    @patch('memory_selector.logger')
    @patch('socket.gethostbyname')
    def test_warning_logged_on_connectivity_failure(self, mock_gethostbyname, mock_logger):
        """Test that warning is logged when connectivity check fails"""
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")
        
        with self.assertRaises(ConnectivityError):
            check_connectivity_in_test_mode(
                url="http://neo4j:8001",
                operation_name="store_data",
                test_mode=True,
                service_name="Neo4j Service"
            )
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once_with(
            "Test mode: Skipping store_data to unreachable hostname 'neo4j'"
        )

    def test_url_parsing_edge_cases(self):
        """Test URL parsing edge cases"""
        edge_case_urls = [
            "http://neo4j:8001/path/to/resource",
            "https://redis:6380/database/0",
            "http://localhost/api/v1/endpoint",
            "http://basic-memory:8080/entities?query=test"
        ]
        
        with patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "127.0.0.1"
            
            for url in edge_case_urls:
                with self.subTest(url=url):
                    result = check_connectivity_in_test_mode(
                        url=url,
                        operation_name="test_operation",
                        test_mode=True,
                        service_name="Test Service"
                    )
                    self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()