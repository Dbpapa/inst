from telegram.utils.request import Request
import socket

class StableRequest(Request):
    """Enhanced request handler with network stability features"""
    
    def __init__(self, *args, **kwargs):
        kwargs.update({
            'connect_timeout': 30,
            'read_timeout': 30,
            'con_pool_size': 10
        })
        super().__init__(*args, **kwargs)

    def _create_connection(self, *args, **kwargs):
        conn = super()._create_connection(*args, **kwargs)
        sock = conn.sock
        
        # TCP Keep-Alive Configuration
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        
        return conn
